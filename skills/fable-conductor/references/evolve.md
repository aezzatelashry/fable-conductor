# Keeping the skill current

The skill improves from evidence, at two levels. Keep them separate: most lessons are about one project and do not belong in a skill used everywhere.

## Level 1: the project (every run)

Two small files in the project, under `.claude/conductor/`:

- `ledger.jsonl`: one line per dispatch, written by `scripts/ledger.py add`.
- `lessons.md`: routing lessons specific to this project. One line each, dated, with the evidence. Keep it under about 40 lines; when it grows, merge duplicates and drop lessons the ledger no longer supports.

Read `lessons.md` at the start of a run; update it at the end. Commit both with the work unless the project's rules say otherwise (in a cloud session, uncommitted files are lost when the container goes).

Example lessons:

```
2026-11-22  Haiku runner drops the skipped count on the full suite; use Sonnet as runner here. (3 mismatches in ledger)
2026-11-22  RTL/i18n review: Sonnet reviewer passes first time; no Opus needed. (5/5 pass)
```

## Level 2: the skill (on request, on flags, or on a model change)

Triggers: the user asks to update the skill; `ledger.py report` shows flags that repeat across projects; the session offers a model or agent option this skill does not mention; a rule here was wrong in practice.

1. **Gather.** Run `ledger.py report` in each project available and read each `lessons.md`. Note which patterns appear in more than one project, or follow from how the models behave rather than from one codebase.
2. **Check the roster.** Look at the Agent tool's `model` options and the agent types listed in the session. For anything about models, limits or pricing, read current documentation; do not write figures from memory.
3. **Decide the change.** Only generalisable lessons go into the skill. Prefer changing a rule and explaining why over adding a new rule; remove rules that no longer earn their place. `SKILL.md` stays under 200 lines.
4. **Edit a copy.** Installed skills may be read-only: copy the skill folder to a working directory and edit there. Keep the `name` unchanged.
5. **Record.** Bump `metadata.version` in `SKILL.md` (patch for wording, minor for a rule change, major for a change to the loop) and add an entry to `CHANGELOG.md` with the date, the change and the evidence behind it.
6. **Check against the founding requirements** in `references/genesis-prompt.md`. A change that breaks one of them needs the user's explicit agreement.
7. **Validate and test.** Run the skill-creator validator and packager if available. Dry-run the changed part: give an executor-tier agent the skill and a realistic task, ask for its routing plan, and check the plan is what you intended.
8. **Mind the two audiences.** The owner's own package carries their profile (`references/owner.md`, merged from the project files). A public copy carries the empty template and no project names, paths or figures from the owner's work; where the repository has a privacy check, run it before anything is pushed.
9. **Hand over.** Show the user the changelog entry and the diff in plain words, then deliver the packaged `.skill` for them to save. The update takes effect only once they do; say so.

Do not rewrite the skill from one bad run. One failure is a lesson for `lessons.md`; a pattern is a reason to change the skill.
