#!/usr/bin/env python3
"""Digest claude-mem records into a human-readable WORKLOG.md.

Two sources are combined:
  - session_summaries -> narrative (what was asked, what was completed).
    Carries commit hashes and PR numbers.
  - observations      -> typed index (decision / feature / fix ...).
    Use it to answer "when was X decided".

The claude-mem DB is always opened read-only: it is the same file a live worker
holds, so opening it writable risks lock contention or corruption.

Only the marker block (<!-- worklog:begin --> ... <!-- worklog:end -->) is
regenerated. Anything written by hand outside that block is preserved.

Usage:
    generate-worklog.py --project bcnc --out ~/Ing/bcnc/WORKLOG.md
    generate-worklog.py --project bcnc --out - --since 2026-07-01
    generate-worklog.py --project bcnc --out ... --index all
    generate-worklog.py --list-projects
"""

import argparse
import os
import re
import sqlite3
import sys
from collections import OrderedDict, defaultdict
from datetime import datetime, timezone

DEFAULT_DB = os.path.expanduser("~/.claude-mem/claude-mem.db")

BEGIN = "<!-- worklog:begin -->"
END = "<!-- worklog:end -->"

# Pointer section planted inside CLAUDE.md. Markers keep repeat runs from duplicating it.
POINTER_BEGIN = "<!-- worklog-pointer:begin -->"
POINTER_END = "<!-- worklog-pointer:end -->"

# Global template. Falls back to EMBEDDED_TEMPLATE below, so the script works standalone.
TEMPLATE_PATH = os.path.expanduser("~/.claude/templates/worklog-pointer.md")

EMBEDDED_TEMPLATE = """## Work history

`{{worklog}}` holds this project's dated work history, generated from claude-mem
records. Newest entries first.

{{sections}}

**Read it when** the user asks what was done before, why something is built the way
it is, how far a task got, or when a decision was made. The claude-mem context
injected at session start covers only the ~50 most recent observations for this
project — anything older lives in this file or in `mem-search`. Check it before
answering from memory or re-deriving history from the code.

**It is not auto-updated.** Regenerate with:

```bash
{{command}}
```

Only the `<!-- worklog:begin -->` … `<!-- worklog:end -->` block is replaced. Text
outside that block is preserved, so notes hand-written into `{{worklog}}` survive
regeneration.

**Entries are point-in-time records, not settled fact.** claude-mem stores
conclusions without verifying them, so a claim that a later session reversed may
still sit here uncorrected. Before relying on any single entry, check whether a
later date revisits it.
"""

# Per --index blurb describing the document layout (fills {{sections}} in the template)
SECTION_BLURBS = {
    "decisions": (
        "- **Decision index** — observations typed `decision` / `security_*`. "
        "Use it to answer \"when and why was X decided\".\n"
        "- **Session log** — what was requested and what was completed, "
        "including commit hashes, PR numbers, and verification results."
    ),
    "all": (
        "- **Observation index** — every observation grouped by day and type "
        "(decision, feature, bugfix, refactor, change, discovery …). "
        "High-volume types are folded into `<details>` blocks.\n"
        "- **Session log** — what was requested and what was completed, "
        "including commit hashes, PR numbers, and verification results."
    ),
    "none": (
        "- **Session log** — what was requested and what was completed, "
        "including commit hashes, PR numbers, and verification results."
    ),
}

# Index display order and labels. Types missing here are grouped under UNKNOWN_LABEL
# rather than dropped — claude-mem preserves custom observation types, so trusting a
# whitelist alone loses records silently.
TYPE_LABELS = OrderedDict([
    ("decision", "Decision"),
    ("feature", "Feature"),
    ("bugfix", "Fix"),
    ("bug-fix", "Fix"),
    ("refactor", "Refactor"),
    ("change", "Change"),
    ("verification", "Verification"),
    ("security_alert", "Security alert"),
    ("security_note", "Security note"),
    ("discovery", "Discovery"),
])
UNKNOWN_LABEL = "Other"

# High-signal, low-volume types that make up the default index
DECISION_TYPES = {"decision", "security_alert", "security_note"}

# High-volume, low-signal types worth folding away
COLLAPSED = {"discovery", "change"}

ORDERED = re.compile(r"^(\d{1,2})[.)]\s+(.*)$")


