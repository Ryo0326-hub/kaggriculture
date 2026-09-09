import json
from copy import deepcopy

import pytest
from kaggle_environments import make

from evaluate import ROOT, run_match, summarize
from main import agent


@pytest.fixture(scope="module")
def full_games():
    artifact = str(ROOT / "main.py")
    return [
        run_match(artifact, "starter", 11, 0),
        run_match(artifact, "starter", 11, 1),
        run_match(artifact, "starter", 11, 0),
        run_match(artifact, artifact, 29, 0),
    ]


def test_full_season_artifact_validity_and_liquidation(full_games):
    for row, env in full_games:
        assert row["outcome"] != "error"
        assert row["resolved_seed"] == row["seed"]
        assert row["recorded_states"] == 720
        assert row["last_action_step"] == 718
        assert row["unsold_shed_units"] == 0
        assert row["unsold_carried_units"] == 0
        assert row["unused_seeds"] == 0
        assert row["candidate_cash"] > 3_000
        assert all(not log.get("stderr") for turn in env.logs for log in turn)
        # Route/maintenance sanity: every non-PASS crop action changes its intended state.
        for before, after in zip(env.steps, env.steps[1:]):
            seat = row["seat"]
            action = after[seat].action["farmer"][0]
            old = before[seat].observation
            new = after[seat].observation
            x, y = old.farms[seat]["farmer"]
            if action in ("PLANT", "WATER", "HARVEST", "DIG"):
                assert old.farms[seat]["tiles"][y][x] != new.farms[seat]["tiles"][y][x]


def test_seed_and_seat_reproducibility(full_games):
    first, other_seat, repeat, mirror = [row for row, _ in full_games]
    assert first["candidate_cash"] == other_seat["candidate_cash"] == repeat["candidate_cash"]
    assert first["opponent_cash"] == other_seat["opponent_cash"] == repeat["opponent_cash"]
    assert first["farmer_actions"] == repeat["farmer_actions"]
    assert first["outcome"] == other_seat["outcome"] == "win"
    assert mirror["outcome"] == "draw"
    for states_a, states_b in zip(full_games[0][1].steps, full_games[2][1].steps):
        assert states_a[0].action == states_b[0].action
        assert states_a[0].observation.farms == states_b[0].observation.farms
        assert states_a[0].observation.market == states_b[0].observation.market


def test_agent_does_not_mutate_observation():
    env = make("kaggriculture", configuration={"seed": 5})
    obs = env.state[0].observation
    before = deepcopy(obs)
    result = agent(obs, env.configuration)
    json.dumps(result, allow_nan=False)
    assert obs == before


def test_short_horizon_avoids_unrecoverable_seed_spending():
    env = make("kaggriculture", configuration={"seed": 5, "episodeSteps": 24})
    env.run([str(ROOT / "main.py"), "pass"])
    assert env.state[0].reward == 3_000
    assert sum(env.state[0].observation.private["seeds"].values()) == 0


def test_crashing_opponent_is_an_error_not_a_win(tmp_path):
    bad = tmp_path / "broken.py"
    bad.write_text('def agent(obs):\n    raise RuntimeError("deliberate test failure")\n')
    row, _ = run_match(str(ROOT / "main.py"), str(bad), 5, 0, episode_steps=4)
    assert row["outcome"] == "error"
    assert row["failures"]
    assert summarize([row])["match_score"] is None
