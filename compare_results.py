"""Compare complete common-pool runs, resampling whole seed blocks rather than games."""

import argparse
import json
import random
import statistics
from pathlib import Path

SCORES = {"win": 1.0, "draw": 0.5, "loss": 0.0}


def read_run(directory):
    path = Path(directory)
    manifest = json.loads((path / "manifest.json").read_text())
    rows = [json.loads(line) for line in (path / "matches.jsonl").read_text().splitlines()]
    expected = {
        (seed, seat, opponent["id"])
        for seed in manifest["seeds"]
        for seat in manifest["seats"]
        for opponent in manifest["opponents"]
    }
    keyed = {(r["seed"], r["seat"], r["opponent"]): r for r in rows}
    if len(rows) != len(keyed) or set(keyed) != expected:
        raise ValueError("Run is incomplete or contains duplicate/unexpected games")
    if any(r["outcome"] not in SCORES for r in rows):
        raise ValueError("Resolve agent errors before a competitive comparison")
    return manifest, keyed


def compare(candidate_directory, reference_directory):
    candidate, rows = read_run(candidate_directory)
    reference, old = read_run(reference_directory)
    for field in [
        "environment",
        "configuration",
        "runner_sha256",
        "lock_sha256",
        "seeds",
        "seats",
        "opponents",
        "episode_steps",
    ]:
        if candidate[field] != reference[field]:
            raise ValueError(f"Unmatched comparison field: {field}")
    seeds = candidate["seeds"]
    if len(seeds) < 2:
        raise ValueError("At least two distinct seed blocks are required")
    blocks = [
        statistics.mean(
            SCORES[rows[k]["outcome"]] - SCORES[old[k]["outcome"]] for k in rows if k[0] == seed
        )
        for seed in seeds
    ]
    rng = random.Random(0)
    boot = sorted(statistics.mean(rng.choices(blocks, k=len(blocks))) for _ in range(10000))
    return {
        "candidate": candidate["candidate"],
        "reference": reference["candidate"],
        "games_per_agent": len(rows),
        "seed_blocks": len(seeds),
        "candidate_match_score": statistics.mean(SCORES[r["outcome"]] for r in rows.values()),
        "reference_match_score": statistics.mean(SCORES[r["outcome"]] for r in old.values()),
        "mean_match_score_difference": statistics.mean(blocks),
        "seed_block_score_differences": dict(zip(map(str, seeds), blocks)),
        "bootstrap_95_percentile_interval": [boot[249], boot[9749]],
        "bootstrap_resamples": 10000,
        "by_opponent": {
            o["id"]: {
                "candidate_match_score": statistics.mean(
                    SCORES[r["outcome"]] for k, r in rows.items() if k[2] == o["id"]
                ),
                "reference_match_score": statistics.mean(
                    SCORES[r["outcome"]] for k, r in old.items() if k[2] == o["id"]
                ),
            }
            for o in candidate["opponents"]
        },
        "interpretation": (
            "Paired common-pool comparison. The percentile interval resamples whole seeds, "
            "preserving seats and opponents. It describes this small internal pool, not "
            "leaderboard strength; unseen opponent classes and model-selection bias remain "
            "outside the interval."
        ),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = compare(args.candidate, args.reference)
    with args.output.open("x") as file:
        json.dump(report, file, indent=2)
        file.write("\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
