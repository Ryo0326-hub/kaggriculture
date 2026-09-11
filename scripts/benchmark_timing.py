"""Controlled timing experiments on the same installed portfolios as Cycle 2."""

import argparse
import json
from concurrent.futures import ProcessPoolExecutor
from datetime import UTC, datetime
from pathlib import Path

from evaluate import environment_metadata, sha256
from experiments import timing
from scripts.benchmark_staffing import run_fixture
from scripts.make_timing_control import MODES

FLAGS = {name: {"timing": value} for name, value in MODES.items()}


def job(args):
    return run_fixture(*args, policy_name="experiments.timing", modes=FLAGS, timing_events=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seeds", type=int, nargs="+", default=[17, 43])
    parser.add_argument("--quadrants", type=int, nargs="+", choices=[1, 2, 3], default=[1, 2, 3])
    parser.add_argument(
        "--modes", nargs="+", choices=MODES, default=["fertilizer", "harvest", "combined"]
    )
    parser.add_argument("--workers", type=int, default=2)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.workers < 1 or any(
        len(v) != len(set(v)) for v in (args.seeds, args.quadrants, args.modes)
    ):
        parser.error("Use positive concurrency and distinct seeds, portfolios and modes")
    args.output.mkdir(parents=True, exist_ok=False)
    manifest = {
        "created_at": datetime.now(UTC).isoformat(),
        "environment": environment_metadata(),
        "kind": "Installed portfolios; no capital purchases; not competition scores",
        "source_sha256": sha256(timing.__file__),
        "runner_sha256": sha256(__file__),
        "fixture_runner_sha256": sha256(Path(__file__).with_name("benchmark_staffing.py")),
        "seeds": args.seeds,
        "seats": [0, 1],
        "quadrants": args.quadrants,
        "modes": args.modes,
        "workers": args.workers,
        "starting_money": 30000,
        "initial_inputs": {"WHEAT": 20, "FERTILIZER": 20},
        "initial_crops_watered": True,
    }
    (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
    jobs = [
        (seed, seat, q, mode)
        for mode in args.modes
        for q in args.quadrants
        for seed in args.seeds
        for seat in (0, 1)
    ]
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        with (args.output / "matches.jsonl").open("x") as file:
            for row in pool.map(job, jobs):
                file.write(json.dumps(row) + "\n")
                file.flush()
                print(
                    f"{row['mode']} q={row['quadrants']} seed={row['seed']} "
                    f"seat={row['candidate_seat']} cash={row['cash_difference']:+.0f} "
                    f"wage_saving={row['wage_saving']:+.0f}",
                    flush=True,
                )
    assert sha256(timing.__file__) == manifest["source_sha256"]


if __name__ == "__main__":
    main()
