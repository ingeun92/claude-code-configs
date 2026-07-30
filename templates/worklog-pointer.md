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
