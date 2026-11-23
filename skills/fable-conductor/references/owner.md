# Owner profile

How the person you work for wants to be worked with. The conductor reads this at the start of every run and follows it without being reminded. This copy ships empty; it fills from real corrections, never from guesses.

There are two files, read in this order:

1. This file, inside the skill: the stable profile that travels with the person to every project.
2. `.claude/conductor/owner.md` in the project: what was learned since the skill was last packaged. Where the two differ, the project file is newer and wins.

## What to record, and when

Add a line to the project file when the person:

- corrects how you worked ("don't ask me that", "show me the plan first", "too long");
- states a standing preference (language, length, how decisions are put to them, what evidence they expect);
- makes a decision that will recur (which checks gate a merge, what may be pushed, what needs their approval).

Each line has the date, what they said in their own words, the scope (everywhere, or this project), and, if you are reading between the lines, your interpretation marked as yours:

```
2026-01-14  "Don't make me type commands; give me choices." Scope: everywhere. Mine: ask every decision as pick-an-option, recommendation first.
```

Do not record: a one-off instruction for the task in hand, anything about the work itself (that belongs in `lessons.md`), and personal details that are not working preferences. Never record secrets, credentials, contact details or anything about other people. If you cannot tell whether something is a standing preference or a passing remark, ask once, and carry on meanwhile.

One correction is a line. The same correction a second time means the first line was not specific enough: rewrite it.

## Using it

- Follow it silently. Do not announce that you are applying a preference.
- The project's rules and the person's words in this conversation outrank the profile. If today's request contradicts a recorded line, do what they ask today and ask whether the line should change.
- A line whose reason no longer holds is dropped, not kept out of habit. Exception: a line that restricts something risky or irreversible stays until the person lifts it.

## The person's control over it

On "what do you know about me", "show my profile" or the `profile` mode: show both files as they are, in the person's language. Change or delete any line they ask to, at once, and say which file you changed. The stable copy inside an installed skill may be read-only: then record the change in the project file (a line that overrides, or `REMOVE: <the old line>`), and fold it in at the next `evolve`.

## Folding the project file into the skill

During `evolve`, when packaging the skill **for its owner**, merge the lines from the project files into the section below: deduplicate, keep the newest wording, drop what was removed. When preparing a **public** copy, this section ships empty: a profile is personal and is never published.

## Profile

(empty)
