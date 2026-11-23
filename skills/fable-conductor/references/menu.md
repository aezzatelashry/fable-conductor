# The menu

People forget phrases. The menu puts everything the skill can do in front of the person as choices, so nothing has to be remembered or typed.

## When to show it

- The first message of a session is not a concrete task: a greeting, "continue", "start", something vague, or nothing actionable.
- The person asks for it in any words: "menu", "القائمة", "what can you do", "مش فاكر أقول إيه", "?".
- At the end of every run, as the last option of the next-step choices ("القائمة" / "Menu").

Do not show it when the first message is a concrete task: do the task. Do not show it twice in a row, and do not show it after the person has dismissed it in this session unless they ask.

## How to show it

Use the structured question tool, in the person's language, one question with four options. The free-text "Other" that the tool adds is where they type or dictate a task directly. If the tool is unavailable or returns no answer, print the same options as a short numbered list and stop for the reply; never treat a skipped answer as a choice.

**Question: what would you like to do?** (عايز تعمل إيه؟)

| Option | What it leads to |
|---|---|
| New work, plan first (شغل جديد، الخطة أولًا) | Ask for the task in one line if it was not given, then run the `plan` mode: split and routing table, no spend until a go-ahead. Recommended default, so list it first |
| Continue where we stopped (كمّل اللي واقف) | Read the project's progress or handoff notes and `.claude/conductor/lessons.md`, say in two lines where things stand, and offer the next step as choices |
| Spend and quality (الاستهلاك والجودة) | Run the `watch` report. Then offer: open or refresh the dashboard, or nothing |
| Maintenance (صيانة) | A second question with the four options below |

**Second question, after Maintenance: which one?** (أنهي واحدة؟)

| Option | What it leads to |
|---|---|
| Prepare this project (جهّز المشروع) | `setup` mode |
| Audit installed skills and plugins (جرد الإضافات) | `audit` mode |
| My profile (ملفي) | `profile` mode: show it, change or delete lines |
| Update the skill (حدّث المهارة) | `evolve` mode |

Give each option a one-line description saying what will happen and whether it spends tokens or changes files. Keep labels to a few words.

## After a run

End every run with one question: the two or three natural next steps for what just happened (for example: go on to the next piece, show spend, stop here), with "Menu" as the last option. If the session has grown long, make one of the options "save state and continue in a fresh session", and say why: every turn resends the whole conversation, so a long session makes each later step dearer.
