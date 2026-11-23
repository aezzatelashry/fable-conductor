import subprocess
import sys
import zipfile
from pathlib import Path

TOOLS = Path(__file__).resolve().parent
VALIDATE = str(TOOLS / "validate.py")
PRIVACY = str(TOOLS / "privacy_check.py")
PACKAGE = str(TOOLS / "package.py")


def run(script, *args, cwd=None):
    return subprocess.run(
        [sys.executable, script, *map(str, args)],
        capture_output=True,
        text=True,
        check=False,
        cwd=cwd,
    )


def make_skill(
    tmp_path,
    name="demo-skill",
    fm=None,
    body="Body.\n",
    version="1.0.0",
    changelog=None,
):
    d = tmp_path / name
    d.mkdir()
    if fm is None:
        fm = f'name: {name}\ndescription: "Does a demo thing."\nmetadata:\n  version: "{version}"\n'
    (d / "SKILL.md").write_text(f"---\n{fm}---\n\n{body}", encoding="utf-8")
    (d / "CHANGELOG.md").write_text(
        changelog or "# Changelog\n\n## 1.0.0 (2026-01-01)\n\n- first\n",
        encoding="utf-8",
    )
    return d


def test_valid_skill_passes(tmp_path):
    r = run(VALIDATE, make_skill(tmp_path))
    assert r.returncode == 0, r.stdout
    assert "passed" in r.stdout


def test_rule_a_no_frontmatter(tmp_path):
    d = make_skill(tmp_path)
    (d / "SKILL.md").write_text("# no frontmatter\n", encoding="utf-8")
    r = run(VALIDATE, d)
    assert r.returncode == 1 and "FAIL a:" in r.stdout


def test_rule_a_missing_file(tmp_path):
    d = tmp_path / "empty-skill"
    d.mkdir()
    r = run(VALIDATE, d)
    assert r.returncode == 1 and "FAIL a:" in r.stdout


def test_rule_b_extra_key(tmp_path):
    fm = 'name: demo-skill\ndescription: "x"\nauthor: someone\nmetadata:\n  version: "1.0.0"\n'
    r = run(VALIDATE, make_skill(tmp_path, fm=fm))
    assert r.returncode == 1 and "FAIL b:" in r.stdout and "author" in r.stdout


def test_rule_c_name_mismatch(tmp_path):
    fm = 'name: other-name\ndescription: "x"\nmetadata:\n  version: "1.0.0"\n'
    r = run(VALIDATE, make_skill(tmp_path, fm=fm))
    assert r.returncode == 1 and "FAIL c:" in r.stdout


def test_rule_c_bad_name_pattern(tmp_path):
    fm = 'name: Demo_Skill\ndescription: "x"\nmetadata:\n  version: "1.0.0"\n'
    r = run(VALIDATE, make_skill(tmp_path, name="Demo_Skill", fm=fm))
    assert r.returncode == 1 and "FAIL c:" in r.stdout


def test_rule_d_empty_description(tmp_path):
    fm = 'name: demo-skill\ndescription: ""\nmetadata:\n  version: "1.0.0"\n'
    r = run(VALIDATE, make_skill(tmp_path, fm=fm))
    assert r.returncode == 1 and "FAIL d:" in r.stdout


def test_rule_d_too_long(tmp_path):
    fm = f'name: demo-skill\ndescription: "{"x" * 1025}"\nmetadata:\n  version: "1.0.0"\n'
    r = run(VALIDATE, make_skill(tmp_path, fm=fm))
    assert r.returncode == 1 and "FAIL d:" in r.stdout and "1025" in r.stdout


def test_rule_d_angle_brackets(tmp_path):
    fm = 'name: demo-skill\ndescription: "use <b> here"\nmetadata:\n  version: "1.0.0"\n'
    r = run(VALIDATE, make_skill(tmp_path, fm=fm))
    assert r.returncode == 1 and "FAIL d:" in r.stdout


def test_rule_e_version_not_semver(tmp_path):
    r = run(VALIDATE, make_skill(tmp_path, version="1.0"))
    assert r.returncode == 1 and "FAIL e:" in r.stdout


