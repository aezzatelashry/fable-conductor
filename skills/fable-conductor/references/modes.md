# Modes beyond the main loop

Read the section for the mode you are running. Each mode changes things outside the conversation only after the user has picked an option that says so.

## setup: prepare a project

Makes routing deterministic in one project and records how its checks run, so later runs do not rediscover it.

1. Show what would change: `python <skill-dir>/scripts/setup.py plan`. It installs the four pinned agents from `assets/agents/` into `.claude/agents/` and creates `.claude/conductor/lessons.md`. It never overwrites: an existing agent file with different content is kept and reported.
2. Ask the user to confirm (one question, options: install with the rules line / install without it / not now). On yes: `setup.py apply`, with `--rules` if they chose it.

   The rules line is what makes the skill start on its own. Measured on 2026-11-23 with plain Arabic requests and no command: inside a project whose rules file names the skill, it started on 3 of 3; outside any project, relying on the description alone among several hundred installed skills, on 3 of 10 runs. So recommend the rules line, and tell the user that without it they may need to name the skill.
3. Establish the baseline: find the project's test, lint and build commands from its own scripts and rules file, run the fast ones once, and write into `lessons.md` one line each for: the test command, the lint command, any build step tests need first, and any check that already fails (with the commit it failed on).
4. Follow the project's rules on committing these files. Newly installed agent types become available to the Agent tool after the files exist; if they do not appear, they will in the next session.

## audit: what is installed, and what it costs

Many plugins ship overlapping skills and session-start hooks. Every skill adds a description to the session and every session-start hook adds text to every conversation, so duplicates cost tokens before any work starts and can pull the model toward conflicting methods.

1. Run `python <skill-dir>/scripts/inventory.py` (read-only).
2. From its output build a table for the user with three groups and a reason per row:
   - **keep**: used by the user's projects, or the only source of a capability;
   - **disable**: a duplicate of something kept (same skill names in several plugins), or for a tool or domain the user's projects do not touch;
   - **your call**: plugins that impose a whole way of working (session-start hooks that tell the model to always follow their process). Two of these active together give contradictory instructions; recommend keeping at most one, and say which you would keep and why.
3. Judge "used" from evidence: the project's rules files, the agents and skills they name, and what was invoked in recent work. Say when you are guessing.
4. Do not disable or remove anything. Tell the user where plugins are turned off (the plugin or customisation settings of their Claude app; in the terminal, `/plugin`), and offer to re-run the inventory afterwards to show the difference.

The inventory counts what is on disk. Whether the app loads each description in full is not visible from the script, so present the character totals as an upper bound, not a measured cost.

## watch --dashboard: the ledger as a page

1. `python <skill-dir>/scripts/ledger.py report --json` (add `--all <dir>` for several projects).
2. Build a single-page dashboard from that JSON with the session's artifact tooling (follow its own design guidance; start from its dashboard type if it offers one): tokens by tier, first-time pass rate, the tier-and-kind table, the flags, and the latest rows. Add the last lines of `lessons.md`. Where the dashboard type takes an uploaded data file, export the `rows` as CSV and let the page compute the totals from it, so every figure traces to a row. To refresh an existing dashboard, replace its data file rather than building a new page.
3. State on the page that the conductor's own token use is not included, and the time the data was generated.
4. Artifacts are private by default. Do not publish a dashboard for a project the user has called sensitive without asking.

If no artifact tooling is available, print the text report instead and say so.

## Why the ledger is filled by hand

Checked against the Claude Code hooks documentation on 2026-11-22: a hook cannot fill the ledger reliably. `SubagentStop` receives no usage, duration or model. `PostToolUse` on the Agent tool does receive token fields, but only for a foreground agent, and they cover the agent's final request rather than its whole run; a background launch returns no usage at all. The figure worth recording is the `subagent_tokens` in the completion notification, so run agents in the background (the default) and log from the notification. An agent whose result carried no usage is logged with `--tokens 0` and a note in `--task`; zero then means "not reported". Re-check this during `evolve`, since hook inputs change between releases.

## Where the skill lives

Checked against the Claude Code skills documentation on 2026-11-22:

- Saved to the user's claude.ai account: available in the apps and in cloud sessions, synced down read-only. This is the copy that follows the user everywhere.
- In a repository's `.claude/skills/`: available to everyone working in that repository, including cloud sessions on it.
- In `~/.claude/skills/` on one machine: every project on that machine, but not cloud sessions.
- When a personal skill and a project skill share a name, the personal one wins. So after `evolve`, the user must save the new package to their account, or their older account copy will shadow a newer one committed to a repository.
- A skill uploaded to the account may only use these frontmatter keys: `name`, `description`, `license`, `compatibility`, `metadata`, `allowed-tools`. Any other key is a hard error, so hooks cannot be bundled in this skill's frontmatter.

## evolve on a schedule

A recurring task can run `evolve` and produce a proposal (a changelog entry and a packaged skill), but it must not adopt its own proposal: the user reviews and saves it. Offer this once, as a question with options (weekly / every two weeks / no). Create the scheduled task only on a yes, in a fresh session each time, with a prompt that stands alone. If the session has no scheduling tool, say so and suggest the user run `evolve` by hand.

## Working alongside other routing skills

If another installed skill assigns the roles differently (for example, a different model as the main loop with the strongest model as an occasional advisor), do not blend the two. When the session's main model is the strongest tier available, this skill's roles apply; when it is not, the main loop still plans and verifies, routes down from its own tier, and treats the stronger model as a second opinion before risky or irreversible steps only. Tell the user once that the two skills overlap and which one you are following.
