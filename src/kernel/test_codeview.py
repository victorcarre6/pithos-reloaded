import ast
from pathlib import Path

import pytest

from kernel import codeview
from kernel.errors import Cause, PithosError


SOURCE = '''
raise RuntimeError("inspection must never execute this module")

def smooth_levels(previous: tuple, target: tuple, factor: float = 0.5, *, clamp: bool = True):
    return tuple(a + factor * (b - a) for a, b in zip(previous, target))

async def mixed(first: int, /, second=None, *items: str, required: bytes, option=2, **extras) -> str:
    def nested():
        pass
    return "ok"

class Container:
    def method(self):
        pass
'''


def test_ast_preserves_signature_without_execution(tmp_path):
    path = tmp_path / "tool.py"
    path.write_text(SOURCE)
    smooth, mixed = codeview.symbols(path)
    assert smooth.name == "smooth_levels"
    assert smooth.arity == 3
    assert smooth.posonly == []
    assert smooth.kwonly == ["clamp"]
    assert smooth.defaults == {"factor": "0.5", "clamp": "True"}
    assert smooth.annotations == {
        "previous": "tuple",
        "target": "tuple",
        "factor": "float",
        "clamp": "bool",
    }
    assert mixed.posonly == ["first"]
    assert mixed.arity == 2
    assert mixed.kwonly == ["required", "option"]
    assert mixed.defaults == {"second": "None", "option": "2"}
    assert mixed.vararg == "items"
    assert mixed.kwarg == "extras"
    assert mixed.annotations == {
        "first": "int", "items": "str", "required": "bytes", "return": "str",
    }
    assert codeview.module_defs(path) == ["smooth_levels", "mixed", "Container"]


def test_smooth_levels_incident_is_visible_in_annotations(tmp_path):
    path = tmp_path / "tool.py"
    path.write_text(SOURCE)
    signature = codeview.symbols(path)[0]
    call = ast.parse("smooth_levels(0.0, 0.0, 0.0)", mode="eval").body
    assert len(call.args) == signature.arity  # l'arité seule laissait passer l'incident
    annotated = [signature.annotations[name] for name in ("previous", "target", "factor")]
    actual = [type(argument.value).__name__ for argument in call.args]
    assert annotated == ["tuple", "tuple", "float"]
    assert actual == ["float", "float", "float"]
    assert actual != annotated  # la gate peut rejeter le domaine sans exécuter le module


def test_ast_reports_invalid_or_unsupported_source(tmp_path):
    broken = tmp_path / "broken.py"
    broken.write_text("def broken(")
    with pytest.raises(SyntaxError):
        codeview.symbols(broken)
    unsupported = tmp_path / "tool.js"
    unsupported.write_text("function f() {}")
    with pytest.raises(PithosError, match="structural_unavailable"):
        codeview.symbols(unsupported)


def test_ast_rejects_oversized_source(tmp_path):
    path = tmp_path / "huge.py"
    path.write_bytes(b"#" * (codeview.MAX_SOURCE_BYTES + 1))
    with pytest.raises(PithosError, match="oversized"):
        codeview.symbols(path)


def test_snippet_of_ten_megabyte_line_is_bounded(tmp_path, monkeypatch):
    path = tmp_path / "huge.py"
    path.write_bytes(b"x" * 10_000_000)
    observed = []
    original_open = Path.open

    class BoundedReader:
        def __enter__(self):
            self.stream = original_open(path, "rb")
            return self

        def __exit__(self, *args):
            self.stream.close()

        def read(self, size=-1):
            observed.append(size)
            assert 0 <= size <= codeview.MAX_SNIPPET_BYTES
            return self.stream.read(size)

    monkeypatch.setattr(Path, "open", lambda *args, **kwargs: BoundedReader())
    result = codeview.snippet(path, 1, 100)
    assert len(result.encode()) == codeview.MAX_SNIPPET_BYTES
    assert observed == [codeview.MAX_SNIPPET_BYTES]


def test_snippet_line_range_and_unicode_budget(tmp_path):
    path = tmp_path / "text.py"
    lines = [f"line {number}\n" for number in range(1, 101)]
    path.write_text("".join(lines))
    assert codeview.snippet(path, 2, 3) == "line 2\nline 3\n"
    assert codeview.snippet(path, 200, 201) == ""
    result = codeview.snippet(path, 1, 100)
    assert len(result.splitlines()) == codeview.MAX_SNIPPET_LINES
    path.write_text("🙂" * 10_000)
    result = codeview.snippet(path, 1, 1)
    assert len(result.encode()) <= codeview.MAX_SNIPPET_BYTES
    assert "�" not in result
    path.write_bytes(b"\xff" * 10_000)
    assert len(codeview.snippet(path, 1, 1).encode()) <= codeview.MAX_SNIPPET_BYTES


