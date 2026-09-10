import json

import pytest

from compare_results import compare


def write_run(path, outcomes):
    path.mkdir()
    manifest = {k: {} for k in ["environment", "configuration", "candidate"]}
    manifest.update(
        runner_sha256="runner",
        lock_sha256="lock",
        seeds=[1, 2],
        seats=[0, 1],
        opponents=[{"id": "rival"}],
        episode_steps=720,
    )
    (path / "manifest.json").write_text(json.dumps(manifest))
    rows = [
        {"seed": seed, "seat": seat, "opponent": "rival", "outcome": outcome}
        for (seed, seat), outcome in zip([(1, 0), (1, 1), (2, 0), (2, 1)], outcomes)
    ]
    (path / "matches.jsonl").write_text("\n".join(map(json.dumps, rows)))


def test_comparison_keeps_correlated_seats_in_seed_blocks(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    write_run(a, ["win", "win", "loss", "loss"])
    write_run(b, ["draw"] * 4)
    result = compare(a, b)
    assert result["seed_block_score_differences"] == {"1": 0.5, "2": -0.5}
    assert result["mean_match_score_difference"] == 0
    assert result["bootstrap_95_percentile_interval"] == [-0.5, 0.5]


def test_comparison_rejects_missing_duplicate_and_failed_games(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    write_run(a, ["win"] * 4)
    write_run(b, ["loss"] * 4)
    path = a / "matches.jsonl"
    original = path.read_text()
    lines = original.splitlines()
    for invalid in [lines[:-1], lines + [lines[0]]]:
        path.write_text("\n".join(invalid))
        with pytest.raises(ValueError, match="incomplete|duplicate"):
            compare(a, b)
    path.write_text(original.replace('"win"', '"error"', 1))
    with pytest.raises(ValueError, match="agent errors"):
        compare(a, b)
    path.write_text(original)
    manifest_path = b / "manifest.json"
    manifest = json.loads(manifest_path.read_text())
    manifest["configuration"] = {"startingMoney": 99999}
    manifest_path.write_text(json.dumps(manifest))
    with pytest.raises(ValueError, match="configuration"):
        compare(a, b)
