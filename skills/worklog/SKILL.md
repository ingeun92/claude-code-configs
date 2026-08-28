---
name: worklog
description: Generate or refresh a project's WORKLOG.md — a dated work-history document digested from claude-mem records — and plant a pointer to it in CLAUDE.md. Use when the user asks to create, generate, update, refresh, or regenerate a worklog / work history / 작업 이력 / 업무 이력 문서, or says "WORKLOG 만들어줘", "worklog 갱신", "이 프로젝트 작업 이력 문서로 만들어줘".
---

# Worklog

Runs `~/.claude/scripts/generate-worklog.py`, which reads the claude-mem SQLite DB
(read-only) and writes a human-readable `WORKLOG.md` plus a pointer section inside
`CLAUDE.md`.

The one thing that actually goes wrong is picking the **claude-mem project key**.
Resolve it explicitly — never guess.

## Steps

### 1. Resolve the project key

The key is normally the **basename of the directory the session runs in**
(`/Users/x/Ing/bcnc` → `bcnc`, `/Users/x/Ing/bcnc/cirqle-mobile` → `cirqle-mobile`,
`/Users/x` → `x`). It is NOT the git repo name and NOT a path.

List the real keys and match:

```bash
~/.claude/scripts/generate-worklog.py --list-projects
```

Match `basename $(pwd)` against that list. If it does not match — e.g. cwd is a
subdirectory like `.../cirqle-mobile/apps/mobile` — walk up the path and test each
ancestor's basename until one matches. If several ancestors match, prefer the
**deepest** one (most specific project).

**Stop the walk before `$HOME`.** The home directory's own basename is usually a
valid project key (the catch-all for sessions started there), so it matches *every*
path beneath it. Accept it only when cwd is exactly `$HOME`. Without this guard,
`~/Ing/xdfi/airfi-cli` — a project with no claude-mem history — silently resolves
to the home project and writes the wrong history into the wrong directory.

If nothing matches, do not invent a key. Show the user the list and ask which
project they mean, or tell them this directory has no claude-mem history yet.
Offering the nearest plausible key is fine; picking one silently is not.

The `summ`/`obs` counts in the listing tell you whether a project has enough
material to be worth a document. Under ~10 summaries usually is not.

### 2. Choose the output path

Default to `WORKLOG.md` in the directory whose basename matched the key — not the
current working directory, if they differ. Confirm with the user when the two
differ, since the pointer is written next to the output file.

### 3. Run it

```bash
~/.claude/scripts/generate-worklog.py --project <key> --out <dir>/WORKLOG.md
```

The command writes two files and prints both to stderr:

```
<dir>/WORKLOG.md — 97,760 chars / 197 summaries · 1217 observations
<dir>/CLAUDE.md — pointer created
```

`pointer created | updated | appended` tells you what happened to CLAUDE.md:
created it, replaced its existing pointer block, or appended to a CLAUDE.md that
already had other content. Existing CLAUDE.md content is never removed.

### 4. Reconcile contradictions into the ledger

The generated document is a faithful transcript, not a verified one. A session that
changed its mind leaves both conclusions in the index, and a decision reversed months
later still reads as current at its own date. This step is what keeps a reader from
acting on a superseded entry — do not skip it.

**Do not attempt this mechanically.** Observation `concepts` are generic taxonomy tags
(`gotcha`, `trade-off`, `how-it-works`), not topics, so same-subject entries cannot be
grouped by query. It takes reading.

1. Read the **Decision & security index** in the file you just generated. On a large
   history, read the most recent ~6 months and anything the user names.
2. Group entries that concern the same subject — a tool kept or dropped, an approach
   chosen, a file's home, a convention. Look for groups where a later entry contradicts,
   narrows, or undoes an earlier one.
3. Maintain a ledger at the **top of WORKLOG.md, above `<!-- worklog:begin -->`**. Text
   before the marker is preserved verbatim by every regeneration; text inside it is not.
   Write it there and nowhere else.

```markdown
## 현재 유효한 결론 (Current conclusions)

_As of 2026-08-28 · reconciled from the index below. Each line is a reading of the
record, not a verified fact — follow the dates before relying on one._

- **OMC 플러그인**: 바닐라 모드 유지, HUD만 격리 설치. (2026-08-25 확정 · `#4555`)
  2026-08-21의 "HUD 부활"(`#4318`)과 v5.0.0 재도입 검토(`#4549`)를 대체.
- **메모리 스택**: claude-mem 단독 유지, LLM wiki 기각. (2026-07-30 · MEMORY.md)
```

Rules for the ledger, in order of importance:

- **Every line carries its date and the observation IDs it rests on.** A ledger line is
  your judgment about someone else's record; without the IDs a reader cannot check it,
  and an unverifiable line is worse than no line. The index prints each entry's id as
  `#4555`; `get_observations([4555])` pulls the full record behind it.
- **Say what each entry supersedes**, with that entry's date and ID. The point of a
  worklog is why the course changed — reconciling means ranking the entries, never
  deleting the losers.
- **Stamp the "as of" date**, because the ledger only refreshes when this skill runs and
  goes stale in between.
- **Rewrite the whole ledger each run** rather than appending. A stale line that has
  itself been superseded is the exact failure this section exists to prevent.
- **Only genuine contradictions.** A subject that never flip-flopped does not belong
  here; padding the ledger buries the entries that matter.
- If nothing contradicts, say so in one line and leave the section short.

Confirm the ledger with the user before writing it when the reconciliation is a judgment
call — you are asserting which of two recorded conclusions won.

### 5. Report

Give the user the counts, the date range, and which of the two files changed how.
If the pointer was `appended`, mention that the project already had a CLAUDE.md so
the section went at the end. Say how many contradictions the ledger reconciled, or
that none were found.

## Options worth knowing

| Flag | Use when |
|---|---|
| `--index all` | User wants every observation indexed by type, not just decisions. Roughly triples the document. |
| `--index none` | Narrative only, no index. |
| `--since` / `--until` | Restrict the date range. Also how you split a large history into a current file and an archive. |
| `--next-steps-from <date>` | Keep "Next steps" for older dates. **Default is the most recent date only**, so unresolved blockers from earlier dates silently drop out on regeneration. Pass this when the user cares about old open items. |
| `--no-claude-md` | Leave CLAUDE.md alone. |
| `--claude-md <path>` | Pointer goes somewhere other than beside the output. |
| `--out -` | Print to stdout for a preview; CLAUDE.md is not touched. |

## Facts that prevent mistakes

- **Full regeneration every run, not incremental.** This is deliberate: deletions
  and corrections in claude-mem propagate to the document. Do not "optimize" it
  into an append.
- **Only the `<!-- worklog:begin -->` … `<!-- worklog:end -->` block is replaced.**
  Hand-written text outside that block survives. Text inside it does not — if the
  user wants to annotate, tell them to write outside the markers.
- **The DB is opened read-only** and writes are atomic (temp file + rename), so a
  failed run cannot damage the live claude-mem DB or truncate an existing document.
- **Entries are point-in-time records.** claude-mem stores conclusions without
  verifying them, so a claim a later session reversed can still sit in the
  document. Do not present worklog contents as settled fact.
- **The two sections are not equally reliable.** The index comes from `observations`,
  written mid-session, so it keeps conclusions the same session later reversed. The
  session log comes from `session_summaries`, written at session end, so it holds that
  session's settled outcome. When they disagree, the session log wins. Reversals across
  sessions are settled by neither — only by the ledger from step 4.
- The pointer wording comes from `~/.claude/templates/worklog-pointer.md`; edit
  that file to change it everywhere. The script falls back to an embedded copy if
  the template is missing.
