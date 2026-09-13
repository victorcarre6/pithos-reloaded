"""Les agrégats se calculent sur les payloads réellement publiés, et ne comblent aucun trou."""

import pytest

from kernel.errors import Cause, PithosError
from observatory.api.stats import context, daily, indicators, tools, validate

CONTEXT_WINDOW = 16384  # capacité explicitement fournie par la fixture


def test_daily_splits_by_utc_day_and_counts_what_it_could_not_date(an_event, moment, validation_event,
                                                                   model_call_event, tool_event):
    events = [
        validation_event(at=moment(1)),
        validation_event(at=moment(2), verification="rejected"),
        model_call_event(at=moment(3), prompt_estimate=100, prompt_tokens=120),
        tool_event("splice", at=moment(4), function_name="f", new_source="def f(x): return x"),
        an_event(ts="2026-09-08T09:00:00+00:00", type="status", payload={}),
        an_event(ts="hier", type="status", payload={}),
    ]
    report = daily(events)
    first, second = report["days"]
    assert [day["day"] for day in report["days"]] == ["2026-09-07", "2026-09-08"]
    assert (first["verified"], first["rejected"]) == (1, 1)
    assert (first["model_calls"], first["tool_calls"]) == (1, 1)
    assert first["families"] == {"validation": 2, "status": 1, "tool_activity": 1}
    assert second["events"] == 1
    assert report["undated_events"] == 1


def test_tools_measures_splice_inflation_against_the_useful_change(tool_event, moment):
    before = b"def f(x):\n    return x\n"
    after = b"def f(x):\n    return x + 1\n"
    events = [
        tool_event("splice", at=moment(1), function_name="f", new_source="def f(x):\n    return x + 1\n"),
        tool_event("write", at=moment(2), before_hex=before.hex(), after_hex=after.hex()),
    ]
    report = tools(events)
    inflation = report["splice_inflation"]
    assert [row["operation"] for row in report["tools"]] == ["splice", "write"]
    assert inflation["pairs"] == 1
    assert inflation["patch_bytes"] == len(after)
    assert inflation["changed_bytes"] == 4
    assert inflation["ratio"] == round(len(after) / 4, 3)


def test_tools_without_any_write_reports_no_ratio(tool_event, moment):
    report = tools([tool_event("splice", at=moment(1), function_name="f", new_source="def f(): ...")])
    assert report["splice_inflation"] == {
        "pairs": 0,
        "patch_bytes": 0,
        "changed_bytes": 0,
        "ratio": None,
    }


@pytest.mark.parametrize("prompt_tokens,expected", [
    (2_000, "low"),
    (9_000, "moderate"),
    (14_000, "high"),
    (17_000, "overflow_risk"),
])
def test_context_grades_pressure_on_the_measured_usage(model_call_event, moment, prompt_tokens, expected):
    events = [model_call_event(at=moment(1), prompt_estimate=1_000, prompt_tokens=prompt_tokens)]
    call = context(events)["calls"][0]
    assert call["pressure"] == expected
    assert call["margin_tokens"] == CONTEXT_WINDOW - prompt_tokens - 512
    assert call["density"] == round(prompt_tokens / 1_000, 3)


def test_context_leaves_an_unreported_usage_absent(model_call_event, moment):
    report = context([model_call_event(at=moment(1), prompt_estimate=800)])
    call = report["calls"][0]
    assert (call["prompt_tokens"], call["occupancy"], call["margin_tokens"]) == (None, None, None)
    assert call["pressure"] == "unknown"
    assert report["calls_without_usage"] == 1
    assert report["window"] == CONTEXT_WINDOW


def test_indicators_report_none_rather_than_a_zero_without_observation(an_event, moment):
    report = indicators([an_event(ts=moment(1), type="status", payload={})])
    assert report["progress_without_intervention"]["value"] is None
    assert report["verified_tool_reused"]["value"] is None
    assert report["diagnosed_limitations"]["value"] == 0
    assert report["stop_proposed_on_exhaustion"]["observations"] == 0


