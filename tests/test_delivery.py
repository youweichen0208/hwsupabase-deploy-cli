import copy
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from email.message import Message
from types import SimpleNamespace
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from hwsupabase.core import Config, DeliveryError, State, atomic_json, digest
from hwsupabase.cloud import Cloud
from hwsupabase.workflow import execute, load_workflow
from hwsupabase.artifacts import build_web, build_python, scan_secrets
from hwsupabase.verification import activate, register_release, verify
from hwsupabase.obs import probe

ROOT = Path(__file__).resolve().parents[1]


class CloudDouble:
    def __init__(self, ready=False, fail=False, delayed=False):
        self.ready, self.fail, self.delayed = ready, fail, delayed
        self.writes = 0

    def call(self, call, context, readonly=False):
        if readonly:
            return {"resources": [{"id": "resource-1", "name": "customer-function", "status": "ACTIVE"}] if self.ready else []}
        self.writes += 1
        if self.fail:
            raise DeliveryError("simulated timeout")
        if not self.delayed:
            self.ready = True
        return {"id": "resource-1"}


def recipe():
    return {"version": 1, "id": "setup-v1", "phase": "setup", "steps": [{
        "id": "function", "ownership": "created",
        "apply": {"service": "FunctionGraph", "operation": "CreateFunction", "input": {"body": {"func_name": "customer-function"}}},
        "capture": {"id": "id"},
        "probe": {"call": {"service": "FunctionGraph", "operation": "ListFunctions"},
                  "select": {"path": "resources", "where": {"name": "customer-function"}},
                  "expect": {"status": "ACTIVE"}, "capture": {"id": "id"}},
    }]}


class DeliveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        import yaml
        self.data = yaml.safe_load((ROOT / "examples" / "hwsupabase.yaml").read_text())
        self.path = self.root / "hwsupabase.yaml"
        self.save_config()

    def tearDown(self):
        self.temp.cleanup()

    def save_config(self):
        atomic_json(self.path, self.data)
        self.config = Config(self.path)

    def test_duplicate_run_reconciles_without_second_create(self):
        cloud = CloudDouble()
        execute(self.config, recipe(), cloud, wait_seconds=0)
        execute(self.config, recipe(), cloud, wait_seconds=0)
        self.assertEqual(cloud.writes, 1)
        state = State(self.config).data
        self.assertEqual(state["runs"]["setup-v1"]["steps"]["function"]["outputs"]["id"], "resource-1")

    def test_timeout_does_not_recreate_and_can_observe_late_success(self):
        cloud = CloudDouble(fail=True)
        with self.assertRaises(DeliveryError):
            execute(self.config, recipe(), cloud, wait_seconds=0)
        with self.assertRaisesRegex(DeliveryError, "Uncertain mutation"):
            execute(self.config, recipe(), cloud, wait_seconds=0)
        self.assertEqual(cloud.writes, 1)
        cloud.ready = True
        execute(self.config, recipe(), cloud, wait_seconds=0)
        self.assertEqual(cloud.writes, 1)
        recovered = State(self.config).data["runs"]["setup-v1"]["steps"]["function"]["outputs"]
        self.assertEqual(recovered["id"], "resource-1")

    def test_capture_must_be_recoverable_after_timeout(self):
        workflow = recipe()
        workflow["steps"][0]["probe"]["capture"] = {}
        path = self.root / "workflow.yaml"
        atomic_json(path, workflow)
        with self.assertRaisesRegex(DeliveryError, "recoverable"):
            load_workflow(path)

    def test_partial_list_cannot_be_used_to_create_duplicate(self):
        class PartialCloud(CloudDouble):
            def call(self, call, context, readonly=False):
                if readonly:
                    return {"resources": [], "count": 42, "next_marker": 10}
                return super().call(call, context, readonly)
        cloud = PartialCloud()
        with self.assertRaisesRegex(DeliveryError, "Incomplete list"):
            execute(self.config, recipe(), cloud, wait_seconds=0)
        self.assertEqual(cloud.writes, 0)

    def test_readiness_resume_preserves_returned_id(self):
        cloud = CloudDouble(delayed=True)
        with self.assertRaisesRegex(DeliveryError, "not ready"):
            execute(self.config, recipe(), cloud, wait_seconds=0)
        state = State(self.config).data
        step = state["runs"]["setup-v1"]["steps"]["function"]
        self.assertEqual(step["status"], "waiting")
        self.assertEqual(step["outputs"]["id"], "resource-1")
        cloud.ready = True
        execute(self.config, recipe(), cloud, wait_seconds=0)
        self.assertEqual(cloud.writes, 1)

    def test_drift_and_changed_workflow_fail_closed(self):
        cloud = CloudDouble()
        execute(self.config, recipe(), cloud, wait_seconds=0)
        cloud.ready = False
        with self.assertRaisesRegex(DeliveryError, "drift"):
            execute(self.config, recipe(), cloud, wait_seconds=0)
        changed = recipe()
        changed["steps"][0]["apply"]["input"]["body"]["func_name"] = "another"
        with self.assertRaisesRegex(DeliveryError, "changed"):
            execute(self.config, changed, cloud)
        self.assertEqual(cloud.writes, 1)

    def test_reuse_never_mutates_mismatched_resource(self):
        workflow = recipe()
        workflow["steps"][0]["ownership"] = "reused"
        cloud = CloudDouble()
        with self.assertRaisesRegex(DeliveryError, "Reused resource"):
            execute(self.config, workflow, cloud)
        self.assertEqual(cloud.writes, 0)

    def test_lock_and_project_identity(self):
        with State(self.config).locked():
            with self.assertRaisesRegex(DeliveryError, "Another process"):
                with State(self.config).locked():
                    pass
        execute(self.config, recipe(), CloudDouble(), wait_seconds=0)
        self.data["project_id"] = "other-project"
        self.save_config()
        with self.assertRaisesRegex(DeliveryError, "identity mismatch"):
            State(self.config)

    def test_secret_references_and_api_request_cleanup(self):
        call = {"service": "FunctionGraph", "operation": "UpdateFunctionConfig", "input": {
            "body": {"encrypted_user_data": {"$json": {"PASSWORD": {"$env": "TEST_SECRET"}}}}}}
        filenames = []
        def invoke(args, **kwargs):
            for arg in args:
                if arg.startswith("--cli-jsonInput="):
                    path = Path(arg.split("=", 1)[1])
                    filenames.append(path)
                    self.assertEqual(path.stat().st_mode & 0o777, 0o600)
                    self.assertIn("secret-example-value", path.read_text())
                    self.assertNotIn("secret-example-value", " ".join(args))
            return SimpleNamespace(returncode=0, stdout="{}", stderr="")
        with patch.dict(os.environ, {"TEST_SECRET": "secret-example-value"}), patch("subprocess.run", side_effect=invoke):
            Cloud(self.config).call(call, {})
        self.assertTrue(filenames)
        self.assertFalse(any(p.exists() for p in filenames))

    def test_reject_wrong_project_and_function_urn(self):
        for value in ({"project_id": "wrong"}, {"function_urn": "urn:fss:other-region:wrong:function:default:fn:latest"}):
            with patch("subprocess.run") as runner:
                with self.assertRaises(DeliveryError):
                    Cloud(self.config).call({"service": "FunctionGraph", "operation": "UpdateFunctionCode", "input": {"path": value}}, {})
                runner.assert_not_called()

    def test_obs_never_writes_supabase_storage_with_or_without_slash(self):
        self.data["obs"]["storage_bucket"] = "example-storage"
        self.save_config()
        for target in ("obs://example-storage", "obs://example-storage/folder"):
            with self.assertRaisesRegex(DeliveryError, "Supabase Storage"):
                Cloud(self.config).call({"kind": "obs", "command": "cp", "args": ["local", target, "-r"]}, {})

    def test_obs_probe_distinguishes_missing_from_forbidden(self):
        client = SimpleNamespace(getBucketMetadata=lambda name: SimpleNamespace(status=404), close=lambda: None)
        env = {"HWC_OBS_ACCESS_KEY": "ak", "HWC_OBS_SECRET_KEY": "sk"}
        call = {"target": "bucket", "bucket": self.data["obs"]["artifact_bucket"]}
        with patch.dict(os.environ, env):
            self.assertEqual(probe(self.config, call, factory=lambda **kwargs: client), {"exists": False})
            client.getBucketMetadata = lambda name: SimpleNamespace(status=403)
            with self.assertRaisesRegex(DeliveryError, "permissions"):
                probe(self.config, call, factory=lambda **kwargs: client)

    def test_web_build_is_immutable_and_rejects_secret_output(self):
        output = self.root / "web" / "dist"
        output.mkdir(parents=True)
        (output / "index.html").write_text("<!doctype html><h1>ok</h1>")
        self.data["web"]["build"] = []
        self.save_config()
        first = build_web(self.config, "r1")
        self.assertFalse(first["cloud_verified"])
        with self.assertRaisesRegex(DeliveryError, "Immutable"):
            build_web(self.config, "r1")
        (output / "bundle.js").write_text("server-secret-example")
        with patch.dict(os.environ, {"SUPABASE_SERVICE_KEY": "server-secret-example"}):
            with self.assertRaisesRegex(DeliveryError, "server secret"):
                build_web(self.config, "r2")

    def test_python_requires_pinned_build_and_safe_includes(self):
        with self.assertRaisesRegex(DeliveryError, "sha256"):
            build_python(self.config, "r1")
        self.data["python"]["build_image"] = "example/image@sha256:" + "a" * 64
        self.data["python"]["include"] = ["../outside"]
        self.save_config()
        with self.assertRaisesRegex(DeliveryError, "include"):
            build_python(self.config, "r1")

    def test_openssh_private_key_is_rejected(self):
        private = self.root / "accidentally-renamed.txt"
        private.write_text("-----BEGIN OPENSSH PRIVATE KEY-----\nexample\n")
        with self.assertRaisesRegex(DeliveryError, "Private key"):
            scan_secrets(private, self.config)

    def test_service_role_jwt_rejected_even_without_environment_value(self):
        import base64
        payload = base64.urlsafe_b64encode(json.dumps({"role": "service_role"}).encode()).rstrip(b"=")
        path = self.root / "bundle.js"
        path.write_bytes(b"eyJhbGciOiJIUzI1NiJ9." + payload + b".abc123")
        with self.assertRaisesRegex(DeliveryError, "service-role JWT"):
            scan_secrets(path, self.config)

    def test_actual_static_example_build_receives_only_public_config(self):
        import shutil
        if not shutil.which("node"):
            self.skipTest("Node is unavailable")
        shutil.copytree(ROOT / "examples" / "web", self.root / "web")
        with patch.dict(os.environ, {"SUPABASE_PUBLIC_KEY": "public-example-key", "SUPABASE_SERVICE_KEY": "private-example-key"}):
            result = build_web(self.config, "web-smoke")
        output = Path(result["directory"])
        public = json.loads((output / "config.json").read_text())
        self.assertEqual(public["publicKey"], "public-example-key")
        self.assertEqual(public["release"], "web-smoke")
        self.assertNotIn("private-example-key", (output / "config.json").read_text())

    def test_skill_relative_links_resolve(self):
        import re
        for file in (ROOT / "skills").rglob("*.md"):
            for target in re.findall(r"\]\(([^)]+)\)", file.read_text()):
                if "://" not in target and not target.startswith("#"):
                    self.assertTrue((file.parent / target.split("#")[0]).exists(), str(file) + " -> " + target)

    def test_python_zip_bootstrap_and_linux_dependencies(self):
        import zipfile
        source = self.root / "flask"
        source.mkdir()
        (source / "app.py").write_text("app = None\n")
        (source / "requirements.txt").write_text("gunicorn==26.2.0\n")
        self.data["python"]["build_image"] = "example/image@sha256:" + "a" * 64
        self.save_config()
        def simulate_build(args, cwd, env, timeout=900):
            self.assertIn("docker", args)
            self.assertNotIn("SUPABASE_SERVICE_KEY", env)
            package = self.config.state_dir / "artifacts" / "r1" / "python-package"
            gunicorn = package / "python" / "gunicorn"
            gunicorn.mkdir(parents=True)
            (gunicorn / "__init__.py").write_text("")
        with patch("hwsupabase.artifacts.run_build", side_effect=simulate_build):
            result = build_python(self.config, "r1")
        with zipfile.ZipFile(result["path"]) as archive:
            self.assertEqual(archive.getinfo("bootstrap").external_attr >> 16, 0o100755)
            self.assertIn(b"127.0.0.1:8000", archive.read("bootstrap"))
            self.assertIn("python/gunicorn/__init__.py", archive.namelist())

    def test_release_registration_and_rollback_are_bound_to_release(self):
        state = State(self.config)
        for release in ("r1", "r2"):
            state.data["runs"]["stage-" + release] = {"status": "complete", "phase": "stage", "release": release,
                "steps": {"function": {"outputs": {"urn": "urn:sample", "version": release}}}}
        state.save()
        for release in ("r1", "r2"):
            folder = self.config.state_dir / "artifacts" / release
            for file in ("web-manifest.json", "python-manifest.json"):
                atomic_json(folder / file, {"release": release, "files": []})
            atomic_json(folder / "apig.json", {"backend_type": "FUNCTION"})
            metadata = {"id": release, "stage_workflow": "stage-" + release, "function_urn": "urn:sample",
                        "function_version": release, "web_manifest": str(folder / "web-manifest.json"),
                        "python_manifest": str(folder / "python-manifest.json"), "apig_snapshot": str(folder / "apig.json")}
            path = self.root / (release + ".yaml")
            atomic_json(path, metadata)
            register_release(self.config, path)
        for release, phase in (("r1", "promote"), ("r2", "promote"), ("r1", "rollback")):
            state = State(self.config)
            workflow = phase + "-" + release
            state.data["runs"][workflow] = {"status": "complete", "phase": phase, "release": release}
            state.save()
            atomic_json(self.config.state_dir / "reports" / (release + ".json"), {
                "release": release, "passed": True, "config_digest": digest(self.config.data), "runs_digest": digest(state.data["runs"])})
            result = activate(self.config, release, workflow)
            self.assertEqual(result["current"], release)
        self.assertEqual(result["previous"], "r2")
        with self.assertRaises(DeliveryError):
            activate(self.config, "r2", "rollback-r1")

    def test_http_verification_checks_cookie_count_and_body(self):
        cases = {"cases": [{"id": category, "category": category, "url": "https://example.test/", "expect": {
            "status": 200, "body": "ok", "header_counts": {"Set-Cookie": 2}, "release": {"header": "X-HWSupabase-Release"}}} for category in ("api", "web", "supabase")]}
        path = self.root / "cases.yaml"
        atomic_json(path, cases)
        class Response(io.BytesIO):
            code = 200
            def __init__(self):
                super().__init__(b"ok")
                self.headers = Message()
                self.headers.add_header("Set-Cookie", "a=1")
                self.headers.add_header("Set-Cookie", "b=2")
                self.headers.add_header("X-HWSupabase-Release", "r1")
        opener = SimpleNamespace(open=lambda *args, **kwargs: Response())
        report = verify(self.config, "r1", path, opener=opener)
        self.assertTrue(report["passed"])
        cases["cases"][0]["expect"]["header_counts"]["Set-Cookie"] = 3
        atomic_json(path, cases)
        self.assertFalse(verify(self.config, "r1", path, opener=opener)["passed"])

    def test_activation_requires_correct_release_and_fresh_verification(self):
        state = State(self.config)
        state.data["releases"]["r1"] = {"metadata": {}, "manifest_digests": {}}
        state.data["runs"]["promote-r1"] = {"status": "complete", "phase": "promote", "release": "r1"}
        state.save()
        report = {"release": "r1", "passed": True, "config_digest": digest(self.config.data), "runs_digest": digest(state.data["runs"])}
        atomic_json(self.config.state_dir / "reports" / "r1.json", report)
        self.assertEqual(activate(self.config, "r1", "promote-r1")["current"], "r1")
        state = State(self.config)
        state.data["runs"]["other"] = {"status": "complete"}
        state.save()
        with self.assertRaisesRegex(DeliveryError, "stale"):
            activate(self.config, "r1", "promote-r1")

    def test_recipe_validation_rejects_mutating_probe_and_literal_secret(self):
        for mutation in ("probe", "secret"):
            value = recipe()
            if mutation == "probe":
                value["steps"][0]["probe"]["call"]["operation"] = "CreateFunction"
            else:
                value["steps"][0]["apply"]["input"]["body"]["password"] = "literal"
            path = self.root / "workflow.yaml"
            atomic_json(path, value)
            with self.assertRaises(DeliveryError):
                load_workflow(path)

    def test_standalone_install_includes_shared_helper(self):
        destination = self.root / "installed"
        subprocess.run([sys.executable, str(ROOT / "scripts" / "install_skills.py"), "--destination", str(destination)], check=True, capture_output=True)
        script = destination / "hw-supabase-deliver" / "scripts" / "deploy.py"
        result = subprocess.run([sys.executable, str(script), "--config", str(self.path), "preflight"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(json.loads(result.stdout)["cloud_verified"])

    def test_failed_promotion_rolls_back_to_last_verified_current(self):
        from contextlib import redirect_stdout
        from hwsupabase.cli import main
        state = State(self.config)
        state.data["current"] = "r1"
        state.data["previous"] = None
        state.data["releases"]["r1"] = {"metadata": {"id": "r1"}, "manifest_digests": {}}
        state.data["runs"]["promote-r2"] = {"phase": "promote", "release": "r2", "status": "partial"}
        state.save()
        stdout = io.StringIO()
        with redirect_stdout(stdout):
            code = main(["--config", str(self.path), "rollback-plan", "--failed-promotion"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(stdout.getvalue())["target"], "r1")
        self.assertEqual(State(self.config).data["current"], "r1")

    def test_mistyped_release_version_cannot_be_registered(self):
        state = State(self.config)
        state.data["runs"]["stage-r1"] = {"status": "complete", "phase": "stage", "release": "r1",
            "steps": {"version": {"outputs": {"urn": "urn:actual", "version": "r1"}}}}
        state.save()
        metadata = {"id": "r1", "stage_workflow": "stage-r1", "function_urn": "urn:different", "function_version": "r0"}
        path = self.root / "release.yaml"
        atomic_json(path, metadata)
        with self.assertRaisesRegex(DeliveryError, "captured together"):
            register_release(self.config, path)
        self.assertNotIn("r1", State(self.config).data["releases"])

    def test_old_version_returning_200_fails_new_release_verification(self):
        path = self.root / "cases.yaml"
        atomic_json(path, {"cases": [{"id": category, "category": category, "url": "https://example.test/",
            "expect": {"status": 200, "release": {"header": "X-Release"}}} for category in ("web", "api", "supabase")]})
        class OldVersion(io.BytesIO):
            code = 200
            def __init__(self):
                super().__init__(b"ok")
                self.headers = Message()
                self.headers.add_header("X-Release", "r1")
        report = verify(self.config, "r2", path, opener=SimpleNamespace(open=lambda *a, **k: OldVersion()))
        self.assertFalse(report["passed"])
        self.assertEqual(set(report["missing_release_categories"]), {"web", "api"})


if __name__ == "__main__":
    unittest.main()
