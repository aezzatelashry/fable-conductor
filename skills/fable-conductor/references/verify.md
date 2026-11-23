# Verification

Delegation moves the work to cheaper models; it does not move the responsibility. What reaches the user is yours. Verification is where the quality comes from, so it is the last place to economise, but it can still be done cheaply: check the decisive evidence, not everything.

## Checking a report (every time)

1. **Raw evidence.** Run the decisive command yourself, or read the log or exit file the agent produced. If a long suite is needed, a Haiku runner can run it and return the verbatim tail; the counts in that tail are evidence, the builder's summary is not.
2. **Counts reconcile.** passed + failed + skipped = total, for files and for tests. A gap means a worker crashed or a file never loaded, whatever the summary says.
3. **Diff matches the brief.** `git diff --stat` first: are the touched files the expected ones? Then read the parts that carry the logic. Look for scope creep, deleted or weakened tests, silenced errors, and TODOs standing in for work.
4. **State is clean.** The commit named is the branch head; `git status` is clean; nothing was left in a shared resource (containers, locks, temp files).
5. **"Nothing found" is a claim too.** When a scout or reviewer reports nothing, check that it looked in the right place before you skip the next step.

## Review depth by risk

| Change | Review |
|---|---|
| Docs, copy, small isolated edits | Your own read of the diff |
| Ordinary features, UI, refactors within a module | One Sonnet reviewer, one lens; add a second lens only if the first finds real problems |
| Money and ledger math, data integrity, permissions and auth, security, migrations and backfills, concurrency and state machines | One Opus reviewer per risky branch, then your own read of its findings against the code |
| Irreversible or outward-facing actions (delete, send, publish, deploy) | Stop and get the user's go-ahead; review does not replace consent |

A reviewer that is handed your conclusion confirms it. Give it the diff range, the spec or brief, and one lens.

## Handling findings

- Verify each finding against the code before acting; reviewers are also wrong sometimes.
- Confirmed findings go back to the original builder by message, with the reviewer's failing scenario attached, so it fixes with its context intact.
- A fix for a serious finding gets re-reviewed. A cosmetic one does not.

## Before saying "done"

- The project's full check has run and passed, in the way the project requires it to be run.
- Each acceptance item from step 1 has its evidence, or is listed as not done.
- What was not tested is stated as not tested.
- Shortcuts and risks you noticed are reported, not buried.

Do not promise the absence of defects. Say what was verified, how, and what remains unknown; that is what makes the result trustworthy.
