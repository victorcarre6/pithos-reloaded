"""Entrée unique, suivi des preuves et interruption transactionnelle."""

import argparse
import fcntl
import io
import json
import os
from pathlib import Path
import pty
import select
import signal
import struct
import subprocess
import sys
import termios
import time

import pytest

from experiments.visualizer import run
from tui import Dashboard, frame, snapshot


ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("case,cause", [
    ("green", None),
    ("rejected", "invariant_failed"),
    ("receipt_refused", "receipt_not_written"),
])
def test_main_preserves_reports_and_exit_codes(case, cause):
    completed = subprocess.run(
        [sys.executable, str(ROOT / "src/main.py"), "selftest", "--case", case],
        capture_output=True,
        text=True,
        timeout=45,
    )
    assert completed.returncode == 0, completed.stderr
    assert "\x1b" not in completed.stdout
    report = json.loads(completed.stdout)
    assert report["cause"] == cause
    assert report["checks_passed"] is True
    output = Path(report["evidence_directory"])
    assert json.loads((output / "result.json").read_text()) == report
    seed = run.SEED.read_bytes()
    target = (output / "workspace/audio_visualizer.py").read_bytes()
    assert (target == seed) == (case != "green")


@pytest.mark.parametrize("arguments", [
    ["--no-tui", "selftest"],
    ["selftest", "--no-tui"],
    ["probe", "--no-tui"],
    ["trial", "--repo", ".", "--seconds", "12", "--no-tui"],
])
def test_no_tui_option_works_before_or_after_command(arguments):
    args = run.build_parser().parse_args(arguments)
    assert args.no_tui is True


def test_main_refuses_invalid_trial_before_inference(tmp_path):
    completed = subprocess.run(
        [sys.executable, str(ROOT / "src/main.py"), "trial", "--repo", str(tmp_path)],
        capture_output=True,
        text=True,
        timeout=10,
    )
    assert completed.returncode == 1
    report = json.loads(completed.stdout)
    assert report["error"] == "ValueError"
    assert not (Path(report["evidence_directory"]) / "events.jsonl").exists()


