"""Copy and validate the exact single-file artifact outside the repository import path."""

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path

VALIDATOR = r"""
import hashlib
import json
import platform
import sys
from importlib.metadata import version
from pathlib import Path
from kaggle_environments import make
from kaggle_environments.envs.kaggriculture import kaggriculture as engine

artifact = Path(sys.argv[1])
env = make("kaggriculture", configuration={"seed": 505, "episodeSteps": 720})
env.run([str(artifact), str(artifact)])
failures = [
    {"state": i, "player": p, "status": s.status}
    for i, states in enumerate(env.steps) for p, s in enumerate(states)
    if s.status in {"ERROR", "INVALID", "TIMEOUT"}
]
statuses = [s.status for s in env.steps[-1]]
durations = [log["duration"] for turn in env.logs for log in turn if "duration" in log]
stderr = [log["stderr"] for turn in env.logs for log in turn if log.get("stderr")]
result = {
    "kind": "local isolated official-loader self-play; not Kaggle server validation",
    "sha256": hashlib.sha256(artifact.read_bytes()).hexdigest(),
    "bytes": artifact.stat().st_size,
    "python": platform.python_version(),
    "kaggle_environments": version("kaggle-environments"),
    "engine_sha256": hashlib.sha256(Path(engine.__file__).read_bytes()).hexdigest(),
    "configuration": dict(env.configuration),
    "seed": env.info["seed"],
    "recorded_states": len(env.steps),
    "statuses": statuses,
    "failures": failures,
    "stderr": stderr,
    "cash": [s.observation.farms[p]["money"] for p, s in enumerate(env.steps[-1])],
    "unsold_shed_units": [sum(s.observation.private["shed"].values()) for s in env.steps[-1]],
    "unsold_carried_units": [sum(sum(inv.values()) for inv in s.observation.private["inventories"])
                             for s in env.steps[-1]],
    "unused_seeds": [sum(s.observation.private["seeds"].values()) for s in env.steps[-1]],
    "decision_max_seconds": max(durations, default=0),
}
result["passed"] = (not failures and not stderr and statuses == ["DONE", "DONE"]
                    and len(env.steps) == 720
                    and max(durations, default=0) < env.configuration.actTimeout)
print("VALIDATION_JSON=" + json.dumps(result))
"""


def prepare(source, output):
    source, output = Path(source).resolve(), Path(output).resolve()
    payload = source.read_bytes()
    # Never replace an existing release or experiment.
    output.mkdir(parents=True, exist_ok=False)
    artifact = output / "main.py"
    artifact.write_bytes(payload)
    process = subprocess.run(
        [sys.executable, "-I", "-c", VALIDATOR, str(artifact)],
        cwd=output,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    (output / "validation.log").write_text(process.stdout + process.stderr)
    reports = [
        line.removeprefix("VALIDATION_JSON=")
        for line in process.stdout.splitlines()
        if line.startswith("VALIDATION_JSON=")
    ]
    if process.returncode or not reports:
        raise RuntimeError(f"Validation process failed; see {output / 'validation.log'}")
    result = json.loads(reports[-1])
    unchanged = artifact.read_bytes() == payload
    if not unchanged or result["sha256"] != hashlib.sha256(payload).hexdigest():
        result["passed"] = False
        result["artifact_changed"] = True
    (output / "validation.json").write_text(json.dumps(result, indent=2) + "\n")
    if not result["passed"]:
        raise RuntimeError(f"Artifact failed validation; see {output / 'validation.json'}")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, default=Path("main.py"))
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = prepare(args.source, args.output)
    print(f"Local validation passed: {args.output / 'main.py'}")
    print(f"SHA-256: {report['sha256']}")
    print("Only main.py is the submission artifact. Kaggle upload has not been performed.")


if __name__ == "__main__":
    main()
