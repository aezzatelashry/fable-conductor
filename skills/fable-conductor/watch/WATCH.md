# Watch: the conductor's monitor

A sub-skill of fable-conductor. Its job is to notice, early, when a run is drifting into waste or risk, and to say what to change. It does not do the work and it does not dispatch agents.

## Where the tokens go

Knowing this is most of the job:

1. **Your own context.** Every turn resends the whole conversation at the conductor's rate. A long session makes every later turn dearer. This is usually the largest cost, and the one people overlook.
2. **Rework.** A piece done twice costs twice plus your time judging it twice.
3. **Over-routing.** A strong model on mechanical work.
4. **Agent start-up.** Each fresh agent re-reads project rules and re-discovers the code. Many tiny agents cost more than a few well-scoped ones.
5. **Verbose returns.** Long reports land in your context and stay there.

## Checkpoint (run at each wave of agents)

Run the report, then answer the questions.

```bash
python <skill-dir>/scripts/ledger.py report
```

- **Is the plan still right?** If two pieces needed rework for the same reason, the cause is upstream (the design or the brief template). Fix that before sending more.
- **Is anything over-routed or under-routed?** Use the flags in the report. Change the routing for the next wave and note it in `.claude/conductor/lessons.md`.
- **Is my context bloated?** Signs: you are reading whole files, agents return pages instead of the fixed format, you are re-deriving things already decided. Remedies: tighten the report format, send a scout instead of reading, and at a natural break save state and continue in a fresh session.
- **Are agents idle or duplicated?** Never have two agents (or an agent and you) on the same piece. Stop agents whose piece was re-planned away.
- **Is the fan-out earning its cost?** If pieces turned out to depend on each other, run them in sequence with one agent rather than parallel agents that collide.

## Waste signals and what to do

| Signal | Likely cause | Action |
|---|---|---|
| Same piece fails twice | Brief gap, or wrong tier | Follow the failure ladder; do not send a third identical attempt |
| Builder report says "done" but counts do not reconcile | Crash hidden by the summary | Treat as failed; get the raw tail |
| Agent asks questions the brief should have answered | Brief written from your context, not its | Rewrite the brief; add the missing section to your habit |
| Opus pieces finishing fast with small token counts, first-time pass | Over-routed | Try Sonnet for that kind next time |
| Haiku output needs your correction often | Under-routed, or it was asked to judge | Route up, or remove the judgment from the task |
| You spawned more than about six agents for one feature | Split too fine | Merge pieces; one agent per coherent unit |
| The session has run through many waves | Context cost compounding | Save state (progress doc, lessons, ledger), then a fresh session |
| You are about to read a large file "to be sure" | Habit | Ask a scout a precise question instead |

## Budget rules of thumb

- One scout question beats reading three files yourself.
- A brief should be shorter than the diff it asks for; if it is not, do the piece yourself.
- Continue an agent by message rather than replacing it; replace it only when its context is the problem.
- Background commands and fixed-format reports keep your context small; prefer both.
- Do not add a review layer the risk does not justify, and do not remove one it does.

## Reporting to the user

When asked about spend, give: dispatches per tier, tokens per tier, first-time pass rate, reworks and their causes, and one or two concrete changes for next time. Numbers come from the ledger; say plainly when the ledger is incomplete. The ledger counts subagent tokens only: the conductor's own usage is visible to the user through `/usage`, not to this script.
