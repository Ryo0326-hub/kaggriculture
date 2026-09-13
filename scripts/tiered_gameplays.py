"""Archive and inspect nine user-supplied recordings without running a game.

Only JSON data is read. Embedded descriptions/specifications are never executed
or treated as instructions. Selection uses observed conditions, not candidate
actions or measured candidate profits. Rank groups are user-provided labels.
"""

import argparse
import base64
import copy
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BATCH = "2026-09-12"
GROUPS = {
    "top": (108377045, 108377042, 108359085),
    "mid": (108380097, 108375914, 108371392),
    "bottom": (108378358, 108365679, 108364290),
}
ARCHIVES = ROOT / "docs/gameplays" / BATCH
RAW_COPIES = ROOT / "replays/user-tiered" / BATCH
FIXTURE = ROOT / "docs/examples/tiered-gameplay-observations.json"
MANIFEST = ARCHIVES / "manifest.json"
MAX_SOURCE_BYTES = 40_000_000
FIRST = {"WHEAT": 2, "CARROT": 2, "MELON": 10, "TOMATO": 8, "STRAWBERRY": 10}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def save_once(path, raw):
    """Generated data/archive output, never overwrite differing prior bytes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        if path.read_bytes() != raw:
            raise FileExistsError(f"Refusing to overwrite {path}")
        return
    with path.open("xb") as stream:
        stream.write(raw)


def read_game(raw, episode):
    if len(raw) > MAX_SOURCE_BYTES:
        raise ValueError("Recording exceeds the 40 MB input bound")
    game = json.loads(raw)
    if game.get("info", {}).get("EpisodeId") != episode:
        raise ValueError("Recording identity does not match its requested filename")
    if game.get("module_version") != "1.32.7":
        raise ValueError("Review mechanics before importing a different module version")
    if len(game.get("steps", [])) != 720 or game["configuration"]["episodeSteps"] != 720:
        raise ValueError("Expected a complete 720-state recording")
    for index, row in enumerate(game["steps"]):
        if len(row) != 2:
            raise ValueError("Expected two player observations")
        for seat, state in enumerate(row):
            obs = state["observation"]
            if obs["player"] != seat or obs["day"] * 24 + obs["hour"] != index:
                raise ValueError("Player or observation clock mismatch")
    if any(state["status"] != "DONE" for state in game["steps"][-1]):
        raise ValueError("Only completed recordings may be archived by this importer")
    return game


def condition_scores(obs):
    farm, private = obs["farms"][obs["player"]], obs["private"]
    cells = [t for row in farm["tiles"] for t in row if isinstance(t, dict)]
    animals = [t for t in cells if t.get("animal")]
    plants = [t for t in cells if t.get("crop")]
    step = obs["day"] * 24 + obs["hour"]
    decay = sum(
        t.get("yield_units", 0) > 0
        and obs["day"] - t["planted_day"] >= FIRST[t["crop"]]
        and 0 <= t.get("max_lifespan_step", -1) <= step + 4
        for t in plants
    )
    urgent = sum(t.get("consecutive_unfed", 0) >= 1 and not t["fed_today"] for t in animals)
    shed = sum(private["shed"].values())
    carried = sum(sum(inv.values()) for inv in private["inventories"])
    return {
        "peak-crew": len(farm["hands"]) + 1,
        "peak-storage": shed + carried,
        "decay-pressure": decay,
        # Final-day neglect is not a survival obligation: scoring ends before
        # another productive day. Terminal snapshots cover that distinct case.
        "late-feed-risk": urgent if obs["hour"] >= 20 and obs["day"] < 29 else 0,
        "price-floor": sum(p == 1 for p in obs["market"]["prices"].values()),
        "duplicate-demand": max(Counter(obs["town"]["unlocked_shops"]).values(), default=0),
        "shed_units": shed,
        "carried_units": carried,
        "animals": len(animals),
        "crops": len(plants),
    }


def unit_bundle(action, previous_obs):
    """Compare recorded worker commands, padding omitted hand commands with PASS."""
    action = action or {}
    farm = previous_obs["farms"][previous_obs["player"]]
    hands = list(action.get("hands", []))
    hands.extend([["PASS"] for _ in range(max(0, len(farm["hands"]) - len(hands)))])
    return [action.get("farmer", ["PASS"]), *hands[: len(farm["hands"])]]


def similarity(game):
    exact, units, markets, active_pairs, active_units = 0, 0, 0, 0, 0
    for i, row in enumerate(game["steps"][1:], 1):
        actions = [s["action"] for s in row]
        bundles = [unit_bundle(actions[s], game["steps"][i - 1][s]["observation"]) for s in (0, 1)]
        exact += actions[0] == actions[1]
        units += bundles[0] == bundles[1]
        markets += actions[0].get("market", []) == actions[1].get("market", [])
        active = any(cmd != ["PASS"] for bundle in bundles for cmd in bundle)
        if active:
            active_pairs += 1
            active_units += bundles[0] == bundles[1]
    return {
        "decisions": 719,
        "exact_action_dict_matches": exact,
        "worker_bundle_matches": units,
        "market_list_matches": markets,
        "active_worker_pair_decisions": active_pairs,
        "active_worker_bundle_matches": active_units,
        "same_algorithm_proven": False,
        "alignment": "row i action produced row i observation from row i-1 observation",
    }


def extract_game(game, episode, tier, source_hash):
    cases, histories, seats = [], [], []
    for seat in (0, 1):
        observations = [row[seat]["observation"] for row in game["steps"][:-1]]
        scores = [condition_scores(o) for o in observations]
        selected = {0: ["opening"], 718: ["final-action"]}
        witnesses = {}
        for label in (
            "peak-crew",
            "peak-storage",
            "decay-pressure",
            "late-feed-risk",
            "price-floor",
            "duplicate-demand",
        ):
            index = max(range(719), key=lambda i: scores[i][label])
            # Do not invent floor events or duplicate shops in a recording lacking them.
            if scores[index][label] < (2 if label == "duplicate-demand" else 1):
                witnesses[label] = None
                continue
            selected.setdefault(index, []).append(label)
            witnesses[label] = {"state_index": index, "value": scores[index][label]}
        for index, labels in sorted(selected.items()):
            obs = observations[index]
            cases.append(
                {
                    "id": f"{tier}-{episode}-seat{seat}-state{index}",
                    "episode": episode,
                    "tier": tier,
                    "seat": seat,
                    "state_index": index,
                    "conditions": labels,
                    "source_sha256": source_hash,
                    "observation_sha256": digest(canonical(obs)),
                    "observation": copy.deepcopy(obs),
                }
            )
        storage_index = witnesses["peak-storage"]["state_index"]
        boundary = min(696, (storage_index // 24 + 1) * 24)
        for label, start in (("dawn-rehire", boundary - 1), ("terminal-delivery", 715)):
            histories.append(
                {
                    "id": f"{tier}-{episode}-seat{seat}-{label}",
                    "episode": episode,
                    "tier": tier,
                    "seat": seat,
                    "kind": label,
                    "state_indices": list(range(start, start + 4)),
                    "observations": copy.deepcopy(observations[start : start + 4]),
                }
            )
        seats.append(
            {
                "seat": seat,
                "name": game["info"]["TeamNames"][seat],
                "final_cash": game["steps"][-1][seat]["reward"],
                "selected_witnesses": witnesses,
                "final_shops": dict(
                    Counter(game["steps"][-1][seat]["observation"]["town"]["unlocked_shops"])
                ),
            }
        )
    return cases, histories, seats


def import_recordings(source_directory):
    manifest = {
        "batch": BATCH,
        "tier_provenance": (
            "User labels: first three top; next three mid (about 2600); last three bottom "
            "(1000s). Not independently verified rankings."
        ),
        "method": (
            "Read-only inspection of completed observations and recorded action lists; "
            "no engine, no candidate actions applied."
        ),
        "games": [],
    }
    fixture = {"configuration_by_episode": {}, "cases": [], "histories": []}
    for tier, episodes in GROUPS.items():
        for episode in episodes:
            source = source_directory / f"{episode}.json"
            if source.stat().st_size > MAX_SOURCE_BYTES:
                raise ValueError("Recording exceeds the 40 MB input bound")
            raw = source.read_bytes()
            game = read_game(raw, episode)
            compressed = gzip.compress(raw, compresslevel=9, mtime=0)
            raw_path, archive = (
                RAW_COPIES / tier / source.name,
                ARCHIVES / tier / (source.name + ".gz"),
            )
            save_once(raw_path, raw)
            save_once(archive, compressed)
            assert raw_path.read_bytes() == gzip.decompress(archive.read_bytes()) == raw
            cases, histories, seats = extract_game(game, episode, tier, digest(raw))
            fixture["cases"].extend(cases)
            fixture["histories"].extend(histories)
            fixture["configuration_by_episode"][str(episode)] = game["configuration"]
            manifest["games"].append(
                {
                    "episode": episode,
                    "tier": tier,
                    "module_version": game["module_version"],
                    "raw_path": str(raw_path.relative_to(ROOT)),
                    "archive_path": str(archive.relative_to(ROOT)),
                    "raw_bytes": len(raw),
                    "archive_bytes": len(compressed),
                    "raw_sha256": digest(raw),
                    "archive_sha256": digest(compressed),
                    "states": len(game["steps"]),
                    "seats": seats,
                    "action_similarity": similarity(game),
                    "selected_snapshots": len(cases),
                }
            )
    expanded = canonical(fixture)
    envelope = {
        "encoding": "gzip+base64",
        "expanded_sha256": digest(expanded),
        "payload": base64.b64encode(gzip.compress(expanded, mtime=0)).decode(),
    }
    manifest["fixture"] = {
        "path": str(FIXTURE.relative_to(ROOT)),
        "expanded_sha256": digest(expanded),
        "snapshots": len(fixture["cases"]),
        "histories": len(fixture["histories"]),
        "observations_per_history": 4,
        "conditions": dict(Counter(tag for case in fixture["cases"] for tag in case["conditions"])),
    }
    save_once(FIXTURE, (json.dumps(envelope, indent=2) + "\n").encode())
    save_once(MANIFEST, (json.dumps(manifest, indent=2) + "\n").encode())
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-directory", type=Path, required=True)
    args = parser.parse_args()
    result = import_recordings(args.source_directory)
    print(json.dumps({"games": len(result["games"]), "fixture": result["fixture"]}, indent=2))
