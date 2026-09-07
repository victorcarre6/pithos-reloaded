import pytest

from kernel.errors import Cause, ErrorAccumulator, PithosError


def test_accumulator_preserves_every_field_and_cause():
    errors = ErrorAccumulator()
    errors.add("tools[0].name", Cause.invalid_symbol, "missing symbol")
    errors.add("tools[1].criterion.domain", Cause.invalid_schema, "unknown domain")
    errors.add("tools[2].target", Cause.invalid_path, "outside workspace")

    with pytest.raises(PithosError) as caught:
        errors.raise_if_any()

    error = caught.value
    assert error.cause == Cause.invalid_schema
    assert error.field_path is None
    assert [(item.field_path, item.cause, item.detail) for item in error.violations] == [
        ("tools[0].name", Cause.invalid_symbol, "missing symbol"),
        ("tools[1].criterion.domain", Cause.invalid_schema, "unknown domain"),
        ("tools[2].target", Cause.invalid_path, "outside workspace"),
    ]
    errors.add("tools[3]", Cause.invalid_schema, "another error")
    assert len(error.violations) == 3
    assert "tools[2].target" in str(error)


def test_empty_accumulator_does_not_raise():
    ErrorAccumulator().raise_if_any()


def test_unknown_cause_is_rejected():
    with pytest.raises(ValueError):
        PithosError("success", "not an error cause")
