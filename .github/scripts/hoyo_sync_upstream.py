"""Sync upstream, preserving fork workflows and compatible dependency fixes."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re
import subprocess
import sys


UPSTREAM_URL = os.environ.get(
    "UPSTREAM_URL", "https://github.com/chiraitori/HoYo_Code_Sender_Discord_Bot.git"
)
REMOTE = "hoyo-upstream"
UPSTREAM_REF = f"refs/remotes/{REMOTE}/main"
MISSING = object()
DEPENDENCY_GROUPS = {"dependencies", "devDependencies", "optionalDependencies", "peerDependencies"}


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args], capture_output=True, text=True, encoding="utf-8", errors="replace"
    )
    if check and result.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed:\n{result.stdout}{result.stderr}")
    return result


def read_json(revision: str, path: str) -> dict:
    return json.loads(git("show", f"{revision}:{path}").stdout)


def version(value):
    if not isinstance(value, str):
        return None
    match = re.fullmatch(r"([~^]?)(\d+)\.(\d+)\.(\d+)", value)
    return (match[1], *(int(match[i]) for i in (2, 3, 4))) if match else None


def higher_compatible(left, right):
    a, b = version(left), version(right)
    if a is None or b is None or a[:2] != b[:2] or (a[1] == 0 and a[2] != b[2]):
        raise ValueError("Dependency versions need manual resolution")
    return left if a[1:] >= b[1:] else right


def merge_json(base, ours, theirs, path=()):
    """Three-way merge; conflicting non-version edits always require a person."""
    if ours == theirs:
        return ours
    if ours == base:
        return theirs
    if theirs == base:
        return ours
    if isinstance(ours, dict) and isinstance(theirs, dict) and (base is MISSING or isinstance(base, dict)):
        base = {} if base is MISSING else base
        result = {}
        for key in dict.fromkeys([*theirs, *ours]):
            value = merge_json(base.get(key, MISSING), ours.get(key, MISSING),
                               theirs.get(key, MISSING), (*path, key))
            if value is not MISSING:
                result[key] = value
        return result
    dependency = ((len(path) == 2 and path[0] in DEPENDENCY_GROUPS)
                  or (len(path) >= 2 and path[0] == "overrides"))
    if dependency:
        try:
            chosen = higher_compatible(ours, theirs)
            # Automatic conflict resolution may advance a dependency, never undo
            # an intentional downgrade, major-version choice or range change.
            if version(base) is not None and (
                higher_compatible(base, ours) != ours or higher_compatible(base, theirs) != theirs
            ):
                raise ValueError("Dependency downgrade")
            return chosen
        except ValueError:
            pass
    raise ValueError(f"Manual package.json conflict at {'.'.join(path) or '<root>'}")


def merge_package(base: str, before: str) -> dict:
    package = merge_json(read_json(base, "package.json"), read_json(before, "package.json"),
                         read_json(UPSTREAM_REF, "package.json"))
    overrides = package.get("overrides", {})
    # A new upstream global fix must also apply inside an existing fork-specific
    # override (for example nodemon -> minimatch), instead of retaining an old pin.
    def align_scoped(rules):
        for dependency, rule in rules.items():
            if isinstance(rule, dict):
                align_scoped(rule)
            elif dependency != "." and isinstance(overrides.get(dependency), str):
                rules[dependency] = higher_compatible(rule, overrides[dependency])
    for rule in overrides.values():
        if isinstance(rule, dict):
            align_scoped(rule)
    return package


def entry(revision: str, path: str):
    listing = git("ls-tree", "-z", revision, "--", path).stdout
    return listing.split("\t", 1)[0].split() if listing else None


def dashboard_migration(base: str, before: str) -> bool:
    old, new = entry(before, "dashboard"), entry(UPSTREAM_REF, "dashboard")
    if not old or not new or old[0] != "040000" or new[0] != "160000":
        return False
    paths = set(filter(None, git("diff", "--name-only", "-z", base, before, "--", "dashboard").stdout.split("\0")))
    allowed = {"dashboard/package.json", "dashboard/package-lock.json"}
    if paths - allowed:
        raise ValueError("Dashboard contains custom code changes. Resolve the submodule migration manually.")
    if "dashboard/package.json" in paths:
        old_package = read_json(base, "dashboard/package.json")
        fork_package = read_json(before, "dashboard/package.json")
        for key in set(old_package) | set(fork_package):
            old_value, new_value = old_package.get(key, MISSING), fork_package.get(key, MISSING)
            if old_value == new_value:
                continue
            if key not in DEPENDENCY_GROUPS or not isinstance(old_value, dict) or not isinstance(new_value, dict):
                raise ValueError("Dashboard has custom configuration. Resolve its migration manually.")
            if old_value.keys() != new_value.keys():
                raise ValueError("Dashboard has custom dependencies. Resolve its migration manually.")
            for name in old_value:
                if old_value[name] != new_value[name] and higher_compatible(old_value[name], new_value[name]) != new_value[name]:
                    raise ValueError("Dashboard contains a dependency downgrade. Resolve its migration manually.")
    return True


def resolve_dashboard(before: str, conflicts: list[str]) -> None:
    expected = entry(UPSTREAM_REF, "dashboard")[2]
    for path in conflicts:
        if path.startswith("dashboard/"):
            # Only tracked legacy files are removed. Their complete versions
            # remain in the pre-merge commit; untracked local data is untouched.
            git("rm", "--force", "--", path)
        elif path.startswith("dashboard~"):
            stages = git("ls-files", "--unmerged", "--", path).stdout.splitlines()
            if entry(before, path) or not stages or any(
                row.split("\t", 1)[0].split()[:2] != ["160000", expected] for row in stages
            ):
                raise ValueError(f"Unexpected dashboard conflict: {path}")
            git("rm", "--cached", "--force", "--", path)
    git("restore", f"--source={UPSTREAM_REF}", "--staged", "--worktree", "--", "dashboard")
    print("Accepted upstream dashboard submodule migration; legacy dashboard history is retained.")


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
    if git("status", "--porcelain", "--untracked-files=no").stdout.strip():
        raise RuntimeError("Commit or stash local file changes before running the sync.")
    if git("remote", "get-url", REMOTE, check=False).returncode:
        git("remote", "add", REMOTE, UPSTREAM_URL)
    else:
        git("remote", "set-url", REMOTE, UPSTREAM_URL)

    fetched = git(
        "fetch", "--no-tags", REMOTE, f"main:{UPSTREAM_REF}", check=False
    )
    if fetched.returncode:
        print(fetched.stdout + fetched.stderr)
        print("::warning::Original repository unavailable. Checking the saved fork code.")
        finish("upstream-unavailable")
        return 0

    ancestor = git("merge-base", "--is-ancestor", UPSTREAM_REF, "HEAD", check=False)
    if ancestor.returncode == 0:
        finish("up-to-date")
        return 0
    if ancestor.returncode != 1:
        raise RuntimeError(ancestor.stdout + ancestor.stderr)

    before = git("rev-parse", "HEAD").stdout.strip()
    bases = git("merge-base", "--all", before, UPSTREAM_REF).stdout.splitlines()
    if len(bases) != 1:
        raise RuntimeError("Multiple merge bases require manual resolution.")
    package = merge_package(bases[0], before)
    migrate_dashboard = dashboard_migration(bases[0], before)
    git("config", "user.name", "github-actions[bot]")
    git("config", "user.email", "41898282+github-actions[bot]@users.noreply.github.com")
    merged = git("merge", "--no-ff", "--no-commit", UPSTREAM_REF, check=False)

    try:
        conflicts = [
            path for path in git("diff", "--name-only", "--diff-filter=U", "-z").stdout.split("\0")
            if path
        ]
        other_conflicts = [path for path in conflicts if not (
            path.startswith(".github/workflows/") or path == "package.json"
            or (migrate_dashboard and (path == "dashboard" or path.startswith(("dashboard/", "dashboard~"))))
        )]
        if other_conflicts or (merged.returncode and not conflicts):
            raise ValueError("Unrecognized upstream merge conflict: " + ", ".join(other_conflicts))
        if migrate_dashboard:
            resolve_dashboard(before, conflicts)
        Path("package.json").write_text(json.dumps(package, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        git("add", "--", "package.json")
        # The standard GITHUB_TOKEN cannot edit workflow files. Keep all fork
        # workflows, including intentional compatibility updates uploaded by its owner.
        git("restore", f"--source={before}", "--staged", "--worktree", "--", ".github/workflows")
        if git("diff", "--name-only", "--diff-filter=U").stdout.strip():
            raise ValueError("Unresolved merge conflict")
    except Exception:
        git("merge", "--abort", check=False)
        raise

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
