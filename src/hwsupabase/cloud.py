"""Execute official tooling without shell expansion or reimplementing signing."""
import json
import os
from pathlib import Path
import subprocess
import tempfile

from .core import DeliveryError, render


READ_PREFIXES = ("Show", "List", "Get", "Check")
SERVICES = {"FunctionGraph", "APIG", "VPC", "IAM", "EIP", "RDS", "DNS", "CCM", "LTS", "NAT"}


def validate_call(call, readonly=False):
    if not isinstance(call, dict):
        raise DeliveryError("A cloud call must be a mapping")
    kind = call.get("kind", "api")
    if kind == "api":
        operation = call.get("operation", "")
        if call.get("service") not in SERVICES or not operation.isalnum():
            raise DeliveryError("Unsupported service or operation")
        if readonly and not operation.startswith(READ_PREFIXES):
            raise DeliveryError("Probes may only use read operations")
        if operation.startswith(("Delete", "Reset", "Stop", "Reboot", "Restart", "BatchDelete")):
            raise DeliveryError("Destructive lifecycle operations are outside the delivery runner")
        if "ApiKeyValue" in operation:
            raise DeliveryError("Obtain API key values through the customer's secure credential process")
        params = call.get("input", {})
        if not isinstance(params, dict) or set(params) - {"path", "query", "body", "header", "formData", "cookie"}:
            raise DeliveryError("KooCLI JSON input requires path/query/body/header/formData/cookie sections")
    elif kind == "obs-read":
        if call.get("target") not in ("bucket", "object", "website", "cors"):
            raise DeliveryError("Unknown structured OBS probe target")
    elif kind == "obs":
        command = call.get("command")
        if command not in ({"ls", "stat"} if readonly else {"ls", "stat", "mb", "cp", "sync", "bucketpolicy"}):
            raise DeliveryError("Unsupported OBS command")
        if not isinstance(call.get("args", []), list):
            raise DeliveryError("OBS args must be a list; shell strings are unsupported")
    else:
        raise DeliveryError("Unknown cloud call kind")


class Cloud:
    def __init__(self, config):
        self.config = config

    def _execute(self, args, timeout=60):
        try:
            result = subprocess.run(args, cwd=self.config.root, stdin=subprocess.DEVNULL,
                                    capture_output=True, text=True, timeout=timeout, check=False)
        except subprocess.TimeoutExpired:
            raise DeliveryError("Cloud command timed out; reconcile remotely before retrying") from None
        except OSError:
            raise DeliveryError("Cannot execute hcloud; install KooCLI and check PATH") from None
        if result.returncode:
            # CLI diagnostics can echo credentials/request bodies. Never persist or print them.
            raise DeliveryError("Cloud command failed (exit %d); inspect a redacted CLI diagnostic locally" % result.returncode)
        return result.stdout

    def call(self, spec, context, readonly=False):
        validate_call(spec, readonly)
        call = render(spec, context)
        validate_call(call, readonly)
        if call.get("kind") == "obs-read":
            from .obs import probe
            return probe(self.config, call)
        if call.get("kind", "api") == "obs":
            args = call.get("args", [])
            if not all(isinstance(arg, str) for arg in args):
                raise DeliveryError("OBS arguments must resolve to strings")
            if any(arg.startswith(("-config", "-i=", "-k=", "-t=", "-e=", "-delete")) for arg in args):
                raise DeliveryError("OBS credentials/config and destructive sync flags cannot be overridden")
            buckets = {self.config.data["obs"].get(k) for k in ("site_bucket", "artifact_bucket", "storage_bucket")}
            for arg in args:
                if arg.startswith("obs://") and arg[6:].split("/")[0] not in buckets:
                    raise DeliveryError("OBS target is outside this customer's configured buckets")
            if call["command"] in ("cp", "sync"):
                storage = self.config.data["obs"].get("storage_bucket")
                if storage and any(arg.startswith("obs://") and arg[6:].split("/")[0] == storage for arg in args):
                    raise DeliveryError("Use Supabase Storage API for user files")
                if "-f" not in args:
                    args = args + ["-f"]
            config_file = self.config.local(self.config.data["obs"]["config_file"])
            if not config_file.is_file():
                raise DeliveryError("Customer-specific OBS configuration is missing")
            text = self._execute(["hcloud", "obs", call["command"], *args, "-config=" + str(config_file)])
            # OBS output is intentionally not used as an API response or persisted wholesale.
            return {"text": text}
        operation = call["operation"]
        def check_scope(value):
            if isinstance(value, dict):
                for key, item in value.items():
                    if key == "project_id" and item != self.config.data["project_id"]:
                        raise DeliveryError("API project_id differs from the configured customer project")
                    check_scope(item)
            elif isinstance(value, list):
                for item in value:
                    check_scope(item)
            elif isinstance(value, str) and value.startswith("urn:fss:"):
                parts = value.split(":")
                if len(parts) < 5 or parts[2:4] != [self.config.data["region"], self.config.data["project_id"]]:
                    raise DeliveryError("Function URN belongs to another region/project")
        check_scope(call.get("input", {}))
        # Validate API existence/parameters against installed KooCLI metadata, not copied schemas.
        self._execute(["hcloud", call["service"], operation, "--help"])
        fd, filename = tempfile.mkstemp(prefix="hwsupabase-", suffix=".json")
        try:
            with os.fdopen(fd, "w") as handle:
                json.dump(call.get("input", {}), handle)
            output = self._execute([
                "hcloud", call["service"], operation,
                "--cli-profile=" + self.config.data["profile"],
                "--cli-region=" + self.config.data["region"],
                "--cli-jsonInput=" + filename,
            ])
            try:
                result = json.loads(output)
            except ValueError:
                if not output.strip():
                    return {}
                raise DeliveryError("KooCLI did not return JSON; do not treat this as success") from None
            if not isinstance(result, (dict, list)):
                raise DeliveryError("Unexpected KooCLI response type")
            if isinstance(result, dict) and (result.get("error_code") or result.get("error")):
                raise DeliveryError("Cloud API returned an error; no success checkpoint written")
            return result
        finally:
            Path(filename).unlink(missing_ok=True)
