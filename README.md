# fable-conductor

A Claude Code skill that runs multi-piece work as a model team. The strongest model in the session plans, writes the briefs, verifies the results and integrates them. Cheaper models execute the pieces each is good at. Every dispatch is logged, so routing improves from evidence instead of habit.

مهارة لـ Claude Code بتشغّل الشغل متعدد الأجزاء كفريق موديلات: أقوى موديل يخطط ويكتب التكليفات ويتحقق ويدمج، والموديلات الأرخص تنفّذ. كل تكليف بيتسجل، فالتوزيع بيتحسّن من الأرقام.

## What it does

| Piece of work | Goes to |
|---|---|
| A command whose output is a few lines | No model: run it directly |
| Locating code, running a long suite, summarising logs, mechanical edits | Haiku |
| Well-specified implementation, tests, ordinary review | Sonnet |
| Hard or underspecified work; review of money, data, auth, security, migrations | Opus |
| Intent, design, briefs, verification, integration | The main model |

Around that table the skill adds what makes delegation hold up in practice:

- **Self-contained briefs** with a fixed report format per role, so an executor can act without the conversation.
- **Verification by evidence.** An agent's report is treated as a claim; the conductor reads the diff and runs the decisive check itself.
- **A failure ladder.** First failure: fix the brief. Second: move up a tier. After two reworks: re-plan.
- **A dispatch ledger** (`scripts/ledger.py`) that reports tokens and first-time pass rate per model and kind of work, and flags work that looks over-routed or under-routed.
- **Watch**, an internal monitor with checkpoints for long runs.
- **Modes** for preparing a project, auditing installed skills and plugins, and updating the skill from its own ledgers.
- **An owner profile** that records how the person wants to be worked with. It ships empty and is never published.

## Install

**From a release (recommended).** Download `fable-conductor.skill` from the [Releases](../../releases) page and save it to your Claude account. It then follows you to every project.

**Into one repository.** Copy `skills/fable-conductor/` to `.claude/skills/fable-conductor/` in that repository and commit it. Everyone working there gets it.

If you have both, the copy in your account wins, so update that one when a new version comes out.

## Use

Say what you want in plain language; a command is optional.

- A request with two or more substantial pieces starts the full loop.
- "Show me the plan first" stops after the split and the routing table.
- "How much did we spend" reads the ledger.
- "Prepare this project for the conductor" installs four pinned agents and a lessons file, and offers a short rule for the project's `CLAUDE.md`.

That last rule matters. In our measurements with plain requests and no command, the skill started on 3 of 3 requests inside a project whose rules file names it, and on 3 of 10 runs outside any project, where it competed with several hundred other installed skills. Without the rule you may need to name the skill.

A worked example of one small run: [examples/small-feature](examples/small-feature/README.md).

## What is in the box

```
skills/fable-conductor/
  SKILL.md                 the loop
  references/routing.md    who does what, escalation
  references/briefs.md     brief template, report formats
  references/verify.md     verification by risk
  references/modes.md      setup, audit, dashboard, scheduling
  references/capabilities.md
  references/evolve.md     how the skill is updated
  references/owner.md      the owner profile (empty here)
  watch/WATCH.md           the monitor
  scripts/ledger.py        dispatch ledger and report
  scripts/setup.py         project setup (never overwrites)
  scripts/inventory.py     read-only inventory of skills, plugins, hooks
  assets/agents/           runner, builder, reviewer, deep-reviewer
```

The scripts use only the Python standard library. `ledger.py` and `setup.py` write only inside a project's `.claude/` directory (`setup.py --rules` also appends to the project's `CLAUDE.md`). `inventory.py` only reads.

## Limits

- It reduces errors through briefs, verification and independent review. It does not guarantee their absence, and it says what was not tested.
- The ledger counts subagent tokens. The main model's own use is visible in your usage view, not to the script.
- Hooks cannot fill the ledger reliably, so dispatches are logged by the conductor from each agent's completion notice.
- Model names and tool names change. The skill tells the conductor to check what the session actually offers.

## How this repository is controlled

- `main` is protected: changes arrive by pull request, CI must pass, and the code owner must approve.
- CI runs lint, the skill validator (`tools/validate.py`), a privacy check (`tools/privacy_check.py`) and the tests.
- A release is cut only from a tag `vX.Y.Z` that equals the version in `SKILL.md`; the workflow rebuilds the package from the tagged source.
- Every change bumps the version and adds a changelog entry that cites its evidence.

See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).

## Licence

Apache-2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE).

This is an independent project. It is not affiliated with or endorsed by Anthropic; Claude and the model names are Anthropic's.
