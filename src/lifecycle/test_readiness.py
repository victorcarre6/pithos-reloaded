"""Un processus lancé ou une probe bloquée ne constituent pas une readiness."""

import time

import pytest

from lifecycle.custody import Readiness, wait_ready


def test_observed_readiness(tmp_path):
    observed = tmp_path / "probe"

    def probe():
        observed.write_text("observed")

        return True

    result = wait_ready(probe, time.monotonic() + 1)
    assert result == Readiness.ready
    assert observed.read_text() == "observed"


def test_no_response_is_timeout():
    result = wait_ready(lambda: False, time.monotonic() + 0.1)
    assert result == Readiness.timeout


def test_hung_probe_cannot_outlive_wait(tmp_path):
    evidence = tmp_path / "started"

    def probe():
        evidence.write_text("started")
        time.sleep(10)

        return True

    before = time.monotonic()
    result = wait_ready(probe, before + 0.2)
    elapsed = time.monotonic() - before
    assert evidence.exists()
    assert result == Readiness.timeout
    assert elapsed < 1


def test_probe_failure_is_not_ready():
    def probe():
        raise RuntimeError("failed to start")

    assert wait_ready(probe, time.monotonic() + 1) == Readiness.failed


def test_expired_deadline_does_not_spawn(tmp_path):
    def probe():
        (tmp_path / "unexpected").touch()

        return True

    assert wait_ready(probe, time.monotonic() - 1) == Readiness.timeout
    assert not (tmp_path / "unexpected").exists()


@pytest.mark.parametrize("deadline", [float("nan"), float("inf")])
def test_invalid_deadline_is_rejected(deadline):
    with pytest.raises(ValueError):
        wait_ready(lambda: True, deadline)
