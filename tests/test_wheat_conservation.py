"""The standalone accounting fix has no waiting, growth stress or future-shop policy."""

import ast
import runpy
from hashlib import sha256
from pathlib import Path

import pytest
from kaggle_environments import make
from kaggle_environments.envs.kaggriculture import kaggriculture as engine

from baselines import cycle_3
from scripts.make_wheat_conservation_control import build


@pytest.fixture
def conservation(tmp_path):
    output = tmp_path / "main.py"
    build(cycle_3.__file__, output)
    return runpy.run_path(str(output))


@pytest.mark.parametrize("wheat,herd,day", [(6, 3, 4), (2, 3, 4), (0, 3, 4), (6, 0, 4), (6, 3, 29)])
def test_feed_and_market_sales_conserve_wheat(conservation, wheat, herd, day):
    env = make("kaggriculture", configuration={"seed": 17})
    obs = env.state[0].observation
    obs.update(day=day, hour=0, step=day * 24)
    for side, quantity in ((0, 6), (1, wheat)):
        tile = engine._new_plant("WHEAT", day - 4, 24)
        tile.update(yield_units=quantity, watered_today=True)
        obs.farms[side]["tiles"][0][0] = tile
    for x in range(herd):
        obs.farms[1]["tiles"][1][x] = engine._new_animal("COW", 0)
    fn = conservation["production_projection"]
    ordinary = cycle_3.production_projection(obs, env.configuration, cycle_3.MARKET)
    assert fn(obs, env.configuration, cycle_3.MARKET) == ordinary
    corrected = fn(obs, env.configuration, cycle_3.MARKET, net_rival_wheat=True)
    feed = herd if day < 29 else 0
    inventory = obs.market["inventory"]["WHEAT"] - 1 - max(0, feed - wheat)
    expected = 0.8 * cycle_3.batch_revenue(
        "WHEAT", inventory + max(0, wheat - feed) / 2, 6, cycle_3.MARKET
    )
    assert corrected["daily"][0]["credited_receipts"] == expected
    if not wheat or not herd or day == 29:
        assert corrected == ordinary


def test_only_expansion_forecast_changes_and_no_rival_wheat_means_same_decision(tmp_path):
    output = tmp_path / "main.py"
    build(cycle_3.__file__, output)
    assert sha256(output.read_bytes()).hexdigest() == (
        "232a0293ed5a52beadbf313ef7669161858cbe12e2759d89a3c9f57897af367b"
    )
    policy = runpy.run_path(str(output))

    def functions(code):
        return {n.name: ast.dump(n) for n in ast.parse(code).body if isinstance(n, ast.FunctionDef)}

    old, new = functions(Path(cycle_3.__file__).read_text()), functions(output.read_text())
    assert new.keys() == old.keys()
    assert {n for n in old if old[n] != new[n]} == {"production_projection", "expansion_investment"}
    env = make("kaggriculture", configuration={"seed": 17})
    obs = env.state[0].observation
    obs.update(day=3, hour=0, step=72)
    obs.farms[0]["money"] = 30000
    assert policy["expansion_turn"](obs, env.configuration) == cycle_3.expansion_turn(
        obs, env.configuration
    )
    with pytest.raises(FileExistsError):
        build(cycle_3.__file__, output)
