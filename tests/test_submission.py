import hashlib

import pytest

from evaluate import ROOT, run_match
from prepare_submission import prepare
from scripts.make_greedy_ablation import build


def test_isolated_artifact_full_season(tmp_path):
    output = tmp_path / "release"
    report = prepare(ROOT / "main.py", output)
    assert report["passed"]
    assert report["recorded_states"] == 720
    assert report["statuses"] == ["DONE", "DONE"]
    assert report["unsold_carried_units"] == report["unsold_shed_units"] == [0, 0]
    assert (output / "main.py").read_bytes() == (ROOT / "main.py").read_bytes()
    assert report["sha256"] == hashlib.sha256((ROOT / "main.py").read_bytes()).hexdigest()
    assert sorted(p.name for p in output.iterdir()) == [
        "main.py",
        "validation.json",
        "validation.log",
    ]
    with pytest.raises(FileExistsError):
        prepare(ROOT / "main.py", output)


def test_repository_import_is_not_available_in_isolated_release(tmp_path):
    bad = tmp_path / "bad.py"
    bad.write_text("import evaluate\ndef agent(obs):\n    return {}\n")
    with pytest.raises(RuntimeError, match="failed validation"):
        prepare(bad, tmp_path / "invalid-release")


def test_greedy_control_uses_the_correct_loader_entry_point(tmp_path):
    control = tmp_path / "greedy.py"
    build(ROOT / "baselines/step_2.py", control)
    row, _ = run_match(str(control), "pass", 5, 0, episode_steps=4)
    assert row["outcome"] != "error"
