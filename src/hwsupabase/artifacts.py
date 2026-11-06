import hashlib
import base64
import json
import mimetypes
import os
from pathlib import Path
import re
import shutil
import subprocess
import zipfile

from .core import DeliveryError, atomic_json, environment_names, identifier


EXCLUDED = {".git", ".venv", "venv", "node_modules", "__pycache__", ".hwsupabase", ".aws", ".hcloud", ".ssh"}


def allowed_file(path):
    return (not any(part in EXCLUDED or part.startswith(".env") for part in path.parts)
            and path.suffix not in {".pem", ".key", ".pyc"}
            and not path.name.startswith(".obsutilconfig"))


def collect(source):
    if not source.is_dir():
        raise DeliveryError("Artifact source directory does not exist")
    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)
        if not allowed_file(relative):
            continue
        if path.is_symlink():
            raise DeliveryError("Artifact contains a symlink; materialize intended files first")
        if path.is_file():
            yield path, relative


def scan_secrets(path, config):
    values = [os.environ.get(name, "").encode() for name in environment_names(config.data)]
    # Public keys also excluded here: inject public frontend config during its build instead
    # and explicitly mark that environment name as public_key_env below.
    public_name = config.data.get("supabase", {}).get("public_key_env")
    public_value = os.environ.get(public_name, "").encode() if public_name else b""
    values = [v for v in values if len(v) >= 8 and v != public_value]
    with path.open("rb") as handle:
        tail = b""
        while True:
            block = handle.read(1024 * 1024)
            if not block:
                break
            data = tail + block
            if re.search(rb"-----BEGIN (?:[A-Z0-9 ]+ )?PRIVATE KEY-----", data):
                raise DeliveryError("Private key found in build output")
            if any(value in data for value in values):
                raise DeliveryError("Configured server secret found in build output")
            if re.search(rb"sb_secret_[A-Za-z0-9_-]+", data):
                raise DeliveryError("Supabase secret key found in build output")
            for token in re.findall(rb"eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", data):
                try:
                    payload = token.split(b".")[1]
                    claims = json.loads(base64.urlsafe_b64decode(payload + b"=" * (-len(payload) % 4)))
                except (ValueError, UnicodeDecodeError):
                    continue
                if isinstance(claims, dict) and claims.get("role") == "service_role":
                    raise DeliveryError("Supabase service-role JWT found in build output")
            tail = data[-max([128] + [len(v) for v in values]):]


def clean_environment(config):
    # Do not expose deployment credentials to package managers/build subprocesses.
    keep = {"PATH", "HOME", "TMPDIR", "LANG", "LC_ALL", "SYSTEMROOT"}
    env = {key: val for key, val in os.environ.items() if key in keep}
    public_name = config.data["supabase"].get("public_key_env")
    if public_name and os.environ.get(public_name):
        env[public_name] = os.environ[public_name]
    return env


def run_build(args, cwd, env, timeout=900):
    if not isinstance(args, list) or not args or not all(isinstance(s, str) for s in args):
        raise DeliveryError("Build command must be an argument list")
    try:
        result = subprocess.run(args, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired):
        raise DeliveryError("Build could not run or timed out; check build tool availability") from None
    if result.returncode:
        raise DeliveryError("Build failed (exit %d); run the same command locally with redacted diagnostics" % result.returncode)


def artifact_dir(config, release):
    identifier(release, "release ID")
    folder = config.state_dir / "artifacts" / release
    folder.mkdir(parents=True, exist_ok=True, mode=0o700)
    return folder


def build_web(config, release):
    spec = config.data.get("web")
    if not spec:
        raise DeliveryError("No web profile configured")
    source = config.local(spec["source"])
    env = clean_environment(config)
    env["SUPABASE_PUBLIC_URL"] = config.data["supabase"]["public_url"]
    env["HWSUPABASE_RELEASE"] = release
    if spec.get("build"):
        run_build(spec["build"], source, env)
    output = (source / spec["output"]).resolve()
    if not output.is_relative_to(source):
        raise DeliveryError("Web output must be inside its source directory")
    target = artifact_dir(config, release) / "web"
    if target.exists():
        raise DeliveryError("Immutable release output already exists; choose a new release ID")
    if not (output / "index.html").is_file():
        raise DeliveryError("Static build must include index.html; SSR output cannot be hosted on OBS")
    files = list(collect(output))
    for path, _ in files:
        scan_secrets(path, config)
    target.mkdir()
    manifest = []
    for path, relative in files:
        dest = target / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)
        hashed = bool(re.search(r"[.-][0-9a-fA-F]{8,}[.-]", path.name))
        manifest.append({"path": relative.as_posix(), "sha256": hashlib.sha256(dest.read_bytes()).hexdigest(),
                         "size": dest.stat().st_size, "content_type": mimetypes.guess_type(path.name)[0] or "application/octet-stream",
                         "cache_control": "public, max-age=31536000, immutable" if hashed and path.suffix != ".html" else "no-cache"})
    atomic_json(target.parent / "web-manifest.json", {"release": release, "files": manifest})
    return {"release": release, "directory": str(target), "files": len(manifest), "cloud_verified": False}


