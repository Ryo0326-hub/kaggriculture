"""Explain a recorded candidate decision using the matching current source."""

import argparse
import json
from pathlib import Path

from evaluate import ROOT, sha256
from main import expansion_turn as plan_turn


def explain_replay(path, state_index, player):
    path = Path(path)
    replay = json.loads(path.read_text())
    manifest = json.loads((path.parent / "manifest.json").read_text())
    digest = sha256(ROOT / "main.py")
    if manifest["candidate"].get("sha256") != digest:
        raise ValueError("Replay candidate differs from current main.py; use matching source")
    if player not in (0, 1) or not 0 <= state_index < len(replay["steps"]) - 1:
        raise ValueError("Choose player 0 or 1 and a nonterminal replay state")
    states = replay["steps"][state_index]
    observation = dict(states[player]["observation"])
    observation["step"] = states[0]["observation"]["step"]
    action, explanation = plan_turn(observation, replay["configuration"])
    if action != replay["steps"][state_index + 1][player]["action"]:
        raise ValueError("Recomputed action differs; choose the candidate seat and matching source")
    previous = None
    for option in explanation.get("economics", {}).get("alternatives", []):
        if previous is not None:
            option["marginal_operating_value"] = (
                option["model_value"]
                + option["hire_cost"]
                - previous["model_value"]
                - previous["hire_cost"]
            )
            option["marginal_hire_cost"] = option["hire_cost"] - previous["hire_cost"]
            option["marginal_net_value"] = option["model_value"] - previous["model_value"]
        previous = option
    return {
        "source_sha256": digest,
        "seed": replay["info"]["seed"],
        "player": player,
        "state_index": state_index,
        "day": observation["day"],
        "hour": observation["hour"],
        "recorded_action_matches": True,
        "action": action,
        "explanation": explanation,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--replay", type=Path, required=True)
    parser.add_argument("--state", type=int, required=True)
    parser.add_argument("--player", type=int, choices=[0, 1], default=0)
    args = parser.parse_args()
    print(json.dumps(explain_replay(args.replay, args.state, args.player), indent=2))


if __name__ == "__main__":
    main()
