import os, tempfile, subprocess, shutil
from pathlib import Path

REPO = os.getenv("DOCS_REPO", "YOUR_GH_ORG/ecomate-docs")
GH = shutil.which("gh")

def open_pr(branch: str, commit_msg: str, changes: dict):
    """changes = { 'path/relative.txt': 'new content' }"""
    if not GH:
        raise RuntimeError("GitHub CLI (gh) not found. Install and `gh auth login` or set GH_TOKEN env.")
    with tempfile.TemporaryDirectory() as td:
        subprocess.run([GH, "repo", "clone", REPO, td], check=True)
        repo = Path(td)
        subprocess.run(["git", "checkout", "-b", branch], cwd=repo, check=True)
        for rel, content in changes.items():
            p = repo / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
        subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=repo, check=True)
        subprocess.run(["git", "push", "--set-upstream", "origin", branch], cwd=repo, check=True)
        subprocess.run([GH, "pr", "create", "--fill"], cwd=repo, check=True)