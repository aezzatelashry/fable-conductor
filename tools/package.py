"""Build the .skill archive (a zip) from a skill directory.

Usage: python tools/package.py [SKILL_DIR] [OUT_FILE]

SKILL_DIR defaults to skills/fable-conductor, OUT_FILE to fable-conductor.skill.
The archive has one top-level folder named after the skill directory. Caches
and test_*.py files are left out. File order and timestamps are fixed so the
same input gives the same archive.
"""

import sys
import zipfile
from pathlib import Path

EXCLUDED_DIRS = {"__pycache__", ".pytest_cache", ".ruff_cache"}
FIXED_TIME = (2020, 1, 1, 0, 0, 0)


def included(path, skill_dir):
    parts = path.relative_to(skill_dir).parts
    if any(p in EXCLUDED_DIRS for p in parts):
        return False
    return not (path.name.startswith("test_") and path.suffix == ".py")


def build(skill_dir, out_file):
    skill_dir = skill_dir.resolve()
    top = skill_dir.name
    files = [p for p in sorted(skill_dir.rglob("*")) if p.is_file() and included(p, skill_dir)]
    with zipfile.ZipFile(out_file, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in files:
            info = zipfile.ZipInfo(f"{top}/{path.relative_to(skill_dir).as_posix()}", FIXED_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (path.stat().st_mode & 0o777) << 16
            zf.writestr(info, path.read_bytes())
    return len(files)


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    skill_dir = Path(argv[0] if argv else "skills/fable-conductor")
    out_file = Path(argv[1] if len(argv) > 1 else "fable-conductor.skill")
    if not (skill_dir / "SKILL.md").is_file():
        print(f"no SKILL.md in {skill_dir}", file=sys.stderr)
        return 1
    n = build(skill_dir, out_file)
    print(f"wrote {out_file} ({n} files)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
