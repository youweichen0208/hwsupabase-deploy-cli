import hashlib
import json
import ssl
import time
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener, HTTPSHandler

from .core import DeliveryError, State, atomic_json, check_url, digest, identifier, no_literal_secrets, read_document, render


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def verify(config, release, cases_path, opener=None):
    identifier(release, "release ID")
    suite = read_document(cases_path)
    no_literal_secrets(suite)
    cases = suite.get("cases", [])
    if not cases:
        raise DeliveryError("Verification requires nonempty HTTP cases")
    names = set()
    for case in cases:
        name = identifier(case.get("id"), "HTTP case ID")
        if name in names:
            raise DeliveryError("Duplicate HTTP case ID")
        names.add(name)
        if not isinstance(case.get("expect"), dict) or "status" not in case["expect"]:
            raise DeliveryError("Each HTTP case must specify expected status")
        if set(case["expect"]) - {"status", "headers", "header_counts", "body", "contains", "sha256", "release"}:
            raise DeliveryError("Unknown HTTP assertion")
        marker = case["expect"].get("release")
        if marker is not None and (not isinstance(marker, dict) or set(marker) not in ({"header"}, {"json_path"})):
            raise DeliveryError("Release assertion requires one header or json_path")
    opener = opener or build_opener(NoRedirect(), HTTPSHandler(context=ssl.create_default_context()))
    state = State(config)
    with state.locked():
        context = {"config": config.data, "state": state.data}
        outcomes = []
        for template in cases:
            case = render(template, context)
            check_url(case["url"], https=True)
            body = case.get("body")
            if body is not None and not isinstance(body, str):
                raise DeliveryError("HTTP body must be a string")
            request = Request(case["url"], data=body.encode() if body is not None else None,
                              headers=case.get("headers", {}), method=case.get("method", "GET"))
            passed, reason = False, "network-or-tls"
            response = None
            try:
                try:
                    response = opener.open(request, timeout=20)
                except HTTPError as error:
                    response = error
                data = response.read(6 * 1024 * 1024 + 1)
                if len(data) > 6 * 1024 * 1024:
                    raise DeliveryError("HTTP verification response exceeded 6 MiB")
                expected = case["expect"]
                checks = [response.code == expected["status"]]
                for key, value in expected.get("headers", {}).items():
                    checks.append(response.headers.get(key) == value)
                for key, count in expected.get("header_counts", {}).items():
                    checks.append(len(response.headers.get_all(key, [])) == count)
                if "body" in expected:
                    checks.append(data == expected["body"].encode())
                if "contains" in expected:
                    checks.append(expected["contains"].encode() in data)
                if "sha256" in expected:
                    checks.append(hashlib.sha256(data).hexdigest() == expected["sha256"])
                marker = expected.get("release")
                if marker:
                    if "header" in marker:
                        checks.append(response.headers.get(marker["header"]) == release)
                    else:
                        from .core import lookup
                        try:
                            checks.append(lookup(json.loads(data), marker["json_path"]) == release)
                        except (ValueError, DeliveryError):
                            checks.append(False)
                passed = all(checks)
                reason = "passed" if passed else "assertion"
            except (URLError, TimeoutError, OSError):
                pass
            finally:
                if response is not None:
                    response.close()
            outcomes.append({"id": template["id"], "category": template.get("category", "api"), "passed": passed,
                             "release_checked": bool(template["expect"].get("release")), "reason": reason})
        required = {"supabase"}
        if config.data.get("web"):
            required.add("web")
        if config.data.get("python"):
            required.add("api")
        covered = {r["category"] for r in outcomes if r["passed"]}
        versions = {r["category"] for r in outcomes if r["passed"] and r["release_checked"]}
        missing_versions = (required - {"supabase"}) - versions
        passed = all(r["passed"] for r in outcomes) and required <= covered and not missing_versions
        report = {"release": release, "config_digest": digest(config.data), "runs_digest": digest(state.data["runs"]),
                  "suite_digest": digest(suite), "checked_at": time.time(), "passed": passed,
                  "missing_categories": sorted(required - covered), "missing_release_categories": sorted(missing_versions), "cases": outcomes}
        atomic_json(config.state_dir / "reports" / (release + ".json"), report)
        return report


def register_release(config, metadata_path):
    metadata = read_document(metadata_path)
    allowed = {"id", "stage_workflow", "function_urn", "function_version", "alias", "apig_snapshot", "web_manifest", "python_manifest"}
    if set(metadata) - allowed:
        raise DeliveryError("Release metadata contains unsupported fields")
    release = identifier(metadata.get("id"), "release ID")
    if config.data.get("python"):
        if not metadata.get("function_urn") or metadata.get("function_version") in (None, "", "latest"):
            raise DeliveryError("Release must identify an immutable deployed function version")
    state = State(config)
    with state.locked():
        run = state.data["runs"].get(metadata.get("stage_workflow"), {})
        if run.get("status") != "complete" or run.get("phase") != "stage" or run.get("release") != release:
            raise DeliveryError("Register only after a completed stage workflow")
        if config.data.get("python"):
            matching = [step for step in run.get("steps", {}).values()
                        if metadata["function_urn"] in step.get("outputs", {}).values()
                        and metadata["function_version"] in step.get("outputs", {}).values()]
            if not matching:
                raise DeliveryError("Function URN/version must be captured together in the stage workflow's cloud readback")
        manifests = {}
        for field in ("web_manifest", "python_manifest", "apig_snapshot"):
            if metadata.get(field):
                path = config.local(metadata[field])
                if not path.is_file() or not path.is_relative_to(config.state_dir):
                    raise DeliveryError("Release manifests/snapshots must exist in this environment's state directory")
                document = read_document(path)
                if field != "apig_snapshot" and document.get("release") != release:
                    raise DeliveryError("Artifact manifest belongs to another release")
                manifests[field] = digest(document)
        for profile, field in (("web", "web_manifest"), ("python", "python_manifest")):
            if config.data.get(profile) and field not in manifests:
                raise DeliveryError("Release is missing " + field)
        if config.data.get("python") and "apig_snapshot" not in manifests:
            raise DeliveryError("Save a redacted APIG configuration snapshot before registration")
        record = {"metadata": metadata, "manifest_digests": manifests}
        existing = state.data["releases"].get(release)
        if existing and existing != record:
            raise DeliveryError("A registered release is immutable")
        state.data["releases"][release] = record
        state.save()
    return {"release": release, "status": "registered", "active": False}


def activate(config, release, workflow):
    state = State(config)
    identifier(release, "release ID")
    with state.locked():
        if release not in state.data["releases"]:
            raise DeliveryError("Release is not registered")
        run = state.data["runs"].get(workflow, {})
        if (run.get("status") != "complete" or run.get("phase") not in ("promote", "rollback")
                or run.get("release") != release):
            raise DeliveryError("Activation requires a completed promote/rollback workflow")
        record = state.data["releases"][release]
        for field, expected_digest in record["manifest_digests"].items():
            if digest(read_document(config.local(record["metadata"][field]))) != expected_digest:
                raise DeliveryError("A registered release manifest has changed")
        report = read_document(config.state_dir / "reports" / (release + ".json"))
        if (not report.get("passed") or report.get("release") != release
                or report.get("config_digest") != digest(config.data)
                or report.get("runs_digest") != digest(state.data["runs"])):
            raise DeliveryError("Verification is missing, failed or stale; verify after the final cloud mutation")
        if state.data["current"] != release:
            state.data["previous"] = state.data["current"]
            state.data["current"] = release
            state.save()
        return {"current": state.data["current"], "previous": state.data["previous"], "status": "http-verified"}
