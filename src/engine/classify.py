"""Classifieur déterministe porté de Villani planning.py:11-57,154-332,388-400.

Villani : projet personnel, copie libre accordée (resources/MANIFEST.md).
L'index explicite remplace leur repo_map ; aucune cible de repli inventée.
"""

import re
from enum import StrEnum
from pathlib import Path

from pydantic import Field, model_validator

from kernel.codeview import PathClass, classify_repo_path
from kernel.contracts import Contract, Name


class PlanRiskLevel(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class ActionClass(StrEnum):
    READ_ONLY = "read_only"
    CODE_EDIT = "code_edit"
    CONFIG_EDIT = "config_edit"
    DEPENDENCY_CHANGE = "dependency_change"
    MIGRATION = "migration"
    TEST_REPAIR = "test_repair"
    REFACTOR_NARROW = "refactor_narrow"
    REFACTOR_BROAD = "refactor_broad"
    SHELL_READ_ONLY = "shell_read_only"
    SHELL_MUTATING = "shell_mutating"
    GIT_SAFE = "git_safe"
    GIT_DESTRUCTIVE = "git_destructive"
    FILE_DELETE_OR_MOVE = "file_delete_or_move"


class EstimatedScope(StrEnum):
    SINGLE_FILE = "single_file"
    NARROW_MULTI_FILE = "narrow_multi_file"
    BROAD_MULTI_FILE = "broad_multi_file"
    PACKAGE_WIDE = "package_wide"
    REPO_WIDE = "repo_wide"


class ChangeImpact(StrEnum):
    TESTS_ONLY = "tests_only"
    SOURCE_ONLY = "source_only"
    SOURCE_AND_TESTS = "source_and_tests"
    CONFIG_ONLY = "config_only"
    DEPENDENCY_SURFACE = "dependency_surface"
    PACKAGE_WIDE_BEHAVIOR = "package_wide_behavior"
    REPO_WIDE_BEHAVIOR = "repo_wide_behavior"


class TaskMode(StrEnum):
    FIX_FAILING_TEST = "fix_failing_test"
    FIX_LINT_OR_TYPE = "fix_lint_or_type"
    NARROW_REFACTOR = "narrow_refactor"
    DOCS_UPDATE_SAFE = "docs_update_safe"
    INSPECT_AND_PLAN = "inspect_and_plan"
    GENERAL = "general"


class RepoIndex(Contract):
    files: tuple[Path, ...]
    imports: dict[Path, tuple[Path, ...]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def relative_paths(self):
        if any(path.is_absolute() or ".." in path.parts for path in self.files):
            raise ValueError("index paths must be relative to the repository")
        known = set(self.files)
        for path, dependencies in self.imports.items():
            if path not in known or not set(dependencies) <= known:
                raise ValueError("imports must reference indexed paths")

        return self


class CandidateTarget(Contract):
    target: Path
    reason: Name


class Analysis(Contract):
    candidate_targets: tuple[CandidateTarget, ...]
    action_classes: tuple[ActionClass, ...]
    estimated_scope: EstimatedScope
    change_impact: ChangeImpact
    risk_level: PlanRiskLevel
    task_mode: TaskMode


def analyze_instruction(text: str, index: RepoIndex) -> Analysis:
    """Dérive cibles et classifications depuis l'instruction humaine et l'index du harness."""

    # classes d'action par signaux lexicaux explicites
    text = text.strip().lower()
    tokens = set(re.findall(r"[a-z0-9_./-]+", text))
    actions = set()
    signals = {
        ActionClass.READ_ONLY: {"inspect", "review", "explain", "plan", "no edits", "read-only"},
        ActionClass.CODE_EDIT: {"fix", "edit", "implement", "patch", "change", "update"},
        ActionClass.CONFIG_EDIT: {"config", "setting", "yaml", "toml", "ini", "json"},
        ActionClass.DEPENDENCY_CHANGE: {"dependency", "dependencies", "lockfile", "requirements", "pyproject"},
        ActionClass.MIGRATION: {"migration", "migrate", "schema", "alembic"},
        ActionClass.FILE_DELETE_OR_MOVE: {"rename", "move", "delete", "remove"},
        ActionClass.SHELL_READ_ONLY: {"bash", "shell", "command"},
        ActionClass.GIT_SAFE: {"git", "commit", "status", "diff"},
    }
    for action, terms in signals.items():
        if terms & tokens:
            actions.add(action)
    if {"test", "pytest", "failing"} & tokens and {"fix", "repair", "pass"} & tokens:
        actions.add(ActionClass.TEST_REPAIR)
    if any(term in text for term in ("reset --hard", "rebase", "force-push", "rm -rf")):
        actions.add(ActionClass.GIT_DESTRUCTIVE)

    # seules les cibles de l'index autoritaire sont candidates ; tri sans troncature
    candidates = []
    unique = set(index.files)
    paths = sorted(unique)
    for path in paths:
        if classify_repo_path(path) != PathClass.authoritative:
            continue
        name = path.name.lower()
        if path.as_posix().lower() in tokens or name in tokens or path.stem.lower() in tokens:
            reason = "instruction_path"
        elif "test" in tokens and ("tests" in path.parts or name.startswith("test_")):
            reason = "test_signal"
        elif {"docs", "readme"} & tokens and path.suffix == ".md":
            reason = "docs_signal"
        else:
            continue
        candidates.append(CandidateTarget(target=path, reason=reason))
    if "refactor" in tokens:
        action = ActionClass.REFACTOR_NARROW if len(candidates) <= 4 else ActionClass.REFACTOR_BROAD
        actions.add(action)
    if not actions:
        actions.add(ActionClass.READ_ONLY)

    # portée et impact restent distincts, même pour une action à risque élevé
    if actions & {ActionClass.REFACTOR_BROAD, ActionClass.GIT_DESTRUCTIVE}:
        scope = EstimatedScope.REPO_WIDE
    elif ActionClass.MIGRATION in actions:
        scope = EstimatedScope.PACKAGE_WIDE
    elif len(candidates) <= 1:
        scope = EstimatedScope.SINGLE_FILE
    elif len(candidates) <= 4:
        scope = EstimatedScope.NARROW_MULTI_FILE
    else:
        scope = EstimatedScope.BROAD_MULTI_FILE
    test_targets = [row for row in candidates if "tests" in row.target.parts or row.target.name.startswith("test_")]
    if ActionClass.DEPENDENCY_CHANGE in actions:
        impact = ChangeImpact.DEPENDENCY_SURFACE
    elif ActionClass.CONFIG_EDIT in actions:
        impact = ChangeImpact.CONFIG_ONLY
    elif scope == EstimatedScope.REPO_WIDE:
        impact = ChangeImpact.REPO_WIDE_BEHAVIOR
    elif scope == EstimatedScope.PACKAGE_WIDE:
        impact = ChangeImpact.PACKAGE_WIDE_BEHAVIOR
    elif test_targets and len(test_targets) == len(candidates):
        impact = ChangeImpact.TESTS_ONLY
    elif test_targets:
        impact = ChangeImpact.SOURCE_AND_TESTS
    else:
        impact = ChangeImpact.SOURCE_ONLY

    # risque dérivé ; aucune autorisation d'exécution ne se déduit de cette étiquette
    high = {ActionClass.DEPENDENCY_CHANGE, ActionClass.MIGRATION, ActionClass.GIT_DESTRUCTIVE, ActionClass.FILE_DELETE_OR_MOVE}
    read_only = {ActionClass.READ_ONLY, ActionClass.SHELL_READ_ONLY, ActionClass.GIT_SAFE}
    if actions & high or scope in {EstimatedScope.REPO_WIDE, EstimatedScope.PACKAGE_WIDE}:
        risk = PlanRiskLevel.HIGH
    elif actions - read_only or len(candidates) > 1:
        risk = PlanRiskLevel.MEDIUM
    else:
        risk = PlanRiskLevel.LOW

    # mode lu par la décomposition, avec priorité à une demande explicite de lecture
    if "no edits" in text or {"inspect", "plan", "read-only"} & tokens:
        mode = TaskMode.INSPECT_AND_PLAN
    elif "failing test" in text or ("fix" in tokens and "test" in tokens):
        mode = TaskMode.FIX_FAILING_TEST
    elif any(term in text for term in ("lint", "mypy", "type error", "typecheck", "ruff")):
        mode = TaskMode.FIX_LINT_OR_TYPE
    elif "refactor" in tokens:
        mode = TaskMode.NARROW_REFACTOR
    elif {"docs", "readme"} & tokens:
        mode = TaskMode.DOCS_UPDATE_SAFE
    else:
        mode = TaskMode.GENERAL

    return Analysis(
        candidate_targets=tuple(candidates),
        action_classes=tuple(sorted(actions)),
        estimated_scope=scope,
        change_impact=impact,
        risk_level=risk,
        task_mode=mode,
    )
