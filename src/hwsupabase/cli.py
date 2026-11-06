import argparse
import json
import shutil
import sys

from .core import Config, DeliveryError, State, digest
from .workflow import execute, load_workflow
from .artifacts import build_python, build_web
from .verification import activate, register_release, verify
from .obs import configure_site


def parser():
    result = argparse.ArgumentParser(description="Internal helpers for the hw-supabase delivery skills")
    result.add_argument("--config", default="hwsupabase.yaml")
    sub = result.add_subparsers(dest="command", required=True)
    sub.add_parser("preflight")
    sub.add_parser("status")
    for command in ("plan", "run"):
        p = sub.add_parser(command)
        p.add_argument("workflow")
    for command in ("build-web", "build-python"):
        p = sub.add_parser(command)
        p.add_argument("release")
    p = sub.add_parser("verify")
    p.add_argument("release")
    p.add_argument("cases")
    p = sub.add_parser("register-release")
    p.add_argument("metadata")
    p = sub.add_parser("activate")
    p.add_argument("release")
    p.add_argument("workflow")
    p = sub.add_parser("rollback-plan")
    p.add_argument("--release")
    p.add_argument("--failed-promotion", action="store_true", help="Restore the last verified current release after a failed promotion")
    p = sub.add_parser("obs-site")
    p.add_argument("settings")
    return result


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        config = Config(args.config)
        if args.command == "preflight":
            tools = {name: shutil.which(name) is not None for name in ("hcloud", "docker")}
            output = {"identity": config.identity, "config_valid": True, "tools": tools,
                      "obs_config_exists": config.local(config.data["obs"]["config_file"]).is_file(),
                      "cloud_verified": False, "next": "Check account identity, region capabilities, costs and current cloud resource state using official tools"}
        elif args.command == "status":
            output = State(config).data
        elif args.command in ("plan", "run"):
            recipe = load_workflow(args.workflow)
            if args.command == "plan":
                output = {"id": recipe["id"], "phase": recipe["phase"], "fingerprint": digest({"recipe": recipe, "config": config.data}),
                          "steps": [{"id": s["id"], "ownership": s["ownership"],
                                     "operation": s["apply"].get("operation", s["apply"].get("command"))} for s in recipe["steps"]],
                          "cloud_verified": False}
            else:
                output = execute(config, recipe)
        elif args.command == "build-web":
            with State(config).locked():
                output = build_web(config, args.release)
        elif args.command == "build-python":
            with State(config).locked():
                output = build_python(config, args.release)
        elif args.command == "verify":
            output = verify(config, args.release, args.cases)
        elif args.command == "register-release":
            output = register_release(config, args.metadata)
        elif args.command == "activate":
            output = activate(config, args.release, args.workflow)
        elif args.command == "rollback-plan":
            state = State(config).data
            release = args.release or (state["current"] if args.failed_promotion else state["previous"])
            if release not in state["releases"]:
                raise DeliveryError("No registered rollback target")
            output = {"target": release, "release": state["releases"][release], "cloud_changed": False,
                      "next": "Generate a rollback workflow from saved metadata; run, verify, then activate"}
        else:
            with State(config).locked():
                output = configure_site(config, args.settings)
        print(json.dumps(output, ensure_ascii=False, indent=2))
        return 1 if args.command == "verify" and not output["passed"] else 0
    except DeliveryError as error:
        print(json.dumps({"error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2
    except (KeyError, TypeError, ValueError, OSError):
        print(json.dumps({"error": "Invalid input or local I/O failure; check configuration and file permissions"}), file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
