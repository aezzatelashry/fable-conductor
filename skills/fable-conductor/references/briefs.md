# Briefs

The executor sees only the brief. Anything you know and did not write down, it does not know. Write for a capable colleague who has never seen this conversation: full sentences, real paths, no labels you invented along the way.

Keep briefs lean by pointing at material (`docs/spec/users.md §3`, `services/api/src/users/import.ts:40-112`) instead of pasting it. Spend the words on what is not obvious from the code: the intent, the trap, the boundary.

## Template

```
GOAL
One or two sentences: what this piece is for and what "done" looks like.

WHERE
Directory or worktree, branch, base commit. What you may read. What you must not touch.

PROBLEM / TASK
What is wrong or missing, with evidence (file:line, failing output, the user-visible symptom).

INTENDED DESIGN
The approach I have decided on. Verify it against the code first. If it does not fit,
stop and tell me why instead of forcing it or inventing a different design.

OUT OF SCOPE
Files other agents are changing. Decisions that are not yours. Things that look
related but must be left alone.

TESTS
What must fail before the change and pass after. Which commands to run.
Do not weaken, skip or delete a test to get green.

SHARED RESOURCES
Locks, ports, databases, containers: the exact command to take and release them.

PROJECT RULES
Read <path to CLAUDE.md> first. Commit style: <style>.

REPORT (exactly this, nothing else)
<the report format for the role, below>
```

Two habits that prevent the commonest brief faults:

- **Name only commands you have run or read in the project's own scripts.** A brief that says "run eslint" in a repository that uses another linter sends the executor chasing a tool that is not there. If you do not know the command, say "use the project's lint script, see package.json" instead of guessing.
- **Say how to undo.** Executors reach for `git checkout`, `restore` or `stash` to discard a mistake, which also discards anything else in the tree. Tell them to back up and restore by file copy, and never to run a git command that throws work away.

Drop a section only when it truly does not apply; write "none" rather than omitting OUT OF SCOPE, since that is the one executors most often guess wrong.

## Report formats

A fixed, short format keeps the result cheap to read and easy to check. Ask for raw output where you will verify it, not a paraphrase.

**Scout (Haiku / Explore)**
```
ANSWER: one or two sentences
EVIDENCE: file:line - what is there   (one line each, max 15)
NOT FOUND: what you looked for and did not find
```

**Runner (Haiku)**
```
COMMAND: exactly what ran
EXIT: code
COUNTS: files passed/failed/skipped/total, tests passed/failed/skipped/total
TAIL: last 30 lines, verbatim
```
A runner never edits anything and never interprets a failure.

**Investigator (Sonnet / Opus)**
```
ROOT CAUSE: one or two sentences, or "not established"
EVIDENCE: file:line and the output or reproduction that shows it
RULED OUT: candidates checked and why they are not the cause
REPRODUCTION: the command or test that triggers it
SUGGESTED FIX: brief, for the conductor to decide on
```
An investigator changes nothing except to add a failing test that reproduces the bug. In its brief, replace INTENDED DESIGN with the candidate causes you already suspect.

**Builder (Sonnet / Opus)**
```
STATUS: done | blocked | design-does-not-fit
CHANGED: file - one line each
COMMIT: sha and message
TESTS: command, counts, last 15 lines verbatim
DEVIATIONS: anything done differently from the brief, and why
NOT DONE / NOT TESTED: explicit list, or "none"
GIT STATUS: output of git status --short
```

**Reviewer (Sonnet / Opus)**
```
VERDICT: approve | changes-required
FINDINGS: severity - file:line - defect - concrete failing scenario   (most severe first)
CHECKED AND FOUND SOUND: what you examined that is fine
NOT EXAMINED: what you did not look at
```
Reviewers are read-only. Give them the diff range and the spec, one lens each, and never your own opinion of the change.

## Reusing a brief that worked

When a brief for a recurring kind of work in a project (a UI change, an endpoint, a migration) is accepted first time, save it as a template in `.claude/conductor/briefs/<kind>.md` with the task-specific parts replaced by placeholders. It already holds the project's real commands, paths and traps, which is where most brief faults come from. Start from the template next time, and update it when a run shows it was missing something.

## Small examples

A weak brief: "Fix the import bug in the users module and add tests."

The same brief, usable: "In `src/users/import.ts:71` a row with an empty `email` is inserted with `''` instead of being rejected, so two such rows collide on the unique index and the whole batch rolls back (failing output: `reports/import-fail.txt`). Reject the row with error code `USER_EMAIL_REQUIRED` and continue the batch. Do not change the CSV parser in `src/csv`; another agent is editing it. Add a test with one valid and two empty-email rows: expect one insert and two row errors. Run `npm test -- users/import`."
