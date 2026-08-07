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

### 4. Report

Give the user the counts, the date range, and which of the two files changed how.
If the pointer was `appended`, mention that the project already had a CLAUDE.md so
the section went at the end.

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
- The pointer wording comes from `~/.claude/templates/worklog-pointer.md`; edit
  that file to change it everywhere. The script falls back to an embedded copy if
  the template is missing.
