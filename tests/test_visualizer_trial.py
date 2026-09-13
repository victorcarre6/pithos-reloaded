"""Le banc exerce la chaîne réelle sur disque, en nommant ses deux substitutions."""

import json
from pathlib import Path
import subprocess
import sys

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "experiments" / "visualizer" / "run.py"


@pytest.mark.parametrize("case,cause", [
    ("green", None),
    ("rejected", "invariant_failed"),
    ("receipt_refused", "receipt_not_written"),
])
def test_trial_cli_measures_green_and_rollbacks(case, cause):
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "selftest", "--case", case],
        capture_output=True,
        text=True,
        timeout=45,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    output = Path(report["evidence_directory"])
    assert json.loads((output / "result.json").read_text()) == report
    assert report["cause"] == cause
    assert report["components"]["bridge"] == "scripted"
    assert report["components"]["git"] == "simulated"
    assert report["components"]["verifier"] == "real"

    # le code et les reçus sont relus indépendamment du résumé du banc
    seed = (SCRIPT.parent / "seed" / "audio_visualizer.py").read_bytes()
    actual = (output / "workspace" / "audio_visualizer.py").read_bytes()
    events = [json.loads(line) for line in (output / "events.jsonl").read_text().splitlines()]
    receipts = [event for event in events if event["type"] == "validation"]
    gates = [json.loads(path.read_text()) for path in output.glob("invariant-*/result.json")]
    if case == "green":
        assert actual != seed
        assert len(receipts) == 1
        assert report["status"] == "passed"
    else:
        assert actual == seed
        assert receipts == []
        assert report["status"] == "blocked"
    if case != "rejected":
        checks = sorted(gate["check"] for gate in gates)
        assert checks == ["failed", "failed", "passed"]


@pytest.mark.parametrize("dedicated", [False, True])
def test_trial_refuses_harness_or_uninitialized_target(tmp_path, dedicated):
    repo = tmp_path if dedicated else ROOT
    completed = subprocess.run(
        [sys.executable, str(SCRIPT), "trial", "--repo", str(repo)],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 1
    report = json.loads(completed.stdout)
    assert report["error"] == "ValueError"
    assert "dedicated initialized Git repository" in report["detail"]
    output = Path(report["evidence_directory"])
    assert not (output / "events.jsonl").exists()
