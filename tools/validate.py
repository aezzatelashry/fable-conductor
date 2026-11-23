"""Validate a skill directory against the rules a claude.ai skill upload expects.

Usage: python tools/validate.py [SKILL_DIR]

SKILL_DIR defaults to skills/fable-conductor. Exit 0 if every rule passes,
1 otherwise, with one line printed per failed rule.
"""

import re
import sys
from pathlib import Path

ALLOWED_KEYS = {
    "name",
    "description",
    "license",
    "compatibility",
    "metadata",
    "allowed-tools",
}
MAX_LINES = 200
MAX_DESCRIPTION = 1024
SEMVER = re.compile(r"^\d+\.\d+\.\d+$")
NAME_RE = re.compile(r"^[a-z0-9-]{1,64}$")
CHANGELOG_HEADING = re.compile(r"^##\s+(\d+\.\d+\.\d+)\b")
BACKTICK = re.compile(r"`([^`\n]+)`")
PATH_PREFIXES = ("references/", "scripts/", "assets/", "watch/")


def unquote(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] == '"':
        inner = value[1:-1]
        return inner.replace('\\"', '"').replace("\\\\", "\\")
    return value


def parse_frontmatter(lines):
    """Return (data, error). Handles top-level key: value and one nested block of indented key: value lines."""
    if not lines or lines[0].strip() != "---":
        return None, "SKILL.md does not start with a --- frontmatter delimiter"
    end = None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            end = i
            break
    if end is None:
        return None, "frontmatter is not closed by a --- line"
    data = {}
    current = None
    for raw in lines[1:end]:
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if raw[0] in " \t":
            if current is None or not isinstance(data.get(current), dict):
                return (
                    None,
                    f"unexpected indented line in frontmatter: {raw.strip()[:40]}",
                )
            key, sep, value = raw.strip().partition(":")
            if not sep:
                return None, f"malformed nested line in frontmatter: {raw.strip()[:40]}"
            data[current][key.strip()] = unquote(value)
            continue
        key, sep, value = raw.partition(":")
        if not sep:
            return None, f"malformed frontmatter line: {raw[:40]}"
        key = key.strip()
        if value.strip() == "":
            data[key] = {}
            current = key
        else:
            data[key] = unquote(value)
            current = None
    return data, None


def changelog_version(path):
    if not path.is_file():
        return None
    for line in path.read_text(encoding="utf-8").splitlines():
        m = CHANGELOG_HEADING.match(line)
        if m:
            return m.group(1)
    return None


def check(skill_dir):
    """Return a list of failure messages."""
    fails = []
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        return ["a: SKILL.md not found in " + str(skill_dir)]
    text = skill_md.read_text(encoding="utf-8")
    lines = text.splitlines()

    data, err = parse_frontmatter(lines)
    if err:
        fails.append("a: " + err)
        data = {}

    extra = sorted(set(data) - ALLOWED_KEYS)
    if extra:
        fails.append("b: frontmatter keys not allowed: " + ", ".join(extra))

    name = data.get("name")
    if not isinstance(name, str) or name != skill_dir.resolve().name:
        fails.append(f"c: name {name!r} does not equal directory name {skill_dir.resolve().name!r}")
    elif not NAME_RE.match(name):
        fails.append("c: name does not match ^[a-z0-9-]{1,64}$")

    desc = data.get("description")
    if not isinstance(desc, str) or not desc.strip():
        fails.append("d: description is missing or empty")
    else:
        if len(desc) > MAX_DESCRIPTION:
            fails.append(f"d: description is {len(desc)} characters, limit {MAX_DESCRIPTION}")
        if "<" in desc or ">" in desc:
            fails.append("d: description contains < or >")

    meta = data.get("metadata")
    version = meta.get("version") if isinstance(meta, dict) else None
    if not version or not SEMVER.match(version):
        fails.append(f"e: metadata.version is missing or not X.Y.Z (got {version!r})")
    else:
        top = changelog_version(skill_dir / "CHANGELOG.md")
        if top is None:
            fails.append("e: CHANGELOG.md missing or has no '## X.Y.Z' heading")
        elif top != version:
            fails.append(f"e: metadata.version {version} differs from CHANGELOG.md top version {top}")

    if len(lines) > MAX_LINES:
        fails.append(f"f: SKILL.md has {len(lines)} lines, limit {MAX_LINES}")

    seen = set()
    for token in BACKTICK.findall(text):
        token = token.strip()
        if token in seen or not token.startswith(PATH_PREFIXES) or "<" in token:
            continue
        seen.add(token)
        if not (skill_dir / token).exists():
            fails.append(f"g: referenced path does not exist: {token}")
    return fails


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    skill_dir = Path(argv[0] if argv else "skills/fable-conductor")
    fails = check(skill_dir)
    for line in fails:
        print("FAIL " + line)
    if fails:
        return 1
    print(f"validate passed ({skill_dir})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
