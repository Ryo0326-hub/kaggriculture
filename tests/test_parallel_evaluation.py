import json
from concurrent.futures import ProcessPoolExecutor

from evaluate import ROOT, run_job


def test_parallel_jobs_preserve_order_actions_and_economic_results():
    jobs = [
        (str(ROOT / "main.py"), "pass", seed, seat, True, 16) for seed, seat in [(5, 0), (7, 1)]
    ]
    serial = list(map(run_job, jobs))
    with ProcessPoolExecutor(max_workers=2) as pool:
        parallel = list(pool.map(run_job, jobs))
    for (row, config, replay, _), (other, other_config, other_replay, _) in zip(serial, parallel):
        for key in ["seed", "seat", "outcome", "candidate_cash", "opponent_cash", "economics"]:
            assert row[key] == other[key]
        assert config == other_config
        first, second = json.loads(replay), json.loads(other_replay)
        assert [s[row["seat"]]["action"] for s in first["steps"]] == [
            s[row["seat"]]["action"] for s in second["steps"]
        ]


def test_successful_job_omits_unrequested_large_outputs():
    row, _, replay, logs = run_job(("pass", "pass", 5, 0, False, 4))
    assert row["outcome"] == "draw"
    assert replay is logs is None