def build_python(config, release):
    spec = config.data.get("python")
    if not spec:
        raise DeliveryError("No Python profile configured")
    image = spec.get("build_image", "")
    if not re.fullmatch(r"[A-Za-z0-9._/:\-]+@sha256:[0-9a-f]{64}", image):
        raise DeliveryError("Set python.build_image to a runtime-compatible Linux image pinned by sha256 digest")
    source = config.local(spec["source"])
    includes = spec.get("include", [])
    if not includes or any(not isinstance(p, str) or Path(p).is_absolute() or ".." in Path(p).parts for p in includes):
        raise DeliveryError("Python profile needs an explicit relative include list")
    folder = artifact_dir(config, release)
    package = folder / "python-package"
    if package.exists() or (folder / "function.zip").exists():
        raise DeliveryError("Immutable Python release already exists; choose a new release ID")
    chosen = {}
    for item in includes:
        path = source / item
        if not allowed_file(Path(item)) or path.is_symlink() or not path.resolve().is_relative_to(source):
            raise DeliveryError("Python include escapes source")
        if path.is_dir():
            selected = [(p, p.relative_to(source)) for p, _ in collect(path)]
        elif path.is_file() and allowed_file(Path(item)):
            selected = [(path, Path(item))]
        else:
            raise DeliveryError("Missing or excluded Python include")
        for p, relative in selected:
            scan_secrets(p, config)
            chosen[relative] = p
    requirement = spec.get("requirements", "requirements.txt")
    if Path(requirement) not in chosen:
        raise DeliveryError("Include the requirements file in the package")
    package.mkdir()
    for relative, path in chosen.items():
        dest = package / relative
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, dest)
    platform = spec.get("platform", "linux/amd64")
    if platform not in ("linux/amd64", "linux/arm64"):
        raise DeliveryError("Unsupported build platform")
    command = ["docker", "run", "--rm", "--platform", platform,
               "--mount", "type=bind,src=" + str(package) + ",dst=/work", "--workdir", "/work", image,
               "python3.12", "-m", "pip", "install", "--disable-pip-version-check", "-r", requirement, "--target", "python"]
    run_build(command, source, clean_environment(config))
    if not (package / "python" / "gunicorn").is_dir():
        raise DeliveryError("Requirements must include Gunicorn")
    bootstrap = package / "bootstrap"
    bootstrap.write_text('#!/bin/sh\nset -eu\ncd "$(dirname "$0")"\n'
                         'export PYTHONPATH="$PWD/python:$PWD${PYTHONPATH:+:$PYTHONPATH}"\n'
                         'exec /opt/function/runtime/python3.12/rtsp/python/bin/python3 -m gunicorn '
                         '--bind 127.0.0.1:8000 --workers 1 --threads 4 --timeout 60 ' + spec["entrypoint"] + '\n')
    bootstrap.chmod(0o755)
    archive = folder / "function.zip"
    with zipfile.ZipFile(archive, "w", compression=zipfile.ZIP_DEFLATED) as handle:
        for path, relative in collect(package):
            scan_secrets(path, config)
            info = zipfile.ZipInfo(relative.as_posix(), (2020, 1, 1, 0, 0, 0))
            info.create_system = 3
            info.external_attr = (0o100755 if relative.as_posix() == "bootstrap" else 0o100644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            handle.writestr(info, path.read_bytes())
    metadata = {"release": release, "path": str(archive), "sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
                "size": archive.stat().st_size, "runtime": "http", "python": "3.12", "build_image": image,
                "platform": platform, "cloud_verified": False}
    atomic_json(folder / "python-manifest.json", metadata)
    return metadata
