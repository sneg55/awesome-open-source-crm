import json
import os
import re
import sys
import urllib.request
from datetime import datetime, timezone

STALE_DAYS = 365
REPO_LINK = re.compile(r"^\s*- \[[^\]]+\]\(https://github\.com/([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)/?(?:#readme)?\)")


def fetch(slug, token):
    request = urllib.request.Request(f"https://api.github.com/repos/{slug}")
    request.add_header("Accept", "application/vnd.github+json")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(request) as response:
        return json.load(response)


def main(path):
    token = os.environ.get("GITHUB_TOKEN", "")
    now = datetime.now(timezone.utc)
    problems = []
    with open(path) as handle:
        slugs = [m.group(1) for line in handle if (m := REPO_LINK.match(line))]
    for slug in slugs:
        try:
            repo = fetch(slug, token)
        except urllib.error.HTTPError as error:
            problems.append(f"{slug}: HTTP {error.code}")
            continue
        pushed = datetime.fromisoformat(repo["pushed_at"].replace("Z", "+00:00"))
        idle_days = (now - pushed).days
        if repo["archived"]:
            problems.append(f"{slug}: archived")
        elif idle_days > STALE_DAYS:
            problems.append(f"{slug}: no push in {idle_days} days")
    print(f"checked {len(slugs)} repositories")
    for problem in problems:
        print(problem)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else "README.md"))
