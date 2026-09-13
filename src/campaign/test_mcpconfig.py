"""La couche `managed` de la config MCP : écrite par le runtime, sans shell ni secret."""

import json

import pytest

from campaign.mcpconfig import LAYER, managed_layer, write_managed
from campaign.registry import TaskLifecycle, ToolEntry, project


DIGESTS = {"tools/csv.py": "a" * 64}


def tool(**changes):
    fields = {"key": "read_csv", "module": "tools.csv", "call": "read",
              "digests": dict(DIGESTS), "lifecycle": TaskLifecycle.passed}

    return ToolEntry(**{**fields, **changes})


def test_only_what_the_projection_exposes_reaches_the_layer():
    projection = project([tool(), tool(key="broken", lifecycle=TaskLifecycle.failed)], DIGESTS, {})
    layer = managed_layer(projection, "python3.12")

    assert set(layer["mcpServers"]) == {"read_csv"}
    assert layer["layer"] == LAYER


def test_a_server_is_an_executable_and_an_exact_argument_list():
    # pas de shell, pas d'env, pas de cwd : la commande n'est jamais une chaîne à interpréter
    server = managed_layer(project([tool()], DIGESTS, {}), "python3.12")["mcpServers"]["read_csv"]

    assert server == {"command": "python3.12", "args": ["-m", "tools.csv", "--call", "read"]}
    assert set(server) == {"command", "args"}


def test_the_layer_carries_no_environment_and_no_secret():
    layer = managed_layer(project([tool()], DIGESTS, {}), "python3.12")
    rendered = json.dumps(layer)

    assert "env" not in rendered
    assert "${" not in rendered


def test_an_empty_projection_writes_an_empty_layer():
    layer = managed_layer(project([], DIGESTS, {}), "python3.12")

    assert layer == {"layer": LAYER, "mcpServers": {}}


def test_the_managed_file_is_owned_whole_and_written_through_the_journal(bound, journal_double):
    path, _ = bound
    journal_double.json_files[path] = {"mcpServers": {"stale": {"command": "sh"}}, "user": "keep me"}
    write_managed(path, project([tool()], DIGESTS, {}), "python3.12", trace=journal_double)
    written = journal_double.json_files[path]

    assert set(written["mcpServers"]) == {"read_csv"}
    assert "user" not in written


@pytest.mark.parametrize("interpreter", ["python3.12", "/usr/bin/python3"])
def test_the_interpreter_is_never_hard_coded(interpreter):
    layer = managed_layer(project([tool()], DIGESTS, {}), interpreter)

    assert layer["mcpServers"]["read_csv"]["command"] == interpreter
