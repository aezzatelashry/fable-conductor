# Routing

The aim is the cheapest tier that gets the piece right the first time. A cheap model that needs two reworks costs more than the tier above it, and a strong model on mechanical work is waste with no quality gain.

## The two questions

1. **How much reasoning does the piece need?** Is the path known (apply this rule, implement this spec) or must it be found (why does this race, what is the right boundary)?
2. **What does a mistake cost?** A wrong label is cheap. A wrong ledger entry, a leaked permission or a lost row is not.

High on either axis moves the piece up a tier. Low on both moves it down.

## Tiers

### No model

Anything a command answers in a few lines: `git` queries, a single test file, a linter, a grep, a build. Run it with Bash, in the background if slow, and read the result yourself.

### Haiku: mechanical, well-defined, high volume

- Find where something lives; list every usage of a symbol; map a directory.
- Run a long suite or build and report the tail verbatim with counts.
- Summarise logs or long output into a fixed format.
- Edits defined by an exact rule (rename, reorder imports, apply a codemod, fill a template).
- Extract fields from many files into a table.

Give it an exact output format and no decisions. It is weakest when asked to judge, so do not ask "is this correct?"; ask "does line X match pattern Y".

### Sonnet: the default builder and reviewer

- Implement a feature or fix from a clear brief, with tests.
- Ordinary refactors inside one module.
- UI, copy, i18n, documentation.
- Review of ordinary changes, one lens per reviewer (correctness, or tests, or accessibility).
- Read several sources and write a synthesis.

If you are unsure between Haiku and Sonnet for something that writes code, pick Sonnet.

### Opus: hard execution and high-stakes review

- Implementation that crosses modules or whose spec has gaps the builder must resolve sensibly.
- Debugging where the cause is unknown after a first look; concurrency, ordering, state machines.
- Independent review of anything touching money, data integrity, auth and permissions, security, migrations and backfills.
- A second opinion on your plan before an expensive or irreversible run.

Use one deep reviewer per risky branch, not one per step.

### The conductor

Intent, architecture, the split, briefs, judging results, integration, the final call, user communication. Also any piece small enough that its context is already in front of you.

## When to do it yourself

- The change is a few lines and you already have the file in context.
- Explaining it would take as long as doing it.
- It is a judgment call that depends on the whole conversation.

Otherwise delegate, and do not peek: reading the files "just to check" before the agent reports spends the tokens you were saving.

## Specialist agents

When the session lists project or plugin agents with a speciality (backend, frontend, security, qa, data-modeler...), prefer them: their definitions carry project conventions you would otherwise have to restate. Choose the agent type by speciality and the model by this file. An agent definition without a pinned effort runs at the session's effort, which is usually higher than the work needs. So: for work that needs the project's conventions (building in its codebase, reviewing its domain), use the specialist and set `model`. For work that does not (running a suite, a generic read-only review), use an agent that pins its effort, such as those in `assets/agents/`.

## Escalation and de-escalation

| Signal | Action |
|---|---|
| First failure, cause is a gap in the brief | Fix the brief, same agent, same tier |
| First failure, the agent misunderstood something the brief stated clearly | One correction message; if it recurs, up a tier |
| Second failure on the same piece | Up one tier, attach both failure outputs |
| Two reworks | Stop. Re-plan the split or the design |
| Ledger shows a tier passing a kind of work first time, repeatedly, with small token counts | Try that kind of work one tier down next time, and record the result |
| Ledger shows a tier's rework rate above about 30% for a kind of work | Route that kind up, or fix the brief template for it |

Project-specific exceptions go in `.claude/conductor/lessons.md`, not here.

## Multi-agent workflows

The Workflow tool (deterministic scripts spawning many agents) is only for when the user has explicitly opted into it. When they have: keep stages that do not need a strong model on Sonnet or Haiku, keep the agent count small, and log what the workflow will not cover.
