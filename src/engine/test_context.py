from pathlib import Path

import pytest
from pydantic import ValidationError

from engine.context import ContextItem, ContextPacket, assemble, detect_stale_context
from kernel.errors import Cause, PithosError


def item(source_id, units, **changes):
    values = {
        "source_id": source_id,
        "source_type": "file",
        "content": f"full content of {source_id}",
        "estimated_units": units,
        "retention": "optional",
        "included_reason": "task_relevance",
        "excluded_reason": None,
        "fingerprints": {},
    }
    values.update(changes)

    return ContextItem(**values)


@pytest.mark.parametrize("reasons", [
    {"included_reason": None, "excluded_reason": None},
    {"included_reason": "task_relevance", "excluded_reason": "stale"},
    {"included_reason": "guessed", "excluded_reason": None},
])
def test_each_item_requires_exactly_one_named_reason(reasons):
    with pytest.raises(ValidationError):
        item("a", 1, **reasons)


def test_fifo_eviction_retains_irreducible_content_and_full_inventory(kernel_double):
    items = [
        item("old", 35),
        item("rule", 40, retention="required"),
        item("recent", 30),
    ]
    packet = assemble(kernel_double.node(), 100, items=items, fingerprints={})
    assert packet.initial_pressure == 1.05
    assert packet.budget.total_units == 48  # 40 de contenu requis + 8 pour la notice
    assert packet.budget.pressure == 0.48
    assert packet.budget.pressure_level == "moderate"
    assert packet.evictions == 2
    assert packet.items[0].excluded_reason == "budget_pressure"
    assert [entry.content for entry in packet.items] == [entry.content for entry in items]
    assert packet.items[2].excluded_reason == "budget_pressure"
    assert packet.render() == "[omitted: budget_pressure=2]\n\nfull content of rule"
    assert items[0].included_reason == "task_relevance"
    assert ContextPacket.model_validate_json(packet.model_dump_json()) == packet


@pytest.mark.parametrize("units,level", [(44, "low"), (45, "moderate"), (74, "moderate"),
                                         (75, "high"), (99, "high"), (100, "overflow_risk")])
def test_pressure_thresholds_for_irreducible_content(kernel_double, units, level):
    packet = assemble(kernel_double.node(), 100, items=[item("rule", units, retention="required")], fingerprints={})
    assert packet.budget.pressure_level == level
    assert packet.blocked_cause is None


def test_irreducible_overflow_is_typed_and_cannot_be_rendered(kernel_double):
    entries = [item("rule", 101, retention="required"), item("optional", 5)]
    packet = assemble(kernel_double.node(), 100, items=entries, fingerprints={})
    assert packet.blocked_cause == Cause.context_overflow
    assert packet.items[0].content == entries[0].content
    assert packet.items[1].excluded_reason == "budget_pressure"
    with pytest.raises(PithosError) as caught:
        packet.render()
    assert caught.value.cause == Cause.context_overflow


@pytest.mark.parametrize("current", [{Path("tool.py"): "b" * 64}, {}])
def test_stale_handoff_is_excluded_even_if_file_is_missing(kernel_double, current):
    handoff = item("previous", 20, source_type="handoff", fingerprints={Path("tool.py"): "a" * 64})
    assert detect_stale_context(handoff, current)
    packet = assemble(kernel_double.node(), 100, items=[handoff], fingerprints=current)
    assert packet.items[0].excluded_reason == "stale"
    assert packet.render() == "[omitted: stale=1]"


def test_matching_handoff_is_retained(kernel_double):
    fingerprints = {Path("tool.py"): "a" * 64}
    handoff = item("previous", 20, source_type="handoff", fingerprints=fingerprints)
    packet = assemble(kernel_double.node(), 100, items=[handoff], fingerprints=fingerprints)
    assert not detect_stale_context(handoff, fingerprints)
    assert packet.render() == handoff.content


def test_handoff_requires_fingerprints():
    with pytest.raises(ValidationError):
        item("previous", 20, source_type="handoff")


def test_missing_required_context_blocks_instead_of_using_stale_text(kernel_double):
    rule = item("rule", 1, retention="required", fingerprints={Path("rules.md"): "a" * 64})
    packet = assemble(kernel_double.node(), 100, items=[rule], fingerprints={})
    assert packet.blocked_cause == Cause.unverifiable
    with pytest.raises(PithosError):
        packet.render()


def test_duplicate_and_preexcluded_entries_keep_their_reasons(kernel_double):
    entries = [item("a", 1), item("a", 1), item("b", 1, included_reason=None, excluded_reason="irrelevant")]
    packet = assemble(kernel_double.node(), 100, items=entries, fingerprints={})
    assert [entry.excluded_reason for entry in packet.items] == [None, "duplicate", "irrelevant"]
    assert packet.budget.total_units == 11  # la notice n'est pas hors budget


def test_conflicting_duplicate_cannot_hide_required_context(kernel_double):
    entries = [item("a", 80), item("a", 80, retention="required")]
    with pytest.raises(ValueError, match="conflicting"):
        assemble(kernel_double.node(), 100, items=entries, fingerprints={})


@pytest.mark.parametrize("limit", [0, -1, True, 1.5])
def test_invalid_context_budget_is_rejected(kernel_double, limit):
    with pytest.raises(ValueError):
        assemble(kernel_double.node(), limit, items=[], fingerprints={})


def test_omission_notice_is_charged_before_admission(kernel_double):
    entries = [item("rule", 99, retention="required"), item("hidden", 1, included_reason=None, excluded_reason="irrelevant")]
    packet = assemble(kernel_double.node(), 100, items=entries, fingerprints={})
    assert packet.budget.total_units > 100
    assert packet.blocked_cause == Cause.context_overflow
    with pytest.raises(PithosError):
        packet.render()


def test_omission_notice_names_reasons_without_leaking_excluded_contents(kernel_double):
    entries = [item("visible", 10), item("hidden", 5, content="SECRET", included_reason=None, excluded_reason="stale")]
    packet = assemble(kernel_double.node(), 100, items=entries, fingerprints={})
    assert packet.render().startswith("[omitted: stale=1]")
    assert packet.budget.total_units > 10
    assert "SECRET" not in packet.render()
