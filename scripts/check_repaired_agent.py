"""Check isolated recorded decisions and known forecast regressions; never advance a game."""

import argparse
import json
import runpy
from copy import deepcopy
from hashlib import sha256
from pathlib import Path
from time import perf_counter


def check(source, replays):
    start = perf_counter()
    loaded = runpy.run_path(str(source))
    name, policy = [(k, v) for k, v in loaded.items() if callable(v)][-1]
    startup = perf_counter() - start
    assert name == "agent", name
    scope = policy.__globals__
    rows, fertilizer, inputs = [], [], []
    for path in replays:
        replay = json.loads(path.read_text())
        inputs.append({"name": path.name, "sha256": sha256(path.read_bytes()).hexdigest()})
        cfg = replay["configuration"]
        for seat in (0, 1):
            for step in (0, 51, 147, 195, 336, 384, 483, 696, 718):
                obs = deepcopy(replay["steps"][step][seat]["observation"])
                obs["step"] = step  # Kaggle omits this shared field for seat 1.
                before = deepcopy(obs)
                start = perf_counter()
                action = policy(obs, cfg)
                elapsed = perf_counter() - start
                assert obs == before, "Observation mutated"
                assert len(action["hands"]) == len(obs["farms"][seat]["hands"])
                assert len(action["market"]) <= cfg["maxMarketOrdersPerTurn"]
                assert elapsed < cfg["actTimeout"]
                json.dumps(action)
                rows.append(
                    {
                        "replay": path.name,
                        "seat": seat,
                        "step": step,
                        "seconds": elapsed,
                        "market": action["market"],
                    }
                )
        if replay["info"]["EpisodeId"] != 107984963:
            continue
        # Passive comparisons against the SAME recorded transitions used by the
        # prior audit. Do not create states or apply any candidate actions.
        for step in range(23, 696, 24):
            before = replay["steps"][step][0]["observation"]
            after = replay["steps"][step + 1][0]["observation"]
            day = before["day"]
            for y, row in enumerate(before["farms"][0]["tiles"]):
                for x, tile in enumerate(row):
                    if (
                        not isinstance(tile, dict)
                        or tile.get("crop") != "TOMATO"
                        or not tile["watered_today"]
                        or tile["fertilized_until_day"] < day
                        or tile["yield_units"]
                    ):
                        continue
                    next_tile = after["farms"][0]["tiles"][y][x]
                    if not isinstance(next_tile, dict) or next_tile.get("yield_units", 0) <= 0:
                        continue
                    col = scope["crop_column"](
                        "TOMATO", tile["planted_day"], 29, tile=tile, today=day
                    )
                    expected, actual = col["outputs"].get(day + 1, 0), next_tile["yield_units"]
                    assert expected == actual
                    fertilizer.append(
                        {"step": step, "site": [x, y], "forecast": expected, "recorded": actual}
                    )
    return {
        "method": "Isolated recorded-observation decisions and passive forecast checks. "
        "No engine import, game advance, match or counterfactual episode.",
        "source_sha256": sha256(source.read_bytes()).hexdigest(),
        "entrypoint": name,
        "startup_seconds": startup,
        "decision_count": len(rows),
        "max_decision_seconds": max(row["seconds"] for row in rows),
        "inputs": inputs,
        "decisions": rows,
        "fertilizer_comparisons": fertilizer,
        "server_validation": "pending",
        "competitive_performance": "unmeasured",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("replays", nargs="+", type=Path)
    args = parser.parse_args()
    result = check(args.source, args.replays)
    with args.output.open("x") as file:
        file.write(json.dumps(result, indent=2) + "\n")
    print(
        json.dumps(
            {
                k: v
                for k, v in result.items()
                if k not in ("inputs", "decisions", "fertilizer_comparisons")
            },
            indent=2,
        )
    )
    print("Fertilizer comparisons:", len(result["fertilizer_comparisons"]))


if __name__ == "__main__":
    main()
