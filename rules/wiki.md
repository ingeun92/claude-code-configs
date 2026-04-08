# LLM Wiki

Global wiki at `~/wiki/`. Read `~/wiki/CLAUDE.md` for the full schema.

**Precedence**: If `## Wiki` section exists in the active CLAUDE.md, that section takes precedence over this file for routing and auto-capture behavior. This file serves as the fallback for environments without a CLAUDE.md Wiki section.

## Auto-capture

During any conversation, proactively identify knowledge worth persisting to the wiki:

- New concepts, entities, or tools encountered during research/work
- Architectural decisions and their rationale
- Non-obvious findings from debugging or investigation
- Cross-project patterns and reusable insights

When detected, suggest briefly: "Save to wiki? — [one-line summary]"
Only write to wiki upon user approval. Skip ephemeral details — capture only knowledge that compounds.

## Routing

- "add to wiki" → project wiki first (if `{cwd}/wiki/` exists), else global (`~/wiki/`)
- "global wiki" → `~/wiki/` explicitly
- "project wiki" → `{cwd}/wiki/` explicitly

## Operations

- **Ingest**: source → `sources/` summary + entity/concept pages + cross-refs + index + log
- **Query**: index → find pages → synthesize with `[[citations]]`
- **Lint**: contradictions, orphans, stale content, missing cross-refs
- **Promote**: project wiki → global wiki (knowledge elevation)
- **Import**: global wiki → project wiki (knowledge retrieval)