@pytest.mark.parametrize("start,end", [(0, 1), (-1, 1), (2, 1)])
def test_snippet_rejects_invalid_ranges(tmp_path, start, end):
    with pytest.raises(ValueError):
        codeview.snippet(tmp_path / "unused", start, end)


@pytest.mark.parametrize("suffix,raw,expected", [
    (".ZIP", b"text", True), (".py", b"", False),
    (".py", b"hello\x00world", True),
    (".txt", b"\xff\xfeh\x00", True),
    (".txt", b"\xfe\xff\x00h", True),
    (".txt", b"\xff\xfe\x00\x00", True),
    (".txt", b"\x00\x00\xfe\xff", True),
    (".txt", b"\x01" * 3 + b"a" * 7, False),
    (".txt", b"\x01" * 4 + b"a" * 6, True),
    (".txt", "é漢字\n\t".encode(), False),
])
def test_binary_detection(tmp_path, suffix, raw, expected):
    path = tmp_path / ("file" + suffix)
    path.write_bytes(raw)
    assert codeview.is_binary(path) is expected


def test_path_containment_resolves_symlinks(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    sibling = tmp_path / "repo-other"
    sibling.mkdir()
    (root / "escape").symlink_to(sibling, target_is_directory=True)
    (root / "inside").symlink_to(root, target_is_directory=True)
    assert codeview.is_path_within(root / "new.py", root)
    assert codeview.is_path_within(root, root)
    assert codeview.is_path_within(root / "inside" / "new.py", root)
    assert not codeview.is_path_within(root / "escape" / "file.py", root)
    assert not codeview.is_path_within(root / ".." / "repo-other", root)


PATH_CASES = [
    (".git/config", "vcs_internal"), ("src/.git/HEAD", "vcs_internal"),
    (".vscode/settings.json", "editor_artifact"), (".idea/a", "editor_artifact"),
    (".DS_Store", "editor_artifact"), ("nested/Thumbs.db", "editor_artifact"),
    ("__pycache__/tool.py", "runtime_artifact"), (".pytest_cache/v/cache", "runtime_artifact"),
    (".mypy_cache/a", "runtime_artifact"), (".ruff_cache/a", "runtime_artifact"),
    (".ipynb_checkpoints/a", "runtime_artifact"), (".venv/lib/a.py", "runtime_artifact"),
    ("venv/lib/a.py", "runtime_artifact"), (".villani_code/state.json", "runtime_artifact"),
    ("tool.PYC", "runtime_artifact"), ("tool.pyo", "runtime_artifact"),
    ("tool.pyd", "runtime_artifact"),
    ("build/a.py", "generated"), ("dist/a.py", "generated"),
    ("node_modules/pkg/index.js", "generated"),
    ("README.md", "authoritative"), ("docs/design.md", "authoritative"),
    ("src/tool.py", "authoritative"), ("tests/test_tool.py", "authoritative"),
    ("pyproject.toml", "authoritative"), ("requirements.txt", "authoritative"),
    ("mybuild/real.py", "authoritative"), ("src/venv_helper.py", "authoritative"),
    (".git/.idea/a.pyc", "vcs_internal"), ("build/.idea/a.pyc", "editor_artifact"),
    ("build/a.pyc", "runtime_artifact"),
]


@pytest.mark.parametrize("path,expected", PATH_CASES)
def test_path_classification_table(path, expected):
    category = codeview.classify_repo_path(Path(path))
    assert category.value == expected
    assert (category == codeview.PathClass.authoritative) is (expected == "authoritative")
    assert len(codeview.PathClass) == 5


@pytest.mark.parametrize("path", [
    ".env", ".env.production", ".env.example", ".hidden", ".hidden/tool.py",
    "secrets/key.pem", "key.key", "key.p12", "key.pfx", "key.crt", "key.cer",
    "credentials.json", "api_key.json", "../tool.py", "/tmp/tool.py", ".",
])
def test_unclassified_or_sensitive_paths_are_rejected(path):
    with pytest.raises(PithosError) as caught:
        codeview.classify_repo_path(Path(path))
    assert caught.value.cause == Cause.invalid_path
