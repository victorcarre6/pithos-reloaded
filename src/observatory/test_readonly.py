"""Les garanties statiques du module : il n'écrit pas, ne binde qu'en loopback, ne rend pas d'HTML."""

import ast
from pathlib import Path

import pytest

from observatory.api.routes import HOST

SOURCES = sorted(
    path for path in (Path(__file__).resolve().parent / "api").glob("*.py")
    if not path.name.startswith("test_")
)
WRITE_METHODS = {
    "write", "writelines", "write_text", "write_bytes", "mkdir", "touch", "unlink", "rmdir",
    "rename", "replace", "chmod", "remove", "makedirs", "symlink_to", "hardlink_to",
}
WRITE_MODES = ("w", "a", "x", "+")


def write_calls(source: str) -> list[str]:
    "Toute ouverture en écriture et toute mutation de filesystem trouvée dans un fichier source."

    tree = ast.parse(source)
    found = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = ast.unparse(node.func)
        attribute = name.rsplit(".", 1)[-1]

        # une mutation de filesystem se nomme ; une ouverture se lit dans son mode
        if attribute in WRITE_METHODS:
            found.append(name)
        if attribute != "open":
            continue
        modes = [argument for argument in node.args[1:] if isinstance(argument, ast.Constant)]
        modes.extend(word.value for word in node.keywords if word.arg == "mode")
        if any(mode.value.startswith(WRITE_MODES) for mode in modes if isinstance(mode.value, str)):
            found.append(f"{name}({modes[0].value})")

    return found


def test_no_source_of_the_module_opens_a_file_for_writing():
    assert SOURCES
    assert {path.name: write_calls(path.read_text()) for path in SOURCES} == {path.name: [] for path in SOURCES}


@pytest.mark.parametrize("source", [
    "open('x.json', 'w')", "open('x.json', mode='a')", "path.write_text('x')",
    "path.write_bytes(b'x')", "path.mkdir()", "path.unlink()", "os.replace(a, b)",
])
def test_the_write_detector_sees_an_injected_write(source):
    assert write_calls(source)


def test_the_bind_address_is_a_constant_that_no_environment_variable_moves():
    routes = (Path(__file__).resolve().parent / "api" / "routes.py").read_text()
    tree = ast.parse(routes)
    names = {ast.unparse(node) for node in ast.walk(tree) if isinstance(node, ast.Attribute)}
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call) and ast.unparse(node.func) == "uvicorn.run"]
    hosts = [word.value for call in calls for word in call.keywords if word.arg == "host"]
    assert HOST == "127.0.0.1"
    assert [ast.unparse(host) for host in hosts] == ["HOST"]
    assert not {name for name in names if name.startswith(("os.environ", "os.getenv", "environ"))}


def test_the_api_never_renders_a_document():
    joined = "\n".join(path.read_text() for path in SOURCES)
    assert "HTMLResponse" not in joined
    assert "text/html" not in joined
    assert "Jinja" not in joined
