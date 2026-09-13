"""Le registre : sept états dont trois échecs, et une satisfaction qui périme avec les octets."""

import pytest

from campaign.registry import (
    FAILURES, Omission, OmissionReason, Projection, Surface, TaskLifecycle, ToolEntry,
    diverged, fingerprint, is_satisfied, project,
)
from kernel.contracts import NodeStatus


CSV = "a" * 64
JSON = "b" * 64
DIGESTS = {"tools/csv.py": CSV, "tools/json.py": JSON, "README.md": "c" * 64}


def entry(**changes):
    fields = {
        "key": "csv",
        "module": "tools.csv",
        "call": "read",
        "digests": {"tools/csv.py": CSV},
        "lifecycle": TaskLifecycle.passed,
    }

    return ToolEntry(**{**fields, **changes})


def test_seven_states_of_which_three_are_failures():
    assert len(TaskLifecycle) == 7
    assert set(FAILURES) == {TaskLifecycle.failed, TaskLifecycle.blocked, TaskLifecycle.exhausted}


def test_failure_is_never_a_single_state():
    # « échoué » ne dit pas s'il faut réessayer : les trois formes se distinguent mécaniquement
    assert len({member.value for member in FAILURES}) == 3
    assert TaskLifecycle.retryable not in FAILURES


def test_the_lifecycle_stays_inside_the_kernel_vocabulary():
    assert {member.value for member in TaskLifecycle} <= {member.value for member in NodeStatus}


def test_fingerprint_ignores_ordering_and_covers_every_listed_file():
    left = fingerprint({"a.py": "1" * 64, "b.py": "2" * 64})
    right = fingerprint({"b.py": "2" * 64, "a.py": "1" * 64})

    assert left == right
    assert left != fingerprint({"a.py": "1" * 64})
    assert left != fingerprint({"a.py": "1" * 64, "b.py": "3" * 64})


@pytest.mark.parametrize("current,satisfied", [
    (DIGESTS, True),
    ({**DIGESTS, "tools/csv.py": "9" * 64}, False),
    ({**DIGESTS, "README.md": "9" * 64}, True),
    ({"tools/json.py": JSON}, False),
])
def test_satisfaction_perishes_with_the_bytes_of_its_own_files(current, satisfied):
    assert is_satisfied(entry(), current) is satisfied


def test_a_vanished_file_perishes_the_satisfaction_too():
    wide = entry(digests={"tools/csv.py": CSV, "tools/gone.py": "d" * 64})

    assert not is_satisfied(wide, DIGESTS)
    assert diverged(wide, DIGESTS) == ["tools/gone.py"]


def test_a_failed_module_omits_every_one_of_its_tools():
    entries = [
        entry(),
        entry(key="reader"),
        entry(key="dump", module="tools.json", digests={"tools/json.py": JSON}),
    ]
    projection = project(entries, DIGESTS, {"tools.csv": "ImportError: no module named pandas"})
    omitted = {omission.subject: omission for omission in projection.omissions}

    assert [available.key for available in projection.available] == ["dump"]
    assert set(omitted) == {"csv", "reader"}
    assert {omission.reason for omission in omitted.values()} == {OmissionReason.module_load_failed}
    assert "pandas" in omitted["csv"].detail


@pytest.mark.parametrize("lifecycle", [state for state in TaskLifecycle if state is not TaskLifecycle.passed])
def test_only_a_passed_task_reaches_the_surface(lifecycle):
    projection = project([entry(lifecycle=lifecycle)], DIGESTS, {})

    assert projection.available == []
    assert projection.omissions[0].reason is OmissionReason.not_passed
    assert projection.omissions[0].detail == lifecycle.value


def test_a_stale_entry_is_omitted_with_the_file_that_moved():
    projection = project([entry()], {**DIGESTS, "tools/csv.py": "9" * 64}, {})

    assert projection.available == []
    assert projection.omissions == [Omission(surface=Surface.tools, reason=OmissionReason.stale_fingerprint,
                                             subject="csv", detail="tools/csv.py")]


def test_a_clean_projection_omits_nothing():
    projection = project([entry()], DIGESTS, {})

    assert [available.key for available in projection.available] == ["csv"]
    assert projection.omissions == []


def test_the_projection_round_trips_through_json():
    projection = project([entry()], {}, {})

    assert Projection.model_validate_json(projection.model_dump_json()) == projection
    assert projection.omissions[0].surface is Surface.tools