def connect_ro(db_path):
    if not os.path.exists(db_path):
        sys.exit(f"claude-mem DB not found: {db_path}")
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def list_projects(conn):
    rows = conn.execute(
        """SELECT project,
                  (SELECT COUNT(*) FROM session_summaries s WHERE s.project = o.project) summaries,
                  COUNT(*) obs,
                  date(MIN(created_at)) first, date(MAX(created_at)) last
           FROM observations o GROUP BY project ORDER BY obs DESC"""
    ).fetchall()
    print(f"{'project':<32}{'summ':>6}{'obs':>7}  {'first':<12}{'last':<12}")
    for r in rows:
        print(
            f"{r['project']:<32}{r['summaries']:>6}{r['obs']:>7}  "
            f"{r['first'] or '-':<12}{r['last'] or '-':<12}"
        )


def _range_clause(sql, args, since, until):
    if since:
        sql += " AND date(created_at) >= ?"
        args.append(since)
    if until:
        sql += " AND date(created_at) <= ?"
        args.append(until)
    return sql


def fetch_summaries(conn, project, since, until):
    sql = """SELECT date(created_at) d, created_at, memory_session_id sid,
                    COALESCE(request,'') request,
                    COALESCE(completed,'') completed,
                    COALESCE(next_steps,'') next_steps
             FROM session_summaries WHERE project = ?"""
    args = [project]
    sql = _range_clause(sql, args, since, until)
    return conn.execute(sql + " ORDER BY created_at_epoch ASC, id ASC", args).fetchall()


def fetch_observations(conn, project, since, until):
    sql = """SELECT date(created_at) d, type, COALESCE(title,'') title,
                    COALESCE(subtitle,'') subtitle
             FROM observations WHERE project = ?"""
    args = [project]
    sql = _range_clause(sql, args, since, until)
    return conn.execute(sql + " ORDER BY created_at_epoch ASC, id ASC", args).fetchall()


def indent_block(text):
    """Normalize claude-mem summary text into a markdown list.

    In the source, 0- and 4-space indents are sibling items; 6+ spaces are true
    children. (Measured distribution: 0sp 382, 4sp 936, 6sp 132, 7sp 45.)
    Mapping 4 spaces straight to one nesting level would make siblings look like
    children of the first item.
    """
    out = []
    for raw in text.replace("\r\n", "\n").split("\n"):
        line = raw.rstrip()
        if not line.strip():
            continue
        stripped = line.lstrip()
        level = 1 if (len(line) - len(stripped)) >= 6 else 0
        stripped = stripped.lstrip("-*·•").strip()
        if not stripped:
            continue
        pad = "  " * (level + 1)
        m = ORDERED.match(stripped)
        if m:  # the number carries sequence information, so keep it
            out.append(f"{pad}{m.group(1)}. {m.group(2)}")
        else:
            out.append(f"{pad}- {stripped}")
    return out


def label_of(typ):
    return TYPE_LABELS.get(typ, UNKNOWN_LABEL)


def render_index(obs, mode):
    """Index of observations grouped day -> type. mode: decisions | all"""
    if mode == "none" or not obs:
        return []

    rows = [o for o in obs if mode == "all" or o["type"] in DECISION_TYPES]
    if not rows:
        return []

    by_day = defaultdict(lambda: defaultdict(list))
    for o in rows:
        by_day[o["d"]][o["type"]].append(o)

    heading = "Decision & security index" if mode == "decisions" else "Observation index"
    L = [f"## {heading}", ""]
    if mode == "decisions":
        L += ["Only observations typed `decision` / `security_*`. "
              "Regenerate with `--index all` for the full set.", ""]

    # Label order: as declared in TYPE_LABELS, unknown types last
    order = list(TYPE_LABELS.keys())

    def type_key(t):
        return (order.index(t), t) if t in order else (len(order), t)

    for day in sorted(by_day, reverse=True):
        groups = by_day[day]
        total = sum(len(v) for v in groups.values())
        L += [f"### {day} ({total})", ""]
        for typ in sorted(groups, key=type_key):
            items = groups[typ]
            fold = typ in COLLAPSED and len(items) > 3
            if fold:
                L += [f"<details><summary><b>{label_of(typ)}</b> ({len(items)})</summary>", ""]
            else:
                L += [f"**{label_of(typ)}** ({len(items)})", ""]
            for it in items:
                title = " ".join(it["title"].split())
                sub = " ".join(it["subtitle"].split())
                line = f"- {title}" if title else "- (untitled)"
                if sub and sub.lower() != title.lower():
                    line += f" — {sub}"
                L.append(line)
            L.append("")
            if fold:
                L += ["</details>", ""]
    return L


