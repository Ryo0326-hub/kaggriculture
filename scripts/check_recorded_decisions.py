"""Check isolated decisions on recorded observations; never advance a game."""

import argparse
import hashlib
import json
import runpy
from copy import deepcopy
from pathlib import Path
from time import perf_counter


def check(source, replays):
    policy = runpy.run_path(str(source))["agent"]
    rows = []
    for path in replays:
        replay = json.loads(path.read_text())
        seat = next(
            i
            for i, name in enumerate(replay["info"]["TeamNames"])
            if name in ("Majkel1337", "Gekkotron")
        )
        # Fixed coverage points, not a performance score or an opponent evaluation.
        for index in (0, 51, 147, 195, 291, 483, 696, 718):
            obs = deepcopy(replay["steps"][index][seat]["observation"])
            obs["step"] = index  # shared field omitted from seat 1's replay JSON
            before = deepcopy(obs)
            start = perf_counter()
            action = policy(obs, replay["configuration"])
            elapsed = perf_counter() - start
            assert before == obs, "Observation mutated"
            assert len(action["hands"]) == len(obs["farms"][seat]["hands"])
            assert len(action["market"]) <= replay["configuration"]["maxMarketOrdersPerTurn"]
            assert elapsed < replay["configuration"]["actTimeout"], "Decision exceeded actTimeout"
            json.dumps(action)
            rows.append(
                {"episode": replay["info"]["EpisodeId"], "state": index, "seconds": elapsed}
            )
    return {
        "method": "isolated inference on recorded observations; no state advances or matches",
        "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
        "decisions": len(rows),
        "max_seconds": max(r["seconds"] for r in rows),
        "results": rows,
        "server_validation": "pending",
        "competitive_rating": "unmeasured",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("replays", type=Path, nargs="+")
    args = parser.parse_args()
    result = check(args.source, args.replays)
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "results"}, indent=2))


if __name__ == "__main__":
    main()
