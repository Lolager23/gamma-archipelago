"""Enforce this personal project's author and committer identity."""

import re
import subprocess
import sys

EXPECTED = "Owen Welch <owenwelch@hotmail.co.uk>"


def git(*arguments: str) -> str:
    return subprocess.check_output(["git", *arguments], text=True).strip()


def check_current() -> None:
    for variable in ("GIT_AUTHOR_IDENT", "GIT_COMMITTER_IDENT"):
        identity = re.sub(r" \d+ [+-]\d{4}$", "", git("var", variable))
        if identity != EXPECTED:
            raise SystemExit(f"{variable}: expected {EXPECTED}; found {identity}")


def main() -> None:
    check_current()
    if "pre-push" in sys.argv:
        for line in sys.stdin:
            _, local, _, remote = line.split()
            if local == "0" * 40:
                continue
            # Already-published server merges can have GitHub's committer identity.
            # Check newly introduced commits, consistently for new/existing branches.
            revisions = [local, "--not", "--remotes"]
            for record in git(
                "log", "--format=%H%x09%an <%ae>%x09%cn <%ce>", *revisions
            ).splitlines():
                commit, author, committer = record.split("\t")
                if author != EXPECTED or committer != EXPECTED:
                    raise SystemExit(f"Personal identity required for outgoing commit {commit}")


if __name__ == "__main__":
    main()
