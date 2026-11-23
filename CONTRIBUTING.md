# Contributing

The maintainer reviews every pull request. Nothing is merged without passing checks and that review.

## What a change needs

- It comes from evidence: a pattern in a ledger or a failure someone else can reproduce. Describe the evidence in the PR.
- One rule change per PR.
- `SKILL.md` stays under 200 lines. Put detail in `references/`.
- Bump `metadata.version` in `SKILL.md` and add a matching entry at the top of `CHANGELOG.md`, with the evidence.
- The PR must not contain private project details: no project names, client names, internal paths, emails or secrets.

## Run the checks locally

```
pip install ruff pytest
ruff check .
ruff format --check .
python tools/validate.py
python tools/privacy_check.py
python -m pytest -q
```

These are the same commands CI runs.

## Releases

Pushing a tag `vX.Y.Z` runs the checks, requires the tag to equal `metadata.version`, and publishes `fable-conductor.skill`.
You can build it locally with `python tools/package.py`.
