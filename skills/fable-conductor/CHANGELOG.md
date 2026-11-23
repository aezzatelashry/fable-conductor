# Changelog

## 2.2.0 (2026-11-23)

- Owner profile: `references/owner.md` (stable, ships empty) and `.claude/conductor/owner.md` per project (learned since the last packaging). The conductor reads both at the start, records corrections and standing preferences as dated lines, and shows or edits them on request (`profile` mode). A profile is folded into the owner's own package during `evolve` and is never published.
- The examples and changelog no longer name any real project.
- Not yet tried in a fresh session: whether a recorded preference is followed without a reminder.

## 2.1.0 (2026-11-23)

From measuring whether the skill starts on its own for plain requests with no command.

- Outside any project, among several hundred installed skills: the 2.0.0 description started the skill on 1 of 5 should-start requests (the English one; 0 of 4 Arabic). A reworded description, Arabic first and asking to be invoked before other process skills, reached 3 of 10 runs. Neither started it on any of the 5 requests that should not start it. Adopted the reworded description; it is still not reliable alone.
- Inside a project whose rules file names the skill: 3 of 3 plain Arabic requests started it. So `setup.py` gained `--rules`, which appends a short section to the project's `CLAUDE.md` (append only, skipped if the file already mentions the skill), and `setup` now recommends it.
- The ledger dashboard published under 2.0.0 passed its page check, with figures matching the ledger.

## 2.0.0 (2026-11-22)

Built with the skill itself: one Sonnet builder (scripts), one Sonnet researcher (documentation), both accepted first time; inventory and verification by the conductor.

- New modes: `setup` (`scripts/setup.py`, never overwrites), `audit` (`scripts/inventory.py`, read-only), `watch --dashboard`.
- `ledger.py report --all DIR` aggregates ledgers across projects; `--json` now carries `rows` and `generated_at`.
- New `references/modes.md` and `references/capabilities.md`.
- Researched and decided against a logging hook: hook inputs do not carry a subagent's whole-run usage. The reasons and the documented facts about where skills live are in `references/modes.md`.
- Guidance for working alongside another routing skill that assigns the roles differently.
- Tried for real: `inventory.py` on a real installation with several hundred skills (it found duplicated skill names and overlapping session-start hooks); `setup.py plan` on two projects; `ledger.py --all`; one dashboard published from the ledger. Not tried: `setup.py apply` outside the tests, the scheduled review, and the dashboard's rendering was not confirmed by a check report.

## 1.2.0 (2026-11-22)

Owner request: no typed commands. The skill now starts on its own for multi-piece tasks, plain phrases select the modes, and decisions are asked as pick-an-option questions. Not yet tested in a fresh session.

## 1.1.0 (2026-11-22)

From the first real run (a small UI feature in a production monorepo: one Haiku scout, one Sonnet builder, accepted first time).

- Added call modes: `plan`, `watch`, `evolve`.
- Added "establish a green baseline" before dispatch. Evidence: the web tests could not load until shared packages were built, and one unrelated test already failed in the environment; both were found before dispatch only by chance.
- Briefs: name only verified commands. Evidence: the brief asked for prettier and eslint in a repository that uses biome.
- Briefs: say how to undo. Evidence: the builder ran `git checkout` on a directory to discard formatter noise.

## 1.0.0 (2026-11-22)

First version. Conductor loop, routing table, brief and report templates, verification by risk, the Watch sub-skill, the dispatch ledger with routing flags, the evolution protocol, and optional pinned agent definitions.
