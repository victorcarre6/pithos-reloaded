"""Gardes pures du remplacement AST ; aucune source candidate n'est exécutée."""

from hashlib import sha256
from pathlib import Path

import pytest

from kernel.errors import PithosError
from workspace.splice import prepare_splice


BEFORE = b"# header\n\ndef f(x):\n    return x\n\n# keep\ndef g(y):\n    return y\n"


@pytest.mark.parametrize("source", [
    '{"function_name": "f", "new_source": "def f(x): pass"}',
    "42", "", "def f(x): pass\ndef g(y): pass", "def g(x): pass",
    "import os\ndef f(x): pass", "def f(x):\n", "def f(x):\n    return '\0'",
])
def test_rejects_payload_before_mutation(source):
    with pytest.raises(PithosError) as caught:
        prepare_splice(BEFORE, "f", source, target=Path("tool.py"))
    assert caught.value.field_path == "new_source"


@pytest.mark.parametrize("parameters", ["x, y", "x=1", "renamed", "x, /", "x, *, y", "*x", "x, **kwargs"])
def test_arity_error_names_both_signatures(parameters):
    with pytest.raises(PithosError) as caught:
        prepare_splice(BEFORE, "f", f"def f({parameters}): return 0", target=Path("tool.py"))
    assert "f(x)" in str(caught.value)
    assert f"f({parameters})" in str(caught.value)


def test_compiles_entire_candidate_without_executing_it(tmp_path):
    marker = tmp_path / "executed"
    source = f"def f(x):\n    open({str(marker)!r}, 'w').close()\n    return 1\n"
    plan = prepare_splice(BEFORE, "f", source, target=Path("tool.py"))
    assert not marker.exists()
    assert plan.fact.sha_before == sha256(BEFORE).hexdigest()
    assert plan.fact.sha_after == sha256(plan.content).hexdigest()
    assert plan.fact.spliced_range == (3, 4)
    assert plan.fact.n_replacements == 1
    assert plan.lines_added == 1
    assert "+    return 1" in plan.diff


def test_parseable_but_uncompilable_def_is_rejected():
    with pytest.raises(PithosError) as caught:
        prepare_splice(BEFORE, "f", "def f(x):\n    break\n", target=Path("tool.py"))
    message = str(caught.value)
    assert all(part in message for part in ("tool.py", "compile", "SyntaxError", "repair"))


def test_noop_is_not_a_replacement():
    with pytest.raises(PithosError, match="n_replacements=0"):
        prepare_splice(BEFORE, "f", "def f(x):\n    return x\n", target=Path("tool.py"))


@pytest.mark.parametrize("bom", [b"", b"\xef\xbb\xbf"])
@pytest.mark.parametrize("newline", [b"\n", b"\r\n", b"\r"])
def test_preserves_bytes_outside_decorated_range(bom, newline):
    prefix = bom + b"# accents: \xc3\xa9\r\n# mixed\n"
    old = newline.join([b"@decorate", b"async def f(x):", b"    return x", b""])
    suffix = b"# untouched\r\ndef g():\n    pass\r\n"
    plan = prepare_splice(prefix + old + suffix, "f", "@decorate\nasync def f(x):\n    return 7\n", target=Path("tool.py"))
    replacement = newline.join([b"@decorate", b"async def f(x):", b"    return 7", b""])
    assert plan.content == prefix + replacement + suffix
    assert plan.fact.spliced_range == (3, 5)


@pytest.mark.parametrize("wrapper", ["{}", "```python\n{}\n```", "```\n{}\n```", "12: def f(x):\n13:     return 1"])
def test_exact_envelopes(wrapper):
    source = wrapper.format("def f(x):\n    return 1")
    plan = prepare_splice(BEFORE, "f", source, target=Path("tool.py"))
    assert b"def f(x):\n    return 1\n" in plan.content


@pytest.mark.parametrize("source", [
    "prose\n```python\ndef f(x): pass\n```", "```python\ndef f(x): pass\n```\nmore",
    "12: def f(x):\n15:     pass", "async def f(x): return x",
])
def test_no_approximate_payload_recovery(source):
    with pytest.raises(PithosError):
        prepare_splice(BEFORE, "f", source, target=Path("tool.py"))


def test_preserves_absence_of_final_newline():
    before = b"\xef\xbb\xbfdef f(x):\r\n    return x"
    plan = prepare_splice(before, "f", "def f(x):\n    return 1\n", target=Path("tool.py"))
    assert plan.content == b"\xef\xbb\xbfdef f(x):\r\n    return 1"


@pytest.mark.parametrize("before", [
    b"class C:\n    def f(x): pass\n", b"def f(x): pass\ndef f(x): pass\n",
    b"def f(x): pass\nclass f: pass\n", b"# no functions\n",
])
def test_target_must_identify_one_module_function(before):
    with pytest.raises(PithosError):
        prepare_splice(before, "f", "def f(x): return 1", target=Path("tool.py"))


def test_parenthesized_decorator_is_replaced_in_full():
    before = b"# keep\n@(\n    decorate\n)\ndef f(x):\n    return x\n# tail\n"
    plan = prepare_splice(before, "f", "@decorate\ndef f(x):\n    return 1", target=Path("tool.py"))
    assert plan.content == b"# keep\n@decorate\ndef f(x):\n    return 1\n# tail\n"
    assert plan.fact.spliced_range == (2, 6)


def test_encoding_cookie_must_not_reinterpret_utf8_replacement():
    before = b"# coding: latin-1\ndef f(x):\n    return x\n"
    with pytest.raises(PithosError, match="UTF-8"):
        prepare_splice(before, "f", "def f(x):\n    return 'é'", target=Path("tool.py"))


def test_unicode_line_separator_in_literal_preserves_offsets():
    before = "MARK = 'a\u2028b'\ndef f(x):\n    return x\n".encode()
    plan = prepare_splice(before, "f", "def f(x): return 1", target=Path("tool.py"))
    assert plan.content == "MARK = 'a\u2028b'\ndef f(x): return 1\n".encode()


def test_optional_values_and_annotations_can_change():
    before = b"def f(x: int=1, /, y=2, *args, flag=True, **kwargs):\n    return x\n"
    source = "def f(renamed: float=3, /, y=4, *other, flag=False, **rest):\n    return renamed\n"
    assert prepare_splice(before, "f", source, target=Path("tool.py")).fact.n_replacements == 1


def test_replacement_cannot_change_module_encoding():
    before = b"def f(x): return x\n"
    with pytest.raises(PithosError, match="UTF-8"):
        prepare_splice(before, "f", "# coding: latin-1\ndef f(x): return 'é'", target=Path("tool.py"))
