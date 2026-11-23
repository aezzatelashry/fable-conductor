# Changelog

## 2.3.0 (2026-11-23)

- **Menu.** When a session opens with something other than a concrete task, or the person asks what the skill can do, the conductor shows its modes as pick-an-option choices (`references/menu.md`), and it ends every run with next-step choices. Tried headless with two vague openings and one concrete task: the vague ones went to the menu file and looked for the question tool, the concrete one went straight to the task; the menu was not seen rendered, because the question tool is not available in a headless run.
- **A visible start line.** The conductor says once per session that it is running, with its version, and answers plainly when asked whether it is.
- **Cost estimate.** `ledger.py report --prices FILE` adds a blended cost estimate: FILE maps a model name to dollars per million tokens. The ledger keeps one total token count per dispatch, so input and output are not priced separately. Output gains `estimated_cost`, `unpriced_models` and a `cost` per tier (JSON), or an `estimated cost:` line and an `unpriced:` line (text). Without `--prices` the output is unchanged. A prices file that is missing, not JSON, not an object, or holds a non-number exits 2; keys starting with `_` are ignored. `assets/prices.example.json` shows the shape with made-up numbers; no real prices are shipped. Not verified: the estimate against a real bill.
- **Brief templates per project** (`references/briefs.md`): a brief that was accepted first time is saved for reuse.
- `setup.py --rules` now also asks for the menu at session start.
- **Measured, once.** The cost-estimate change, an issue template and a worked example were built twice from identical copies in headless sessions: by the main model alone, and by the main model using this skill with Sonnet and Haiku executors. Both results passed the same 27 acceptance checks, written beforehand. Whole-session cost as reported by the CLI: 3.19 dollars alone, 2.81 with the skill (12% less); wall time 238 s and 201 s. In the skill's run the main model was still 81% of the cost, most of it reading the session's own context. One run per arm on one task: an indication, not a rate.

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
