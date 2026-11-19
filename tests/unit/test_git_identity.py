"""Check the real hook against unpublished work and already-fetched server history."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "tools/check_git_identity.py"
PERSONAL = {
    "GIT_AUTHOR_NAME": "Owen Welch",
    "GIT_AUTHOR_EMAIL": "owenwelch@hotmail.co.uk",
    "GIT_COMMITTER_NAME": "Owen Welch",
    "GIT_COMMITTER_EMAIL": "owenwelch@hotmail.co.uk",
}


def git(root, *arguments, identity=None):
    # These empty commits are test fixtures, not changes in a project checkout.
    return subprocess.check_output(
        [
            "git",
            "-C",
            str(root),
            "-c",
            "core.hooksPath=" + str(root / "no-hooks"),
            "-c",
            "commit.gpgSign=false",
            *arguments,
        ],
        env={**os.environ, **PERSONAL, **(identity or {})},
        text=True,
    ).strip()


def commit(root, *, foreign=False):
    identity = {"GIT_COMMITTER_NAME": "GitHub", "GIT_COMMITTER_EMAIL": "noreply@github.com"}
    git(root, "commit", "--allow-empty", "-qm", "fixture", identity=identity if foreign else None)
    return git(root, "rev-parse", "HEAD")


def check(root, local, remote):
    return subprocess.run(
        [sys.executable, str(SCRIPT), "pre-push"],
        cwd=root,
        input=f"refs/heads/pr {local} refs/heads/pr {remote}\n",
        env={**os.environ, **PERSONAL},
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize("new_branch", [False, True])
def test_already_published_server_merge_is_not_mistaken_for_new_foreign_work(tmp_path, new_branch):
    git(tmp_path, "init", "-q")
    original = commit(tmp_path)
    published = commit(tmp_path, foreign=True)
    git(tmp_path, "update-ref", "refs/remotes/origin/main", published)
    local = commit(tmp_path)
    result = check(tmp_path, local, "0" * 40 if new_branch else original)
    assert result.returncode == 0, result.stderr


@pytest.mark.parametrize("new_branch", [False, True])
def test_unpublished_foreign_committer_remains_rejected(tmp_path, new_branch):
    git(tmp_path, "init", "-q")
    original = commit(tmp_path)
    git(tmp_path, "update-ref", "refs/remotes/origin/main", original)
    local = commit(tmp_path, foreign=True)
    result = check(tmp_path, local, "0" * 40 if new_branch else original)
    assert result.returncode != 0
    assert "Personal identity required" in result.stderr
