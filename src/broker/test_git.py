"""Le fait de dépôt, la validation des arguments, et les deux commandes `gh`."""

import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

from broker.git import PullRequest, automerge, checked_ref, checked_repo_path, checked_text
from broker.git import commit, open_pr, parse_status, preflight, repo_fact
from kernel.errors import Cause, PithosError
from kernel.facts import RepoChange, RepoFact


def run(repo, *args):
    "Commande de préparation du dépôt de test, hors du code sous test."

    return subprocess.run(["git", *args], cwd=repo, capture_output=True, text=True, check=True)


@pytest.fixture
def repo(tmp_path):
    run(tmp_path, "init", "-q", "-b", "main")
    run(tmp_path, "config", "user.email", "test@pithos.local")
    run(tmp_path, "config", "user.name", "pithos test")
    (tmp_path / "kept.py").write_text("value = 1\n")
    run(tmp_path, "add", "kept.py")
    run(tmp_path, "commit", "-qm", "socle")

    return tmp_path


class Recorder:
    "Runner injecté : enregistre chaque commande et rend la sortie scriptée pour son verbe."

    def __init__(self, outputs):
        self.outputs = outputs
        self.commands = []

    def __call__(self, command, **kwargs):
        self.commands.append(command)
        key = " ".join(command[1:3])

        return SimpleNamespace(returncode=0, stdout=self.outputs.get(key, ""), stderr="")


# --- statut porcelain ------------------------------------------------------

def test_rename_carries_both_sides():
    changes = parse_status("R  new.py\0old.py\0 M kept.py\0")
    renamed, modified = changes
    assert (renamed.status, renamed.path, renamed.origin) == ("R ", Path("new.py"), Path("old.py"))
    assert (modified.status, modified.path, modified.origin) == (" M", Path("kept.py"), None)


def test_untracked_and_spaced_paths_survive():
    changes = parse_status("?? a b/c d.py\0")
    assert [(change.status, str(change.path)) for change in changes] == [("??", "a b/c d.py")]


@pytest.mark.parametrize("raw", [
    "M kept.py\0", "MMM kept.py\0", "ZZ kept.py\0", "R \0", " M\0", "R  new.py\0",
])
def test_malformed_entry_raises(raw):
    with pytest.raises(PithosError) as failure:
        parse_status(raw)
    assert failure.value.cause is Cause.invalid_schema


# --- fait de dépôt et préflight -------------------------------------------

def test_clean_repository_has_head_and_no_change(repo):
    fact = repo_fact(repo)
    assert isinstance(fact, RepoFact)
    assert fact.complete is True
    assert len(fact.head) == 40
    assert (fact.changes, fact.diff) == ([], "")


def test_worktree_change_reaches_the_fact(repo):
    (repo / "kept.py").write_text("value = 2\n")
    fact = repo_fact(repo)
    assert [str(change.path) for change in fact.changes] == ["kept.py"]
    assert "value = 2" in fact.diff
    assert isinstance(fact.changes[0], RepoChange)
    assert fact.complete is True


def test_staged_rename_reaches_the_fact_with_both_sides(repo):
    run(repo, "mv", "kept.py", "moved.py")
    renamed = repo_fact(repo).changes[0]
    assert (str(renamed.path), str(renamed.origin)) == ("moved.py", "kept.py")


def test_unborn_repository_is_not_a_failure(tmp_path):
    run(tmp_path, "init", "-q", "-b", "main")
    (tmp_path / "draft.py").write_text("value = 1\n")
    fact = repo_fact(tmp_path)
    assert (fact.head, fact.diff) == ("", "")
    assert [str(change.path) for change in fact.changes] == ["draft.py"]
    assert fact.complete is False


def test_untracked_content_prevents_a_complete_diff_claim(repo):
    (repo / "extra.py").write_text("value = 3\n")
    assert repo_fact(repo).complete is False


@pytest.mark.parametrize("raw", [" M kept.py", " M ../escape.py\0", " M /absolute.py\0", "   kept.py\0"])
def test_truncated_or_unscoped_status_never_produces_a_fact(raw):
    with pytest.raises(PithosError) as failure:
        parse_status(raw)
    assert failure.value.cause is Cause.invalid_schema


def test_preflight_names_the_dirty_files(repo):
    (repo / "kept.py").write_text("value = 2\n")
    (repo / "extra.py").write_text("value = 3\n")
    with pytest.raises(PithosError) as failure:
        preflight(repo)
    assert failure.value.cause is Cause.invariant_failed
    assert "kept.py" in failure.value.detail and "extra.py" in failure.value.detail


def test_preflight_passes_on_a_clean_repository(repo):
    assert preflight(repo) is None


# --- commit borné aux chemins désignés ------------------------------------

