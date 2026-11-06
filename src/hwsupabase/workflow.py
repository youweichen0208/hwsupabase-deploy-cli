import json
import os
import re
import time

from .core import DeliveryError, State, digest, environment_names, identifier, lookup, no_literal_secrets, read_document, render
from .cloud import Cloud, validate_call


def load_workflow(path):
    recipe = read_document(path)
    no_literal_secrets(recipe)
    if recipe.get("version") != 1 or recipe.get("phase") not in ("setup", "stage", "promote", "rollback"):
        raise DeliveryError("Workflow requires version 1 and phase setup/stage/promote/rollback")
    identifier(recipe.get("id"), "workflow ID")
    if recipe["phase"] != "setup":
        identifier(recipe.get("release"), "workflow release ID")
    steps = recipe.get("steps")
    if not isinstance(steps, list) or not steps:
        raise DeliveryError("Workflow requires nonempty steps")
    seen = set()
    for step in steps:
        name = identifier(step.get("id"), "step ID")
        if name in seen:
            raise DeliveryError("Duplicate workflow step ID")
        seen.add(name)
        if "apply" not in step or "probe" not in step:
            raise DeliveryError("Every step requires apply and a read-only probe")
        validate_call(step["apply"])
        if step["apply"].get("kind") == "obs-read":
            raise DeliveryError("A structured OBS probe cannot be used as a mutation")
        probe = step["probe"]
        validate_call(probe.get("call"), readonly=True)
        if not probe.get("expect"):
            raise DeliveryError("Every probe needs explicit expected fields")
        if not isinstance(probe["expect"], dict):
            raise DeliveryError("Probe expect must be a field/value mapping")
        if set(step.get("capture", {})) - set(probe.get("capture", {})):
            raise DeliveryError("Every mutation capture must also be recoverable from the probe")
        if step.get("ownership") not in ("created", "reused", "updated"):
            raise DeliveryError("Each step must declare resource ownership")
        for mapping in (step.get("capture", {}), probe.get("capture", {})):
            for key, path in mapping.items():
                identifier(key, "capture name")
                if not isinstance(path, str) or re.search(r"secret|password|token|api.?key|user_data|^text$", key + " " + path, re.I):
                    raise DeliveryError("Only nonsecret scalar resource metadata can be captured")
    return recipe


def select_result(result, select, context):
    if not select:
        return result
    rows = lookup(result, select["path"])
    if not isinstance(rows, list):
        raise DeliveryError("Probe selection must refer to an array")
    if isinstance(result, dict):
        total = result.get("count", result.get("total"))
        if (isinstance(total, int) and total > len(rows)) or result.get("next_marker") not in (None, 0, "", "0"):
            raise DeliveryError("Incomplete list probe; exhaust pagination or use an explicit resource ID")
    where = render(select.get("where", {}), context)
    if not where:
        raise DeliveryError("List probes require an exact identity filter")
    matched = []
    for row in rows:
        try:
            if all(lookup(row, key) == value for key, value in where.items()):
                matched.append(row)
        except DeliveryError:
            continue
    if len(matched) > 1:
        raise DeliveryError("Ambiguous resource match; use an explicit cloud resource ID")
    return matched[0] if matched else None


def capture(result, mapping, secret_values):
    values = {}
    for key, path in mapping.items():
        item = lookup(result, path)
        if not isinstance(item, (str, int, float, bool)) or item is None:
            raise DeliveryError("Capture only scalar IDs, names, versions and digests")
        if isinstance(item, str) and any(secret and secret in item for secret in secret_values):
            raise DeliveryError("Refusing to write a secret into deployment state")
        values[key] = item
    return values


def execute(config, recipe, cloud=None, wait_seconds=20):
    """Reconcile first, execute a mutation once, then checkpoint cloud observations.

    An interrupted mutation is never blindly retried. Resume can observe its success;
    otherwise the engineer must reconcile it before generating a new workflow.
    """
    cloud = cloud or Cloud(config)
    state = State(config)
    secret_values = [os.environ.get(n, "") for n in environment_names(recipe) | environment_names(config.data)]
    with state.locked():
        run_id = recipe["id"]
        identity = digest({"recipe": recipe, "config": config.data})
        run = state.data["runs"].setdefault(run_id, {"fingerprint": identity, "phase": recipe["phase"], "release": recipe.get("release"), "steps": {}, "status": "pending"})
        if run["fingerprint"] != identity:
            raise DeliveryError("Workflow/config changed under an existing ID; reconcile then use a new ID")
        context = {"config": config.data, "state": state.data, "steps": run["steps"]}
        for step in recipe["steps"]:
            record = run["steps"].setdefault(step["id"], {"status": "pending", "outputs": {}, "ownership": step["ownership"]})
            probe = step["probe"]

            def observe():
                result = cloud.call(probe["call"], context, readonly=True)
                selected = select_result(result, probe.get("select"), context)
                if selected is None:
                    return False
                expected = render(probe["expect"], context)
                try:
                    matches = all(lookup(selected, key) == val for key, val in expected.items())
                except DeliveryError:
                    matches = False
                if matches:
                    record["outputs"].update(capture(selected, probe.get("capture", {}), secret_values))
                return matches

            try:
                if observe():
                    record["status"] = "complete"
                    state.save()
                    continue
                if record["status"] == "complete":
                    raise DeliveryError("Cloud drift detected for completed step " + step["id"])
                if record["status"] in ("in_flight", "uncertain"):
                    raise DeliveryError("Uncertain mutation for " + step["id"] + "; reconcile cloud state before retrying")
                if step["ownership"] == "reused" and record["status"] == "pending":
                    raise DeliveryError("Reused resource does not match; refusing to mutate it")
                if record["status"] == "pending":
                    record["status"] = "in_flight"
                    run["status"] = "partial"
                    state.save()  # intent written BEFORE the mutating request
                    result = cloud.call(step["apply"], context)
                    record["outputs"].update(capture(result, step.get("capture", {}), secret_values))
                    record["status"] = "waiting"
                    state.save()  # save returned IDs before readiness checks
                deadline = time.monotonic() + min(max(wait_seconds, 0), 45)
                while True:
                    if observe():
                        record["status"] = "complete"
                        state.save()
                        break
                    if time.monotonic() >= deadline:
                        raise DeliveryError("Resource not ready: " + step["id"] + "; resume the same workflow to poll again")
                    time.sleep(min(2, max(0, deadline - time.monotonic())))
            except Exception:
                if record["status"] == "in_flight":
                    record["status"] = "uncertain"
                run["status"] = "partial"
                state.save()
                raise
        run["status"] = "complete"
        state.save()
        return {"workflow": run_id, "phase": run["phase"], "status": "complete"}
