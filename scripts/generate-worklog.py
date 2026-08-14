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
import tempfile
from collections import Counter, OrderedDict, defaultdict
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
    ("sensitive", "Sensitive"),
    ("discovery", "Discovery"),
])
UNKNOWN_LABEL = "Other"

# High-signal, low-volume types that make up the default index.
# `sensitive` belongs here: claude-mem writes it for secret-adjacent findings, and it
# is what this DB actually stores — the `security_*` names alone silently dropped them.
DECISION_TYPES = {"decision", "security_alert", "security_note", "sensitive"}

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


def _in_clause(projects):
    """`project IN (?,?,…)` — a single key still goes through here so both paths
    share one query shape."""
    return " AND project IN (%s)" % ",".join("?" * len(projects))


def fetch_summaries(conn, projects, since, until):
    sql = """SELECT date(created_at) d, created_at, memory_session_id sid, project,
                    COALESCE(request,'') request,
                    COALESCE(investigated,'') investigated,
                    COALESCE(learned,'') learned,
                    COALESCE(completed,'') completed,
                    COALESCE(next_steps,'') next_steps
             FROM session_summaries WHERE 1=1"""
    args = list(projects)
    sql += _in_clause(projects)
    sql = _range_clause(sql, args, since, until)
    return conn.execute(sql + " ORDER BY created_at_epoch ASC, id ASC", args).fetchall()


def fetch_observations(conn, projects, since, until):
    sql = """SELECT date(created_at) d, type, project, COALESCE(title,'') title,
                    COALESCE(subtitle,'') subtitle
             FROM observations WHERE 1=1"""
    args = list(projects)
    sql += _in_clause(projects)
    sql = _range_clause(sql, args, since, until)
    return conn.execute(sql + " ORDER BY created_at_epoch ASC, id ASC", args).fetchall()


# Directory names that never hold a sibling project and would blow up the scan.
SCAN_SKIP = {
    "node_modules", "dist", "build", "out", "target", "vendor", "Pods",
    "ios", "android", "coverage", "__pycache__", ".venv", "venv",
}
SCAN_DEPTH = 2


def discover_projects(root, known, depth=SCAN_DEPTH):
    """claude-mem keys whose name matches a directory under `root`.

    claude-mem stores only the basename as the project key — no path — so a
    same-named directory elsewhere on disk is indistinguishable from this one.
    That is why the caller prints the adopted keys: the operator, not the
    script, is the one who can spot a wrong match.

    Depth 2 costs ~1ms on a 26-directory workspace, so it is not worth making
    configurable; the skip list keeps `node_modules` from dominating the walk.
    """
    found = set()

    def walk(path, level):
        if level > depth:
            return
        try:
            entries = list(os.scandir(path))
        except OSError:  # unreadable dir is not fatal — just unscannable
            return
        for e in entries:
            if not e.is_dir(follow_symlinks=False):
                continue
            if e.name.startswith(".") or e.name in SCAN_SKIP:
                continue
            if e.name in known:
                found.add(e.name)
            walk(e.path, level + 1)

    walk(root, 1)
    return found


def all_project_keys(conn):
    return {r["project"] for r in conn.execute("SELECT DISTINCT project FROM observations")}


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


def render_index(obs, mode, tag_project=False):
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
                if tag_project:
                    line = f"- `{it['project']}` {line[2:]}"
                if sub and sub.lower() != title.lower():
                    line += f" — {sub}"
                L.append(line)
            L.append("")
            if fold:
                L += ["</details>", ""]
    return L


def render_narrative(summaries, next_from, tag_project=False):
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
            # Without the origin, entries from three repos read as one undifferentiated
            # stream and "which codebase was this?" becomes unanswerable.
            if tag_project:
                title = f"`{r['project']}` · {title}"
            L.append(f"#### {title}")
            body = indent_block(r["completed"])
            L += body if body else ["  - (nothing recorded as completed)"]
            # `learned` carries the technical findings and `investigated` the search
            # trail — the two thickest fields in a summary. Omitting them made entries
            # read as "nothing much happened" even when the session recorded plenty.
            for label, field in (("Learned", "learned"), ("Investigated", "investigated")):
                blk = indent_block(r[field])
                if blk:
                    L += ["", f"  **{label}**"] + blk
            if next_from and r["d"] >= next_from and r["next_steps"].strip():
                nb = indent_block(r["next_steps"])
                if nb:
                    L += ["", "  **Next steps**"] + nb
            L.append("")
    return L, by_date