def render_narrative(summaries, next_from):
    by_date = OrderedDict()
    seen = set()
    for r in summaries:
        key = (r["created_at"], r["completed"])
        if key in seen:  # drop verbatim duplicates
            continue
        seen.add(key)
        by_date.setdefault(r["d"], []).append(r)

    L = ["## Session log", ""]
    for d in reversed(list(by_date.keys())):
        L += [f"### {d}", ""]
        last_sid = None
        for r in by_date[d]:
            if r["sid"] != last_sid:
                last_sid = r["sid"]
                L.append(f"<!-- session {r['sid']} -->")
            title = " ".join(r["request"].split()) or "(no request recorded)"
            if len(title) > 160:
                title = title[:157] + "..."
            L.append(f"#### {title}")
            body = indent_block(r["completed"])
            L += body if body else ["  - (nothing recorded as completed)"]
            if next_from and r["d"] >= next_from and r["next_steps"].strip():
                nb = indent_block(r["next_steps"])
                if nb:
                    L += ["", "  **Next steps**"] + nb
            L.append("")
    return L, by_date


def build(project, summaries, obs, next_from, index_mode, since, until):
    stamp = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M %Z")
    narrative, by_date = render_narrative(summaries, next_from) if summaries else ([], {})
    dates = sorted({*(by_date.keys()), *(o["d"] for o in obs)})
    sessions = len({r["sid"] for r in summaries})

    L = [
        "> Generated from claude-mem records. **Text outside the marker block is preserved**",
        "> across regeneration.",
        f"> Update: `~/.claude/scripts/generate-worklog.py --project {project} --out <this file>`",
        ">",
        "> **Each entry is a point-in-time record, not settled fact.** claude-mem stores",
        "> conclusions without verifying them, so a claim that a later session reversed may",
        "> still sit here uncorrected. Check later dates before relying on any single entry.",
        "",
    ]
    if dates:
        L.append(f"- Range: {dates[0]} ~ {dates[-1]} ({len(dates)} days)")
    L += [
        f"- {sessions} sessions / {len(summaries)} summaries / {len(obs)} observations",
        f"- Generated: {stamp}",
    ]
    if since or until:
        L.append(f"- Filter: {since or 'start'} ~ {until or 'end'}")
    L += ["", "---", ""]

    idx = render_index(obs, index_mode)
    if idx:
        L += idx + ["---", ""]
    L += narrative
    return "\n".join(L).rstrip() + "\n"


def splice(existing, body, project):
    """Replace only the marker block, preserving everything outside it."""
    block = f"{BEGIN}\n{body}{END}\n"
    if existing and BEGIN in existing and END in existing:
        head, rest = existing.split(BEGIN, 1)
        _, tail = rest.split(END, 1)
        return f"{head}{block}{tail.lstrip(chr(10))}"
    if existing:  # existing file without markers — append instead of destroying it
        return f"{existing.rstrip()}\n\n{block}"
    return f"# {project} work history\n\n{block}"


def load_template(path):
    """Read the global template, falling back to the embedded copy."""
    try:
        with open(os.path.expanduser(path), encoding="utf-8") as fh:
            text = fh.read().strip()
            if text:
                return text
    except OSError:
        pass
    return EMBEDDED_TEMPLATE.strip()


def render_pointer(template, worklog_name, command, index_mode):
    # Plain replacement rather than str.format — code fences and braces in the
    # template would break format().
    text = template
    for key, val in (
        ("{{worklog}}", worklog_name),
        ("{{command}}", command),
        ("{{sections}}", SECTION_BLURBS.get(index_mode, SECTION_BLURBS["decisions"])),
    ):
        text = text.replace(key, val)
    return f"{POINTER_BEGIN}\n{text.strip()}\n{POINTER_END}\n"