def test_interruption_restores_modified_target_and_writes_report(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(run, "HERE", tmp_path)

    def interrupt(*args, **kwargs):
        targets = list(tmp_path.glob("runs/selftest-*/workspace/audio_visualizer.py"))
        assert targets[0].read_bytes() != run.SEED.read_bytes()
        raise KeyboardInterrupt

    monkeypatch.setattr(run.verifier, "run", interrupt)
    assert run.main(["selftest"]) == 130
    report = json.loads(capsys.readouterr().out)
    assert report["status"] == "interrupted"
    output = Path(report["evidence_directory"])
    assert (output / "workspace/audio_visualizer.py").read_bytes() == run.SEED.read_bytes()
    assert json.loads((output / "result.json").read_text()) == report


def test_snapshot_counts_transport_once_and_shows_real_tool_activity(tmp_path):
    usage = {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120}
    payloads = [
        {"scope": "engine", "operation": "running", "node_id": "clamp-level"},
        {"endpoint": "http://localhost/v1/chat/completions", "model": "local", "outcome": "completed", "usage": usage},
        {"scope": "engine", "operation": "candidate_response", "outcome": "completed", "usage": usage},
        {"operation": "splice", "function_name": "clamp_level"},
    ]
    events = []
    for index, payload in enumerate(payloads):
        kind = "tool_activity" if index == 3 else "status"
        events.append({"event_id": index + 1, "type": kind, "payload": payload})
    lines = [json.dumps(event) for event in events]
    (tmp_path / "events.jsonl").write_text("\n".join(lines) + '\n{"partial":')
    state = snapshot(tmp_path, "trial")
    assert state["calls"] == 1
    assert state["tokens"] == {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120}
    assert state["turns_started"] == state["turns_done"] == 1
    assert state["tools"] == 1
    assert "splice" in state["recent"][-1]
    assert "fragment" in state["notice"]


def test_missing_usage_is_not_reported_as_zero(tmp_path):
    event = {"type": "status", "payload": {"endpoint": "local", "outcome": "transport_error", "usage": {}}}
    (tmp_path / "events.jsonl").write_text(json.dumps(event) + "\n")
    state = snapshot(tmp_path, "probe")
    assert state["tokens"]["total_tokens"] is None
    assert state["calls"] == 1


@pytest.mark.parametrize("width,height", [(120, 32), (80, 24), (40, 10), (1, 1)])
def test_frame_fits_terminal_and_removes_control_sequences(tmp_path, width, height):
    args = argparse.Namespace(mode="selftest", case="green")
    state = snapshot(tmp_path, args.mode)
    state["recent"] = ["splice\x1b[2J\nmalicious"]
    lines = frame(args, tmp_path, state, 1.5, width, height)
    assert len(lines) == height
    assert all(len(line) <= width for line in lines)
    assert "\x1b" not in "".join(lines)
    if width >= 80:
        display = "\n".join(lines)
        for title in ("Projet", "Inférence", "Travail actuel", "Activité récente"):
            assert title in display


def test_terminal_restores_cursor_on_failure(tmp_path, monkeypatch):
    stream = io.StringIO()
    args = argparse.Namespace(mode="selftest", case="green")
    dashboard = Dashboard(args, tmp_path, stream=stream)
    monkeypatch.setattr(dashboard, "enabled", True)
    with pytest.raises(RuntimeError, match="injected"):
        with dashboard:
            raise RuntimeError("injected")
    output = stream.getvalue()
    assert "\x1b[?1049h" in output
    assert output.endswith("\x1b[?25h\x1b[?1049l")
    assert not dashboard.thread.is_alive()


def test_terminal_keeps_usage_received_between_frames(tmp_path, monkeypatch, capsys):
    stream = io.StringIO()
    args = argparse.Namespace(mode="probe")
    dashboard = Dashboard(args, tmp_path, stream=stream)
    monkeypatch.setattr(dashboard, "enabled", True)
    dashboard.stop.set()
    with dashboard:
        event = {"type": "status", "payload": {"endpoint": "local", "usage": {"total_tokens": 120}}}
        (tmp_path / "events.jsonl").write_text(json.dumps(event) + "\n")
        (tmp_path / "result.json").write_text('{"mode": "probe", "usable": true}')
    assert "Tokens total : 120" in stream.getvalue()
    assert "tokens : 120" in capsys.readouterr().err
    assert stream.getvalue().endswith("\x1b[?25h\x1b[?1049l")


def test_real_terminal_sigint_restores_target_and_screen(tmp_path):
    # le vrai signal arrive après le splice, pendant une vérification retenue
    code = (
        "import sys, time\n"
        "from pathlib import Path\n"
        "from src.main import main\n"
        "from experiments.visualizer import run\n"
        "run.HERE = Path(sys.argv[1])\n"
        "def hold(*args, **kwargs):\n"
        "    (run.HERE / 'ready').touch()\n"
        "    time.sleep(30)\n"
        "run.verifier.run = hold\n"
        "raise SystemExit(main(['selftest']))\n"
    )
    master, slave = pty.openpty()
    size = struct.pack("HHHH", 28, 120, 0, 0)
    fcntl.ioctl(slave, termios.TIOCSWINSZ, size)
    environment = dict(os.environ, TERM="xterm-256color", PYTHONDONTWRITEBYTECODE="1")
    process = subprocess.Popen(
        [sys.executable, "-c", code, str(tmp_path)],
        cwd=ROOT,
        env=environment,
        stdin=slave,
        stdout=slave,
        stderr=slave,
    )
    os.close(slave)
    chunks = []
    interrupted = False
    deadline = time.monotonic() + 15
    try:
        while time.monotonic() < deadline:
            readable, _, _ = select.select([master], [], [], 0.1)
            if readable:
                try:
                    chunk = os.read(master, 65536)
                except OSError:
                    break
                if not chunk:
                    break
                chunks.append(chunk)
            transcript = b"".join(chunks)
            if b"splice" in transcript and (tmp_path / "ready").exists() and not interrupted:
                process.send_signal(signal.SIGINT)
                interrupted = True
        process.wait(timeout=5)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        os.close(master)

    # effets réels : panneau rafraîchi, octets restaurés, rapport durable, curseur rendu
    transcript = b"".join(chunks).decode()
    assert interrupted, transcript
    assert process.returncode == 130, transcript
    assert "Activité récente" in transcript
    assert transcript.count("\x1b[H") >= 2
    assert "\x1b[?25h\x1b[?1049l" in transcript
    reports = list(tmp_path.glob("runs/selftest-*/result.json"))
    report = json.loads(reports[0].read_text())
    assert report["status"] == "interrupted"
    target = reports[0].parent / "workspace/audio_visualizer.py"
    assert target.read_bytes() == run.SEED.read_bytes()
