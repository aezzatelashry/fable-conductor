"""Fail if a tree contains text that should not be in a public repository.

Usage: python tools/privacy_check.py [ROOT]

ROOT defaults to the current directory. Scans every text file except .git/,
virtualenv and cache directories, and this script. Rules:

  email      an email address, except @users.noreply.github.com, @anthropic.com, @example.com
  home-path  /home/<name>/, /Users/<name>/ or C:\\Users\\<name>\\ (the placeholder /home/user/ is allowed)
  denylist   a regex listed one per line in ROOT/.privacy-denylist (blank lines and # lines ignored)

Output names file:line and the rule only; it never prints the offending text.
Exit 0 if clean, 1 otherwise.
"""

import re
import sys
from pathlib import Path

SKIP_DIRS = {".git", ".venv", "__pycache__", ".pytest_cache", ".ruff_cache"}
DENYLIST_NAME = ".privacy-denylist"
ALLOWED_EMAIL_DOMAINS = ("users.noreply.github.com", "anthropic.com", "example.com")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@([A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,})")
HOME_PATH = re.compile(r"(?:/home/|/Users/)([^/\s\\]+)/|[A-Za-z]:\\Users\\([^\\\s/]+)\\")


def load_denylist(root):
    path = root / DENYLIST_NAME
    patterns = []
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                patterns.append(re.compile(line))
    return patterns


def scan_line(line, denylist):
    rules = []
    for m in EMAIL.finditer(line):
        domain = m.group(1).lower()
        if not any(domain == d or domain.endswith("." + d) for d in ALLOWED_EMAIL_DOMAINS):
            rules.append("email")
            break
    for m in HOME_PATH.finditer(line):
        name = m.group(1) or m.group(2)
        if name == "user" and m.group(0).startswith("/home/"):
            continue
        if "<" in name:
            continue
        rules.append("home-path")
        break
    for pat in denylist:
        if pat.search(line):
            rules.append("denylist")
            break
    return rules


def text_files(root, self_path):
    for path in sorted(root.rglob("*")):
        rel_parts = path.relative_to(root).parts
        if any(part in SKIP_DIRS for part in rel_parts[:-1]) or not path.is_file():
            continue
        if path.resolve() == self_path or (path.name == DENYLIST_NAME and len(rel_parts) == 1):
            continue
        try:
            data = path.read_bytes()
        except OSError:
            continue
        if b"\0" in data[:8192]:
            continue
        try:
            yield path, data.decode("utf-8")
        except UnicodeDecodeError:
            continue


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    root = Path(argv[0] if argv else ".").resolve()
    denylist = load_denylist(root)
    self_path = Path(__file__).resolve()
    findings = []
    count = 0
    for path, text in text_files(root, self_path):
        count += 1
        for n, line in enumerate(text.splitlines(), 1):
            for rule in scan_line(line, denylist):
                findings.append(f"{path.relative_to(root).as_posix()}:{n} {rule}")
    if findings:
        for item in findings:
            print(item)
        print(f"privacy check failed ({len(findings)} findings)")
        return 1
    print(f"privacy check passed ({count} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
