"""Merge upstream bot code while retaining this fork's GitHub workflows."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys


UPSTREAM_URL = os.environ.get(
    "UPSTREAM_URL", "https://github.com/chiraitori/HoYo_Code_Sender_Discord_Bot.git"
)
REMOTE = "hoyo-upstream"
UPSTREAM_REF = f"refs/remotes/{REMOTE}/main"


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args], capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if check and result.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed:\n{result.stdout}{result.stderr}")
    return result


def finish(status: str) -> None:
    revision = git("rev-parse", "HEAD").stdout.strip()
    print(f"Sync status: {status}; fork revision: {revision}")
    output = os.environ.get("GITHUB_OUTPUT")
    if output:
        with Path(output).open("a", encoding="utf-8") as stream:
            stream.write(f"status={status}\nrevision={revision}\n")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with Path(summary).open("a", encoding="utf-8") as stream:
            stream.write(f"## Upstream sync\n\nStatus: `{status}`\n\nFork commit: `{revision}`\n")


def main() -> int:
    if git("remote", "get-url", REMOTE, check=False).returncode:
        git("remote", "add", REMOTE, UPSTREAM_URL)
    else:
        git("remote", "set-url", REMOTE, UPSTREAM_URL)

    fetched = git(
        "fetch", "--no-tags", REMOTE, f"main:{UPSTREAM_REF}", check=False
    )
    if fetched.returncode:
        print(fetched.stdout + fetched.stderr)
        print("::warning::Original repository unavailable. Building the saved fork code.")
        finish("upstream-unavailable")
        return 0

    ancestor = git("merge-base", "--is-ancestor", UPSTREAM_REF, "HEAD", check=False)
    if ancestor.returncode == 0:
        finish("up-to-date")
        return 0
    if ancestor.returncode != 1:
        raise RuntimeError(ancestor.stdout + ancestor.stderr)

    before = git("rev-parse", "HEAD").stdout.strip()
    git("config", "user.name", "github-actions[bot]")
    git("config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    merged = git("merge", "--no-ff", "--no-commit", UPSTREAM_REF, check=False)

    if merged.returncode:
        conflicts = [
            path for path in git("diff", "--name-only", "--diff-filter=U", "-z").stdout.split("\0")
            if path
        ]
        other_conflicts = [path for path in conflicts if not path.startswith(".github/workflows/")]
        if not conflicts or other_conflicts:
            # A real conflict stops the build. Never overwrite fork edits or force-push.
            git("merge", "--abort", check=False)
            print(merged.stdout + merged.stderr)
            print("::error::Upstream merge conflict. Resolve it manually; no image was published.")
            return 1

    # Keep this fork's workflows, including its own build pipeline. This also
    # prevents upstream CI/deployment workflow changes from being auto-enabled.
    # The standard GITHUB_TOKEN cannot edit workflow files.
    git("restore", f"--source={before}", "--staged", "--worktree", "--", ".github/workflows")
    if git("diff", "--name-only", "--diff-filter=U").stdout.strip():
        git("merge", "--abort", check=False)
        print("::error::Unresolved merge conflict. No image was published.")
        return 1

    git("commit", "--no-edit")
    git("push", "origin", "HEAD:refs/heads/main")
    finish("updated")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as error:
        print(f"::error::{error}", file=sys.stderr)
        sys.exit(1)
