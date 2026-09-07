from itertools import product

import pytest
from pydantic import ValidationError

from kernel.facts import RecordKey, same_identity


def test_identity_is_an_equivalence_on_present_keys():
    first = RecordKey(kind="verification", value=("mission", "node", 1, "total"))
    restored = RecordKey.model_validate_json(first.model_dump_json())
    third = RecordKey(kind="verification", value=("mission", "node", 1, "total"))
    other = RecordKey(kind="verification", value=("mission", "node", 2, "total"))
    keys = [first, restored, third, other]
    for a, b, c in product(keys, repeat=3):
        assert same_identity(a, a)
        assert same_identity(a, b) == same_identity(b, a)
        if same_identity(a, b) and same_identity(b, c):
            assert same_identity(a, c)
    assert len(set(keys)) == 2
    assert not same_identity(first, other)
    assert not same_identity(None, None)
    assert not same_identity(first, None)
    assert not same_identity(None, first)


@pytest.mark.parametrize("value", [
    ("another", "node", 1, "total"), ("mission", "node ", 1, "total"),
    ("mission", "node", 2, "total"), ("mission", "node", 1, "idempotent"),
])
def test_no_component_is_ignored_or_normalized(value):
    first = RecordKey(kind="verification", value=("mission", "node", 1, "total"))
    other = RecordKey(kind="verification", value=value)
    assert not same_identity(first, other)


@pytest.mark.parametrize("data", [
    {"kind": "unknown", "value": ("m", "n", 1, "total")},
    {"kind": "verification", "value": "m:n:1:total"},
    {"kind": "verification", "value": ("", "n", 1, "total")},
    {"kind": "verification", "value": ("m", "n", 0, "total")},
    {"kind": "verification", "value": ("m", "n", True, "total")},
    {"kind": "verification", "value": ("m", "n", 1, "unknown")},
])
def test_record_key_rejects_untyped_or_partial_identities(data):
    with pytest.raises(ValidationError):
        RecordKey(**data)


@pytest.mark.parametrize("raw", ["same", {}, ("mission", "node", 1, "total")])
def test_raw_values_do_not_reconcile(raw):
    assert not same_identity(raw, raw)