def test_commit_publishes_only_the_designated_paths(repo):
    (repo / "wanted.py").write_text("value = 4\n")
    (repo / "unwanted.py").write_text("value = 5\n")
    (repo / "kept.py").write_text("value = 6\n")
    sha = commit(repo, [Path("wanted.py")], "broker: chemin désigné")
    listed = run(repo, "show", "--name-only", "--format=", "HEAD").stdout.split()
    assert listed == ["wanted.py"]
    assert sha == repo_fact(repo).head
    assert {str(change.path) for change in repo_fact(repo).changes} == {"unwanted.py", "kept.py"}


@pytest.mark.parametrize("path", ["../escape.py", "-force.py", "sub/../../escape.py"])
def test_commit_refuses_a_path_outside_the_repository(repo, path):
    with pytest.raises(PithosError) as failure:
        commit(repo, [Path(path)], "broker: injection")
    assert failure.value.cause is Cause.invalid_path


def test_commit_refuses_an_empty_message(repo):
    with pytest.raises(PithosError):
        commit(repo, [Path("kept.py")], "   ")


# --- validation des arguments ---------------------------------------------

def test_checked_repo_path_renders_a_relative_posix_path(repo):
    assert checked_repo_path(repo / "sub" / "leaf.py", repo) == "sub/leaf.py"


@pytest.mark.parametrize("ref", [
    "--upload-pack=evil", "-b", "feature..main", "release.lock", "", "a b", "x;rm -rf /",
])
def test_checked_ref_refuses_anything_but_a_name(ref):
    with pytest.raises(PithosError) as failure:
        checked_ref(ref)
    assert failure.value.cause is Cause.invalid_symbol


def test_checked_ref_accepts_a_plain_branch():
    assert checked_ref("pithos/mission-3") == "pithos/mission-3"


@pytest.mark.parametrize("text", ["", "   ", "body\0injected"])
def test_checked_text_refuses_empty_or_nul(text):
    with pytest.raises(PithosError):
        checked_text(text, "body")


# --- gh : ouverture de PR et auto-merge -----------------------------------

def test_open_pr_reads_its_identity_back_from_the_host(repo):
    view = '{"number": 12, "url": "https://x/pr/12", "headRefName": "work", "headRefOid": "abc123"}'
    recorder = Recorder({"pr view": view})
    pull = open_pr(repo, "work", "titre de la pr\n\ncorps", runner=recorder)
    created = recorder.commands[0]
    assert created[:5] == ["gh", "pr", "create", "--head", "work"]
    assert "titre de la pr" in created
    assert (pull.number, pull.url, pull.branch, pull.head_sha) == (12, "https://x/pr/12", "work", "abc123")


def test_open_pr_refuses_an_injected_branch(repo):
    recorder = Recorder({})
    with pytest.raises(PithosError):
        open_pr(repo, "--upload-pack=evil", "titre", runner=recorder)
    assert recorder.commands == []


def pull_request(repo):
    return PullRequest(repo=repo, number=12, url="https://x/pr/12", branch="work", head_sha="abc123")


def test_automerge_runs_only_on_a_green_rollup(repo):
    green = '{"statusCheckRollup": [{"conclusion": "SUCCESS"}, {"conclusion": "SUCCESS"}]}'
    recorder = Recorder({"pr view": green})
    automerge(pull_request(repo), runner=recorder)
    assert recorder.commands[-1] == ["gh", "pr", "merge", "12", "--auto", "--squash"]


@pytest.mark.parametrize("rollup", [
    '{"statusCheckRollup": [{"conclusion": "SUCCESS"}, {"conclusion": "FAILURE"}]}',
    '{"statusCheckRollup": [{"state": "PENDING"}]}',
    '{"statusCheckRollup": []}',
    '{}',
])
def test_automerge_refuses_anything_but_green(repo, rollup):
    recorder = Recorder({"pr view": rollup})
    with pytest.raises(PithosError) as failure:
        automerge(pull_request(repo), runner=recorder)
    assert failure.value.cause is Cause.invariant_failed
    assert [command for command in recorder.commands if "merge" in command] == []


def test_gh_invalid_json_is_a_schema_error(repo):
    recorder = Recorder({"pr view": "not json"})
    with pytest.raises(PithosError) as failure:
        automerge(pull_request(repo), runner=recorder)
    assert failure.value.cause is Cause.invalid_schema


@pytest.mark.parametrize("target", [Path("/campaign/tool.py"), Path("/elsewhere/tool.py")])
def test_double_scopes_absolute_file_facts(double, kernel_double, target):
    memory = double("broker")
    fact = kernel_double.file_fact(path=target)
    if target.is_relative_to(Path("/campaign")):
        memory.agree_with(fact, repo=Path("/campaign"))
        observed = memory.repo_fact(Path("/campaign"))
        assert observed.changes[0].path == Path("tool.py")
        assert observed.complete is False
    else:
        with pytest.raises(ValueError):
            memory.agree_with(fact, repo=Path("/campaign"))
        assert memory.repo_fact(Path("/campaign")).changes == []
