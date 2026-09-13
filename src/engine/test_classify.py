from pathlib import Path

import pytest
from pydantic import ValidationError

from engine.classify import ActionClass, RepoIndex, analyze_instruction
from engine.tree import Tree
from engine.walk import decompose


def test_targets_come_only_from_index_and_runtime_paths_are_excluded():
    index = RepoIndex(files=(Path("src/parser.py"), Path("tests/test_parser.py"), Path(".villani_code/parser.py")))
    analysis = analyze_instruction("fix parser.py and missing.py", index)
    targets = [candidate.target for candidate in analysis.candidate_targets]
    assert targets == [Path("src/parser.py")]
    assert analysis.action_classes == (ActionClass.CODE_EDIT,)
    assert analysis.risk_level == "medium"
    assert analysis.estimated_scope == "single_file"
    assert analysis.change_impact == "source_only"
    assert analysis.task_mode == "general"
    assert all(candidate.reason for candidate in analysis.candidate_targets)


def test_full_path_mentions_do_not_select_homonymous_files():
    index = RepoIndex(files=(Path("a/tool.py"), Path("b/tool.py")))
    analysis = analyze_instruction("fix a/tool.py", index)
    assert [candidate.target for candidate in analysis.candidate_targets] == [Path("a/tool.py")]


def test_ungrounded_instruction_has_no_invented_fallback():
    analysis = analyze_instruction("fix unavailable.py", RepoIndex(files=(Path("tool.py"),)))
    assert analysis.candidate_targets == ()


@pytest.mark.parametrize("instruction,mode,risk", [
    ("fix failing test", "fix_failing_test", "medium"),
    ("fix lint tool.py", "fix_lint_or_type", "medium"),
    ("refactor tool.py", "narrow_refactor", "medium"),
    ("update docs", "docs_update_safe", "medium"),
    ("inspect tool.py", "inspect_and_plan", "low"),
    ("delete tool.py", "general", "high"),
    ("git reset --hard", "general", "high"),
])
def test_five_classifications_are_deterministic(instruction, mode, risk):
    index = RepoIndex(files=(Path("tool.py"), Path("tests/test_tool.py"), Path("docs/guide.md")))
    analysis = analyze_instruction(instruction, index)
    assert analysis.task_mode == mode
    assert analysis.risk_level == risk
    assert analyze_instruction(instruction, index) == analysis


@pytest.mark.parametrize("path", [Path("/absolute.py"), Path("../escape.py")])
def test_index_rejects_paths_outside_repo(path):
    with pytest.raises(ValidationError):
        RepoIndex(files=(path,))


def test_classifier_is_consumed_by_decomposition(kernel_double, journal_double):
    index = RepoIndex(files=(Path("b/tool.py"), Path("a/tool.py")))
    tree = Tree(mission_id="mission", nodes=(kernel_double.node(criterion=None),), cap_children=2)
    result = decompose(tree, tree.nodes[0].id, "fix tool.py", index,
                       tree_path=Path("mission/tree.json"), journal=journal_double)
    assert [node.target for node in result.nodes[1:]] == [Path("a/tool.py"), Path("b/tool.py")]
    classification = journal_double.events[0].payload["analysis"]
    assert classification["action_classes"] == ["code_edit"]
    assert classification["estimated_scope"] == "narrow_multi_file"
    assert classification["change_impact"] == "source_only"
    assert classification["risk_level"] == "medium"
    assert classification["task_mode"] == "general"


def test_inspection_does_not_become_a_code_edit(kernel_double, journal_double):
    index = RepoIndex(files=(Path("tool.py"),))
    tree = Tree(mission_id="mission", nodes=(kernel_double.node(criterion=None),), cap_children=2)
    result = decompose(tree, tree.nodes[0].id, "inspect tool.py", index,
                       tree_path=Path("mission/tree.json"), journal=journal_double)
    assert len(result.nodes) == 1
    assert result.nodes[0].status == "blocked"
    assert journal_double.events[0].payload["analysis"]["task_mode"] == "inspect_and_plan"