def test_rule_e_changelog_mismatch(tmp_path):
    r = run(VALIDATE, make_skill(tmp_path, version="1.1.0"))
    assert r.returncode == 1 and "FAIL e:" in r.stdout


def test_rule_f_too_many_lines(tmp_path):
    r = run(VALIDATE, make_skill(tmp_path, body="line\n" * 200))
    assert r.returncode == 1 and "FAIL f:" in r.stdout


def test_rule_g_missing_reference(tmp_path):
    body = "See `references/real.md`, `references/missing.md` and `scripts/<name>.py`.\n"
    d = make_skill(tmp_path, body=body)
    (d / "references").mkdir()
    (d / "references" / "real.md").write_text("x\n", encoding="utf-8")
    r = run(VALIDATE, d)
    assert r.returncode == 1
    assert "references/missing.md" in r.stdout
    assert "references/real.md" not in r.stdout
    assert "<name>" not in r.stdout


def test_privacy_clean_and_exceptions(tmp_path):
    at = "@"
    (tmp_path / "ok.md").write_text(
        f"a{at}users.noreply.github.com b{at}anthropic.com c{at}example.com\n"
        "path /home/user/x and <skill-dir>/scripts and actions/checkout@v4\n",
        encoding="utf-8",
    )
    r = run(PRIVACY, tmp_path)
    assert r.returncode == 0, r.stdout
    assert "privacy check passed (1 files)" in r.stdout


def test_privacy_catches_email_and_hides_line(tmp_path):
    secret = "jane.roe" + "@" + "corp-mail.org"
    (tmp_path / "a.txt").write_text(f"line one\ncontact {secret} please\n", encoding="utf-8")
    r = run(PRIVACY, tmp_path)
    assert r.returncode == 1
    assert "a.txt:2 email" in r.stdout
    assert secret not in r.stdout + r.stderr
    assert "contact" not in r.stdout + r.stderr


def test_privacy_catches_home_paths(tmp_path):
    (tmp_path / "b.txt").write_text(
        "/home/" + "alice/proj\n" + "/Users/" + "bob/x\n" + "C:\\Users\\" + "carol\\x\n",
        encoding="utf-8",
    )
    r = run(PRIVACY, tmp_path)
    assert r.returncode == 1
    assert r.stdout.count("home-path") == 3
    assert "alice" not in r.stdout and "bob" not in r.stdout and "carol" not in r.stdout


def test_privacy_denylist(tmp_path):
    word = "secretproj" + "name"
    (tmp_path / ".privacy-denylist").write_text(f"# comment\n\n{word}\\d*\n", encoding="utf-8")
    (tmp_path / "c.txt").write_text(f"we call it {word}42 internally\n", encoding="utf-8")
    r = run(PRIVACY, tmp_path)
    assert r.returncode == 1
    assert "c.txt:1 denylist" in r.stdout
    assert word not in r.stdout
    assert ".privacy-denylist:" not in r.stdout


def test_privacy_skips_git_dir(tmp_path):
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text("x" + "@" + "corp-mail.org\n", encoding="utf-8")
    (tmp_path / "d.txt").write_text("fine\n", encoding="utf-8")
    r = run(PRIVACY, tmp_path)
    assert r.returncode == 0, r.stdout


def test_package_archive(tmp_path):
    d = make_skill(tmp_path)
    (d / "scripts").mkdir()
    (d / "scripts" / "tool.py").write_text("x = 1\n", encoding="utf-8")
    (d / "scripts" / "test_tool.py").write_text("def test_x(): pass\n", encoding="utf-8")
    (d / "scripts" / "__pycache__").mkdir()
    (d / "scripts" / "__pycache__" / "tool.pyc").write_bytes(b"\0")
    out = tmp_path / "out.skill"
    r = run(PACKAGE, d, out)
    assert r.returncode == 0, r.stderr
    names = zipfile.ZipFile(out).namelist()
    assert "demo-skill/SKILL.md" in names
    assert "demo-skill/scripts/tool.py" in names
    assert not any("test_" in n or "__pycache__" in n for n in names)
    assert all(n.startswith("demo-skill/") for n in names)