def write_pointer(path, section, project):
    """Plant the pointer section into CLAUDE.md.

    Returns 'created' | 'updated' | 'appended'.
    If the markers are present, only that block is replaced; otherwise the section
    is appended at the end. Existing content is never removed.
    """
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)

    existing = ""
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            existing = fh.read()

    if not existing.strip():
        doc, action = f"# {project}\n\n{section}", "created"
    elif POINTER_BEGIN in existing and POINTER_END in existing:
        head, rest = existing.split(POINTER_BEGIN, 1)
        _, tail = rest.split(POINTER_END, 1)
        doc, action = f"{head}{section}{tail.lstrip(chr(10))}", "updated"
    else:
        doc, action = f"{existing.rstrip()}\n\n{section}", "appended"

    with open(path, "w", encoding="utf-8") as fh:
        fh.write(doc)
    return action


def main():
    ap = argparse.ArgumentParser(description="claude-mem -> WORKLOG.md digest")
    ap.add_argument("--project", help="claude-mem project key (e.g. bcnc)")
    ap.add_argument("--out", help="output path, or '-' for stdout (default: stdout)")
    ap.add_argument("--since", metavar="YYYY-MM-DD", help="start date")
    ap.add_argument("--until", metavar="YYYY-MM-DD", help="end date")
    ap.add_argument(
        "--index",
        choices=["decisions", "all", "none"],
        default="decisions",
        help="observation index scope (default: decisions — decision/security_* only)",
    )
    ap.add_argument(
        "--next-steps-from",
        metavar="YYYY-MM-DD",
        help="include 'Next steps' only for entries on/after this date "
             "(default: the most recent date)",
    )
    ap.add_argument(
        "--claude-md",
        metavar="PATH",
        help="CLAUDE.md to plant the pointer in (default: alongside --out)",
    )
    ap.add_argument("--no-claude-md", action="store_true", help="leave CLAUDE.md untouched")
    ap.add_argument(
        "--template",
        default=TEMPLATE_PATH,
        metavar="PATH",
        help=f"pointer template (default {TEMPLATE_PATH}, else the embedded copy)",
    )
    ap.add_argument("--db", default=DEFAULT_DB, help=f"claude-mem DB path (default {DEFAULT_DB})")
    ap.add_argument("--list-projects", action="store_true", help="list available project keys")
    a = ap.parse_args()

    conn = connect_ro(a.db)
    try:
        if a.list_projects:
            list_projects(conn)
            return
        if not a.project:
            ap.error("--project is required (use --list-projects to see the keys)")

        summaries = fetch_summaries(conn, a.project, a.since, a.until)
        obs = fetch_observations(conn, a.project, a.since, a.until)
        if not summaries and not obs:
            sys.exit(f"no records for project '{a.project}' under these filters.")

        next_from = a.next_steps_from or (max(r["d"] for r in summaries) if summaries else None)
        body = build(a.project, summaries, obs, next_from, a.index, a.since, a.until)
    finally:
        conn.close()

    if not a.out or a.out == "-":
        sys.stdout.write(splice("", body, a.project))
        return

    path = os.path.expanduser(a.out)
    parent = os.path.dirname(path)
    if parent:  # dirname is '' when --out is a bare filename, which makedirs rejects
        os.makedirs(parent, exist_ok=True)
    existing = ""
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            existing = fh.read()
    doc = splice(existing, body, a.project)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(doc)
    state = "" if BEGIN in existing else " (new)"
    print(
        f"{path} — {len(doc):,} chars / {len(summaries)} summaries · {len(obs)} observations{state}",
        file=sys.stderr,
    )

    if a.no_claude_md:
        return
    # Collapse paths under $HOME back to ~ — a shell-expanded absolute path baked
    # into the command would not port to another machine.
    home = os.path.expanduser("~")
    abs_path = os.path.abspath(path)
    shown = f"~{abs_path[len(home):]}" if abs_path.startswith(home + os.sep) else path
    cmd = (
        f"~/.claude/scripts/generate-worklog.py --project {a.project} "
        f"--out {shown}"
        + (f" --index {a.index}" if a.index != "decisions" else "")
    )
    section = render_pointer(
        load_template(a.template), os.path.basename(path), cmd, a.index
    )
    md_path = os.path.expanduser(a.claude_md) if a.claude_md else os.path.join(
        os.path.dirname(abs_path), "CLAUDE.md"
    )
    action = write_pointer(md_path, section, a.project)
    print(f"{md_path} — pointer {action}", file=sys.stderr)


if __name__ == "__main__":
    main()
