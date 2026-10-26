"""Publish the site to GitHub Pages without git push, through the GitHub CLI (gh).

    python publish.py            upload every tracked file that changed, then report the live status
    python publish.py --prune    also delete files on GitHub that are no longer tracked here
    python publish.py --dry-run  list what would change and stop

Needs: gh logged in as OpenSourceSam (check with: gh auth status). Run build.py and check.py first.
Commits are made as Sam with GitHub's private email address, so his personal email is not exposed.
If git push works on this computer, "git push" does the same job and this script is optional.
"""
from __future__ import annotations

import base64
import json
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
REPO = "OpenSourceSam/opensourcesam.github.io"
BRANCH = "main"
LIVE = "https://opensourcesam.github.io/"
AUTHOR = {"name": "Sam Cloutier", "email": "216459885+OpenSourceSam@users.noreply.github.com"}


def run(*args: str, input_text: str | None = None) -> str:
    result = subprocess.run(args, cwd=ROOT, capture_output=True, text=True, input=input_text)
    if result.returncode != 0:
        raise RuntimeError(f"{' '.join(args)} failed: {result.stderr.strip()[:300]}")
    return result.stdout


def remote_files() -> dict[str, str]:
    data = json.loads(run("gh", "api", f"repos/{REPO}/git/trees/{BRANCH}?recursive=1"))
    return {item["path"]: item["sha"] for item in data["tree"] if item["type"] == "blob"}


def local_files() -> dict[str, str]:
    paths = [p for p in run("git", "ls-files").splitlines() if p]
    shas = run("git", "hash-object", "--stdin-paths", input_text="\n".join(paths)).split()
    return dict(zip(paths, shas))


def call(method: str, path: str, body: dict) -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as tmp:
        json.dump(body, tmp)
    try:
        run("gh", "api", "-X", method, f"repos/{REPO}/contents/{path}", "--input", tmp.name)
    finally:
        Path(tmp.name).unlink(missing_ok=True)


def main() -> int:
    prune, dry = "--prune" in sys.argv, "--dry-run" in sys.argv
    print("GitHub login:", run("gh", "api", "user", "--jq", ".login").strip())
    remote, local = remote_files(), local_files()
    changed = [p for p, sha in local.items() if remote.get(p) != sha]
    gone = [p for p in remote if p not in local] if prune else []
    print(f"{len(changed)} file(s) to upload, {len(gone)} to delete.")
    for p in changed:
        print("  upload", p)
    for p in gone:
        print("  delete", p)
    if dry or not (changed or gone):
        return 0
    for p in changed:
        body = {"message": f"Update {p}", "branch": BRANCH, "author": AUTHOR, "committer": AUTHOR,
                "content": base64.b64encode((ROOT / p).read_bytes()).decode()}
        if p in remote:
            body["sha"] = remote[p]
        call("PUT", p, body)
    for p in gone:
        call("DELETE", p, {"message": f"Remove {p}", "branch": BRANCH, "sha": remote[p],
                           "author": AUTHOR, "committer": AUTHOR})
    print("Uploaded. Waiting for GitHub Pages to rebuild (up to 5 minutes)...")
    for _ in range(20):
        time.sleep(15)
        status = run("gh", "api", f"repos/{REPO}/pages/builds/latest", "--jq", ".status").strip()
        if status in ("built", "errored"):
            break
    print("Pages build:", status)
    with urllib.request.urlopen(LIVE, timeout=20) as resp:
        print("Live page answers", resp.status, LIVE)
    return 0 if status == "built" else 1


if __name__ == "__main__":
    sys.exit(main())
