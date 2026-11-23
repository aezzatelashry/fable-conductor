# Capabilities by stage

What the environment already offers for each stage of the loop, so the conductor uses it instead of rebuilding it or leaving it idle. This is a map, not a guarantee: what exists differs between the terminal, the desktop app and cloud sessions, and changes between releases. Before relying on a row, check that the tool, skill or agent type is actually listed in this session. Update this file during `evolve`.

Last checked against a live session: 2026-11-22 (Claude Code cloud session).

| Stage | Capability | Use it for | Note |
|---|---|---|---|
| Understand | Explore agent (read-only search) | "where does X live" across many files | Give it a precise question and ask for `file:line`; run it on the cheapest tier |
| Understand | The project's rules and memory files (`CLAUDE.md`, progress or handoff docs) | conventions, what is forbidden, where work stopped | These outrank the skill |
| Decide | Plan mode | getting the user's agreement on an approach before any change | It waits for a person: never use it for an unattended child session |
| Decide | Structured questions (pick an option) | every decision that is the user's | Recommendation first; the user should not have to type |
| Split | Git worktrees, or worktree isolation on the Agent tool | parallel builders that must not collide | One worktree per builder; clean up after merging |
| Route | The Agent tool's `model` option and agent definitions with pinned `model` and `effort` | choosing the tier per piece | An agent without a pinned effort runs at the session's effort |
| Route | Project or plugin specialist agents | work that needs the project's conventions | Pick the type by speciality, the model by difficulty |
| Dispatch | Background agents and background commands | anything slow | You are notified on completion; do not poll |
| Dispatch | Messaging a running or finished agent | corrections and follow-ups | Keeps the context already paid for |
| Verify | The built-in code review, security review and simplify skills | an independent pass on a diff | A review skill run at its highest level starts many agents: use that only when asked |
| Verify | A browser (where installed) | seeing a UI change render | Only when the app can run in the environment |
| Integrate | Pull requests and PR activity subscriptions | handing work over and following CI and reviews | Pushing and merging follow the project's rules and the user's consent |
| Report | Artifacts | a dashboard, a report the user will share | Private by default |
| Record | The ledger and `lessons.md` | improving routing from evidence | `scripts/ledger.py` |
| Economise | Compacting the conversation at a natural break; a fresh session per stage | long sessions, where every turn resends the whole conversation | Save state first |
| Economise | The usage view | the user's real spend, including the conductor's own | The ledger cannot see the conductor's tokens |
| Repeat | Scheduled tasks; a self-paced loop | recurring reviews, periodic checks | Create only what the user asked for |
| Scale | Scripted multi-agent workflows | very large fan-outs | Only when the user has explicitly opted in; keep cheap stages on cheap tiers |
| Maintain | The inventory script | finding duplicate skills and session-start hooks | `scripts/inventory.py`, read-only |
