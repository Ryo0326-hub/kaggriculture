"""Join reconciled public replays, own runtime logs and exact source decisions."""

import argparse
import hashlib
import json
import runpy
from pathlib import Path

from scripts.benchmark_profiles import profile
from scripts.replay_timing import summarize


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify_source(replay_path, log_path, source):
    replay = json.loads(replay_path.read_text())
    episode = replay["info"]["EpisodeId"]
    if log_path.stem not in (f"{episode}-0", f"{episode}-1"):
        raise ValueError("Log filename must identify this episode and the own seat")
    seat = int(log_path.stem[-1])
    agent = runpy.run_path(str(source))["agent"]
    mismatches = []
    for state, (before, after) in enumerate(zip(replay["steps"], replay["steps"][1:])):
        if agent(before[seat]["observation"], replay["configuration"]) != after[seat]["action"]:
            mismatches.append(state)
    logs = json.loads(log_path.read_text())
    entries = [entry for turn in logs for entry in turn]
    decisions = len(replay["steps"]) - 1
    if len(logs) != decisions or len(entries) != decisions:
        raise ValueError("Runtime log does not contain one entry per recorded decision")
    if mismatches:
        raise ValueError(f"Source differs in {len(mismatches)} decisions; first: {mismatches[0]}")
    return {
        "episode_id": episode,
        "seat": seat,
        "source_sha256": digest(source),
        "replay_sha256": digest(replay_path),
        "log_sha256": digest(log_path),
        "decisions_matched": decisions,
        "max_server_seconds": max(e["duration"] for e in entries),
        "stderr_entries": sum(bool(e.get("stderr")) for e in entries),
        "statuses": replay["statuses"],
        "cash": replay["rewards"],
        "own_margin": replay["rewards"][seat] - replay["rewards"][1 - seat],
    }


def build(replays, logs, source, audit_directory):
    if len(replays) != len(logs) or len(set(replays)) != len(replays):
        raise ValueError("Provide one own log for each unique replay, in the same order")
    games = []
    for replay, log in zip(replays, logs):
        verification = verify_source(replay, log, source)
        episode = verification["episode_id"]
        audit = json.loads((audit_directory / f"analysis-{episode}.json").read_text())
        game_profile = profile(replay, audit_directory)
        timing = summarize(replay, audit_directory)
        # These are exact successful operations, not requested-action estimates.
        work = json.loads((audit_directory / f"work-{episode}.json").read_text())
        raw = json.loads(replay.read_text())
        own = verification["seat"]
        gaps = [
            state[own]["observation"]["farms"][own]["money"]
            - state[own]["observation"]["farms"][1 - own]["money"]
            for state in raw["steps"]
        ]
        tpd = raw["configuration"]["turnsPerDay"]
        final_start = (raw["configuration"]["episodeSteps"] - 2) // tpd * tpd
        closing_accounts = []
        for player in audit["players"]:
            final_events = [e for e in player["transactions"] if e["step"] >= final_start]
            sales = {}
            for event in final_events:
                if event["op"] == "SELL":
                    sales[event["item"]] = sales.get(event["item"], 0) + event["cash"]
            expenses = sum(e["cash"] for e in final_events if e["op"] != "SELL")
            closing_accounts.append(
                {
                    "seat": player["seat"],
                    "sales_cash": sales,
                    "expenses": expenses,
                    "net_cash": sum(sales.values()) - expenses,
                }
            )
        post_water = [0, 0]
        for event in work:
            if (
                event["changed"]
                and event["op"] == "FERTILIZE"
                and event.get("crop") == "STRAWBERRY"
            ):
                seat = event["seat"]
                x, y = event["position"]
                tile = raw["steps"][event["step"]][seat]["observation"]["farms"][seat]["tiles"][y][
                    x
                ]
                post_water[seat] += int(tile["watered_today"])
        games.append(
            {
                "verification": verification,
                "profile": game_profile,
                "timing": timing,
                "successful_strawberry_fertilizer_after_water": post_water,
                "cash_lead": {
                    "maximum": max(gaps),
                    "maximum_state": gaps.index(max(gaps)),
                    "last_positive_state": max(
                        (i for i, gap in enumerate(gaps) if gap > 0), default=None
                    ),
                    "final_day_opening_gap": gaps[final_start],
                    "final": gaps[-1],
                },
                "final_day_accounts": closing_accounts,
                "executed_accounts": [
                    {
                        key: value
                        for key, value in player.items()
                        if key not in ("transactions", "daily", "final_carried", "installations")
                    }
                    for player in audit["players"]
                ],
            }
        )
    return {
        "interpretation": (
            "User-supplied public games, not a random ladder sample or validation self-play. "
            "Exact recorded-action resimulation is an accounting audit, not a counterfactual. "
            "Matching source actions supports identity in these states. "
            "Submission IDs are not read from these replay files."
        ),
        "source_sha256": digest(source),
        "reporter_sha256": digest(__file__),
        "games": games,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replays", nargs="+", type=Path, required=True)
    parser.add_argument("--logs", nargs="+", type=Path, required=True)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--audit-directory", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = build(args.replays, args.logs, args.source, args.audit_directory)
    with args.output.open("x") as file:
        json.dump(result, file, indent=2)
        file.write("\n")


if __name__ == "__main__":
    main()
