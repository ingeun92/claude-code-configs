## Work history

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

**Two layers, different reliability.** The index is written mid-session and keeps
conclusions the same session later reversed; the session log is written at session
end and holds that session's settled outcome — prefer the session log when the two
disagree.

**A `## 현재 유효한 결론 (Current conclusions)` section at the top of `{{worklog}}`,
if present, outranks both.** It is the hand-maintained ledger reconciling reversals
across sessions, refreshed by `/worklog`, and each line carries the dates and
observation IDs it rests on. It goes stale between regenerations — check its "as of"
date, and verify against the log below before treating a line as current.