def test_indicators_measure_progress_blockage_and_resumption(node_event, validation_event, an_event, moment):
    events = [
        node_event("root", at=moment(1)),
        validation_event(at=moment(2)),
        node_event("a", at=moment(3), parent_id="root", depth=1, status="blocked",
                   blocked_cause="unverifiable", criterion=None),
        an_event(ts=moment(4), type="status", payload={"segment_from": "events.jsonl", "torn_bytes": 12}),
        an_event(ts=moment(5), type="status", payload={"stop_proposal": {"reason": "backlog_exhausted"}}),
    ]
    report = indicators(events)
    assert report["progress_without_intervention"] == {
        "question": "Progresse-t-il sans intervention ?",
        "value": 0.5,
        "verified": 1,
        "cycles": 2,
    }
    assert report["diagnosed_limitations"]["by_cause"] == {"unverifiable": 1}
    assert report["resumption_after_interruption"]["value"] == 1
    assert report["stop_proposed_on_exhaustion"]["value"] == 1


def test_a_verified_symbol_counts_as_reused_only_when_named_later(validation_event, tool_event, node_event, moment):
    events = [
        validation_event(at=moment(1), symbols=("f",)),
        validation_event(at=moment(2), symbols=("g",)),
        tool_event("splice", at=moment(3), function_name="f", new_source="def f(x): return x"),
    ]
    report = indicators(events)["verified_tool_reused"]
    assert report["reused"] == ["f"]
    assert report["verified_symbols"] == 2
    assert report["value"] == 0.5


def test_a_symbol_named_before_its_verification_is_not_a_reuse(validation_event, tool_event, moment):
    events = [
        tool_event("splice", at=moment(1), function_name="f", new_source="def f(x): return x"),
        validation_event(at=moment(2), symbols=("f",)),
    ]
    assert indicators(events)["verified_tool_reused"]["reused"] == []


def test_validate_reports_every_violation_with_its_field_path():
    summary = {
        "n_events": 3,
        "families": {"status": 1},
        "digest": {"window": {"total": 2, "above": 0, "below": 0}},
        "artifacts": {"tree.json": {"path": "/tmp/tree.json", "exists": True, "size": None}},
    }
    with pytest.raises(PithosError) as failure:
        validate(summary)
    paths = [violation.field_path for violation in failure.value.violations]
    assert paths == ["families", "digest.window.total", "artifacts.tree.json"]
    assert failure.value.cause == Cause.invalid_schema


def test_validate_accepts_a_coherent_summary():
    summary = {
        "n_events": 1,
        "families": {"status": 1},
        "digest": {"window": {"total": 1, "above": 0, "below": 0}},
        "artifacts": {"tree.json": {"path": "/tmp/tree.json", "exists": False, "size": None}},
    }
    assert validate(summary) is None


def test_context_never_guesses_a_window_from_the_model_name(model_call_event, moment):
    event = model_call_event(at=moment(1), prompt_tokens=100)
    event.payload.pop("context_window")
    call = context([event])["calls"][0]
    assert call["context_window"] is None
    assert call["occupancy"] is None
    assert call["pressure"] == "unknown"


def test_context_counts_truncation_once_and_keeps_asserted_capacity(model_call_event, moment):
    event = model_call_event(at=moment(1), prompt_tokens=100, outcome="truncated")
    event.payload.update(raw_stop_reason="length", context_window=4096, context_provenance="asserted")
    report = context([event])
    assert report["summary"]["calls"] == 1
    assert report["summary"]["truncated"] == 1
    assert report["summary"]["truncation_rate"] == 1
    assert report["calls"][0]["context_provenance"] == "asserted"
    assert report["calls"][0]["margin_tokens"] == 4096 - 100 - 512


def test_preflight_refusal_is_not_a_model_request(model_call_event, moment):
    report = context([model_call_event(at=moment(1), outcome="budget_refused")])
    assert report["summary"]["calls"] == 0
    assert report["summary"]["budget_refused"] == 1
    assert report["summary"]["truncation_rate"] is None


def test_node_intent_does_not_count_as_observed_progress(node_event, moment):
    event = node_event("n", at=moment(1), status="blocked", blocked_cause="unverifiable")
    event.payload["phase"] = "intent"
    report = indicators([event])
    assert report["progress_without_intervention"]["cycles"] == 0
    assert report["diagnosed_limitations"]["value"] == 0
