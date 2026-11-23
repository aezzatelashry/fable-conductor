# A small run, step by step

> **Illustrative and fictional.** This is not a recorded run. The project (tidepool), the file names, the token counts, the durations, the test counts and every output below are invented to show the shape of one small run. Do not read them as measurements.

The example is deliberately small: two pieces, two dispatches. It shows what the conductor writes, what comes back, and what it checks before it believes the result.

## The request

> Add a `--format csv` option to the `tides` command in tidepool, and document it in the user guide.

## The split

1. **Implementation and tests.** Add `--format {table,csv}` to `tides` (default `table`). Files: `src/tidepool/cli.py`, `src/tidepool/render.py`, `tests/test_tides_cli.py`. Proven by the test suite, including new tests for the CSV output.
2. **User guide section.** Describe the flag with one example. File: `docs/user-guide.md`. Proven by reading the diff against the flag spec in the brief.

The pieces are independent. The flag name, values and CSV columns are fixed by the conductor in both briefs, so neither agent waits for the other.

## The routing table

| Piece | Goes to | Why |
|---|---|---|
| 1. Implementation and tests | Sonnet builder | Clear spec, one module, tests included; no gaps to resolve. |
| 2. User guide section | Sonnet builder | Prose that must match behaviour is documentation, which routing.md sends to Sonnet; not an exact-rule edit, so not Haiku. |

## One full brief

This is the brief for piece 1, as sent.

```
GOAL
Add a --format option to the `tides` command so tide tables can be printed as CSV.
Done means `tidepool tides --station 0412 --format csv` prints a header row and one
row per tide event, and the existing table output is unchanged.

WHERE
Work in the repository root, on branch feature/tides-csv, base commit as checked out.
You may read anything. You may edit only src/tidepool/cli.py, src/tidepool/render.py
and tests/test_tides_cli.py. Do not touch docs/ (another agent is editing
docs/user-guide.md).

PROBLEM / TASK
`tides` only prints a fixed-width table: see render_table() in src/tidepool/render.py
and the call in the tides() handler in src/tidepool/cli.py. Users who want to load the
output into a spreadsheet have to parse the table by hand.

INTENDED DESIGN
Add `--format` with choices `table` and `csv`, default `table`. Add render_csv(events)
beside render_table() in render.py, using the standard library csv module (not manual
string joins; station names can contain commas). Columns, in order: station, time_utc,
kind, height_m. kind is `high` or `low`. Write with "\n" line endings. Verify this
against the code first. If it does not fit, stop and tell me why.

OUT OF SCOPE
docs/ (another agent). A third format such as JSON. Any change to render_table() or to
how events are fetched. Unit conversion: height_m stays in metres.

TESTS
New tests in tests/test_tides_cli.py: header and column order; one row per event;
a station name containing a comma is quoted; default output is still the table;
an unknown format value exits with code 2. Run the project's test command from
pyproject.toml (`python -m pytest`). Do not weaken, skip or delete an existing test.
To undo a mistake, copy the file back from a backup copy; never run a git command
that discards changes.

SHARED RESOURCES
None.

PROJECT RULES
Read CONTRIBUTING.md first. Commit style: one commit, imperative subject line.

REPORT (exactly this, nothing else)
STATUS / CHANGED / COMMIT / TESTS / DEVIATIONS / NOT DONE / NOT TESTED / GIT STATUS
```

## The report that came back

```
STATUS: done
CHANGED:
  src/tidepool/render.py - add render_csv() using csv.writer
  src/tidepool/cli.py - add --format option, dispatch to render_csv or render_table
  tests/test_tides_cli.py - 7 new tests
COMMIT: 3f9c2ab "Add --format csv option to tides"
TESTS: python -m pytest
  31 passed, 1 skipped, 0 failed (32 total)
  tests/test_tides_cli.py ............s.......
  ======= 31 passed, 1 skipped in 1.84s =======
DEVIATIONS: none
NOT DONE / NOT TESTED: reading station IDs from a file (not requested); behaviour with
  Windows line endings (not tested).
GIT STATUS:
  (clean after commit)
```

## What the conductor verified

The report is a claim. The conductor checked it itself:

- **Tests.** Ran `python -m pytest`: 31 passed, 1 skipped, 0 failed, 32 total. Before the change the suite had 24 passed and 1 skipped (25 total), so the 7 new tests account for the difference. The one skip is the same pre-existing test as before.
- **Diff in scope.** `git diff --stat` against the base commit listed the three allowed files and nothing under `docs/`.
- **Git status.** Clean, no stray files, on the expected branch, and commit `3f9c2ab` is the branch head.
- **Design followed.** Read `render_csv()`: it uses `csv.writer`, the column order is as specified, and `render_table()` is unchanged.
- **One thing the report did not prove.** A passing quoting test does not show the test can fail. The conductor copied `render.py` aside, replaced the `csv.writer` call with a plain comma join, and reran the file. The comma-in-station-name test failed, as it should. It then restored `render.py` from the copy and confirmed the diff was unchanged.

The user guide piece came back separately and was read against the flag spec: flag name, values, default and column order all matched. One example output was missing the `kind` column. The conductor sent that one finding back to the same agent, which corrected the line, so the dispatch is logged as `rework`, not `pass`.

## The ledger lines

```json
{"ts": "2026-01-15T10:02:11+00:00", "model": "sonnet", "role": "builder", "kind": "implement", "tokens": 38420, "duration_ms": 214000, "outcome": "pass", "task": "tides --format csv: implementation and tests"}
{"ts": "2026-01-15T10:03:40+00:00", "model": "sonnet", "role": "builder", "kind": "docs", "tokens": 9150, "duration_ms": 61000, "outcome": "rework", "task": "tides --format csv: user guide section"}
```
