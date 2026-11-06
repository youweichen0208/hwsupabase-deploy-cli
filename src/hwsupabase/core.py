import contextlib
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from urllib.parse import urlsplit

import yaml


class DeliveryError(Exception):
    """An actionable failure whose text must not contain credentials."""


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def read_document(path):
    try:
        value = yaml.safe_load(Path(path).read_text())
    except (OSError, yaml.YAMLError):
        raise DeliveryError("Cannot read document; check path and YAML/JSON syntax") from None
    if not isinstance(value, dict):
        raise DeliveryError("Document must be a mapping")
    return value


def identifier(value, name="identifier"):
    if not isinstance(value, str) or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}", value):
        raise DeliveryError("Invalid " + name)
    return value


def lookup(value, path):
    if path == "":
        return value
    try:
        for part in path.split("."):
            value = value[int(part)] if isinstance(value, list) else value[part]
        return value
    except (KeyError, IndexError, TypeError, ValueError):
        raise DeliveryError("Required field is missing: " + path) from None


def environment_names(value):
    names = set()
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "$env" or key.endswith("_env"):
                if isinstance(item, str):
                    names.add(item)
            else:
                names.update(environment_names(item))
    elif isinstance(value, list):
        for item in value:
            names.update(environment_names(item))
    return names


def no_literal_secrets(value):
    """Reject common credential fields unless their values are environment references."""
    sensitive = re.compile(r"^(ak|sk|password|secret|secret_key|service_key|service_role_key|"
                           r"access_key|access_key_id|token|authorization|apikey|database_url)$", re.I)
    if isinstance(value, dict):
        for key, item in value.items():
            if sensitive.fullmatch(key) and item not in (None, ""):
                if not isinstance(item, dict) or set(item) != {"$env"}:
                    raise DeliveryError("Use an environment reference for sensitive field: " + key)
            no_literal_secrets(item)
    elif isinstance(value, list):
        for item in value:
            no_literal_secrets(item)


def render(value, context):
    if isinstance(value, dict):
        if set(value) == {"$ref"}:
            return lookup(context, value["$ref"])
        if set(value) == {"$env"}:
            name = value["$env"]
            if not isinstance(name, str) or not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", name):
                raise DeliveryError("Invalid environment variable reference")
            if not os.environ.get(name):
                raise DeliveryError("Missing environment variable: " + name)
            return os.environ[name]
        if set(value) == {"$json"}:
            return json.dumps(render(value["$json"], context), separators=(",", ":"))
        return {key: render(item, context) for key, item in value.items()}
    if isinstance(value, list):
        return [render(item, context) for item in value]
    return value


def check_url(value, https=False):
    parsed = urlsplit(value)
    if (parsed.scheme not in (["https"] if https else ["http", "https"])
            or not parsed.hostname or parsed.username or parsed.password
            or parsed.fragment):
        raise DeliveryError("Expected an HTTP URL without credentials" + (" using HTTPS" if https else ""))
    return value


class Config:
    def __init__(self, path):
        self.path = Path(path).resolve()
        self.root = self.path.parent
        self.data = read_document(self.path)
        no_literal_secrets(self.data)
        if self.data.get("version") != 1:
            raise DeliveryError("Configuration version must be 1")
        for name in ("customer", "environment", "region", "profile", "project_id"):
            identifier(self.data.get(name), name)
        supabase = self.data.get("supabase", {})
        identifier(supabase.get("application_id"), "Supabase application ID")
        check_url(supabase.get("public_url", ""), https=True)
        check_url(supabase.get("internal_url", ""))
        for name in ("vpc_id", "subnet_id", "security_group_id"):
            identifier(self.data.get("network", {}).get(name), name)
        obs = self.data.get("obs", {})
        check_url(obs.get("endpoint", ""), https=True)
        buckets = [obs.get(key) for key in ("site_bucket", "artifact_bucket", "storage_bucket") if obs.get(key)]
        if not obs.get("artifact_bucket") or len(set(buckets)) != len(buckets):
            raise DeliveryError("Specify an artifact bucket and distinct site/artifact/storage buckets")
        for bucket in buckets:
            if not re.fullmatch(r"[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]", bucket):
                raise DeliveryError("Invalid OBS bucket name")
        if not isinstance(obs.get("config_file"), str) or not obs["config_file"]:
            raise DeliveryError("Specify a customer-specific OBS config_file")
        apig = self.data.get("apig", {})
        if apig.get("mode") not in ("create", "reuse"):
            raise DeliveryError("APIG mode must be create or reuse")
        if apig["mode"] == "reuse":
            identifier(apig.get("instance_id"), "APIG instance ID")
        else:
            for key in ("spec_id", "network_id", "available_zone_ids"):
                if not apig.get(key):
                    raise DeliveryError("APIG create requires " + key)
        python = self.data.get("python")
        if python:
            if python.get("framework") not in ("flask", "django") or python.get("version") != "3.12":
                raise DeliveryError("v1 Python profile supports Flask/Django on Python 3.12")
            if not re.fullmatch(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*:[A-Za-z_]\w*", python.get("entrypoint", "")):
                raise DeliveryError("Use an explicit module:object WSGI entrypoint")
        self.identity = {key: self.data[key] for key in ("customer", "environment", "region", "profile", "project_id")}
        self.state_dir = self.root / ".hwsupabase" / self.data["customer"] / self.data["environment"]

    def local(self, path):
        return (self.root / Path(path).expanduser()).resolve()


def atomic_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, temp = tempfile.mkstemp(dir=path.parent, prefix=".write-", suffix=".json")
    try:
        with os.fdopen(fd, "w") as handle:
            json.dump(data, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


class State:
    def __init__(self, config):
        self.config = config
        self.path = config.state_dir / "state.json"
        self.data = {"version": 1, "identity": config.identity, "runs": {}, "releases": {}, "current": None, "previous": None}
        if self.path.exists():
            self.data = read_document(self.path)
            if self.data.get("identity") != config.identity or self.data.get("version") != 1:
                raise DeliveryError("State identity mismatch; do not reuse state across accounts or regions")

    @contextlib.contextmanager
    def locked(self):
        # Advisory OS locks release on process death; no stale PID file guessing.
        import fcntl
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with open(self.path.parent / "lock", "a") as handle:
            os.chmod(handle.name, 0o600)
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError:
                raise DeliveryError("Another process is deploying this customer/environment") from None
            try:
                # Reload after locking, not from a potentially stale constructor snapshot.
                refreshed = State(self.config)
                self.data = refreshed.data
                yield self
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)

    def save(self):
        atomic_json(self.path, self.data)