def build(projects, summaries, obs, next_from, index_mode, since, until, command):
    stamp = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M %Z")
    multi = len(projects) > 1
    narrative, by_date = (
        render_narrative(summaries, next_from, multi) if summaries else ([], {})
    )
    dates = sorted({*(by_date.keys()), *(o["d"] for o in obs)})
    sessions = len({r["sid"] for r in summaries})

    L = [
        "> Generated from claude-mem records. **Text outside the marker block is preserved**",
        "> across regeneration.",
        f"> Update: `{command}`",
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
    if multi:
        # Per-key counts make a missing repo obvious — a key that scanned but holds
        # nothing in range shows up as 0 rather than silently vanishing.
        per = Counter(o["project"] for o in obs)
        parts = ", ".join(f"{p} ({per.get(p, 0)})" for p in projects)
        L.append(f"- Projects: {parts}")
    if since or until:
        L.append(f"- Filter: {since or 'start'} ~ {until or 'end'}")
    L += ["", "---", ""]

    idx = render_index(obs, index_mode, multi)
    if idx:
        L += idx + ["---", ""]
    L += narrative
    return "\n".join(L).rstrip() + "\n"


def splice(existing, body, title):
    """Replace only the marker block, preserving everything outside it."""
    block = f"{BEGIN}\n{body}{END}\n"
    if existing and BEGIN in existing and END in existing:
        head, rest = existing.split(BEGIN, 1)
        _, tail = rest.split(END, 1)
        return f"{head}{block}{tail.lstrip(chr(10))}"
    if existing:  # existing file without markers — append instead of destroying it
        return f"{existing.rstrip()}\n\n{block}"
    return f"# {title} work history\n\n{block}"


def atomic_write(path, text):
    """Write via a temp file in the same directory, then rename over the target.

    A plain open(path, "w") truncates immediately, so a crash mid-write leaves a
    partial file. The generated body is recoverable from the DB, but hand-written
    text outside the marker block is not. os.replace() is atomic on the same
    filesystem, so readers see either the old file or the new one, never a stump.
    """
    directory = os.path.dirname(os.path.abspath(path))
    # mkstemp creates 0600 and os.replace carries the temp file's mode over, so the
    # target's permissions must be restored explicitly or every run tightens them.
    try:
        mode = os.stat(path).st_mode & 0o777
    except OSError:
        umask = os.umask(0)
        os.umask(umask)
        mode = 0o666 & ~umask
    fd, tmp = tempfile.mkstemp(dir=directory, prefix=".worklog-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            fh.write(text)
            fh.flush()
            os.fsync(fh.fileno())
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


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

    atomic_write(path, doc)
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
    ap.add_argument(
        "--include-subprojects",
        action="store_true",
        help=f"also pull keys matching directories under the output dir "
             f"(depth {SCAN_DEPTH}) — for a workspace holding several repos",
    )
    a = ap.parse_args()

    conn = connect_ro(a.db)
    try:
        if a.list_projects:
            list_projects(conn)
            return
        if not a.project:
            ap.error("--project is required (use --list-projects to see the keys)")

        projects = [a.project]
        if a.include_subprojects:
            if not a.out or a.out == "-":
                ap.error("--include-subprojects needs --out (the scan root is its directory)")
            root = os.path.dirname(os.path.abspath(os.path.expanduser(a.out))) or "."
            extra = discover_projects(root, all_project_keys(conn)) - {a.project}
            projects += sorted(extra)
            # claude-mem keys carry no path, so a same-named directory elsewhere is
            # indistinguishable. Print what was adopted — the operator is the only
            # one who can catch a wrong match.
            print(f"projects: {', '.join(projects)}  (scan root: {root})", file=sys.stderr)

        summaries = fetch_summaries(conn, projects, a.since, a.until)
        obs = fetch_observations(conn, projects, a.since, a.until)
        if not summaries and not obs:
            sys.exit(f"no records for {', '.join(projects)} under these filters.")

        next_from = a.next_steps_from or (max(r["d"] for r in summaries) if summaries else None)

        # Collapse paths under $HOME back to ~ — a shell-expanded absolute path baked
        # into the command would not port to another machine.
        home = os.path.expanduser("~")
        shown = None
        if a.out and a.out != "-":
            abs_out = os.path.abspath(os.path.expanduser(a.out))
            shown = f"~{abs_out[len(home):]}" if abs_out.startswith(home + os.sep) else a.out
        cmd = (
            f"~/.claude/scripts/generate-worklog.py --project {a.project}"
            + (f" --out {shown}" if shown else "")
            + (f" --index {a.index}" if a.index != "decisions" else "")
            + (" --include-subprojects" if a.include_subprojects else "")
        )
        body = build(projects, summaries, obs, next_from, a.index, a.since, a.until, cmd)
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
    atomic_write(path, doc)
    state = "" if BEGIN in existing else " (new)"
    print(
        f"{path} — {len(doc):,} chars / {len(summaries)} summaries · {len(obs)} observations{state}",
        file=sys.stderr,
    )

    if a.no_claude_md:
        return
    section = render_pointer(
        load_template(a.template), os.path.basename(path), cmd, a.index
    )
    md_path = os.path.expanduser(a.claude_md) if a.claude_md else os.path.join(
        os.path.dirname(os.path.abspath(path)), "CLAUDE.md"
    )
    action = write_pointer(md_path, section, a.project)
    print(f"{md_path} — pointer {action}", file=sys.stderr)


if __name__ == "__main__":
    main()
