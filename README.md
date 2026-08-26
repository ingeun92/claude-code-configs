# Claude Code Configs

A repository for managing and sharing Claude Code global settings (`~/.claude`).

## Structure

```
├── CLAUDE.md                  # Global instructions
├── RTK.md                     # RTK token-saving CLI guide
├── rules/
│   ├── cli-checklist.md       # CLI tool building checklist
│   ├── readme-guide.md        # README writing guide
│   └── refactor-safety.md     # Refactoring safety rules
├── hooks/
│   ├── bash-auto-allow.sh     # Auto-allow Bash commands (blocks dangerous patterns)
│   ├── git-guard-hook.sh      # Injects checklists on git commit/push
│   ├── rtk-rewrite.sh         # RTK token-saving auto-rewrite
│   ├── pre-commit-checklist.md
│   └── pre-push-checklist.md
├── scripts/
│   └── generate-worklog.py    # Generates WORKLOG.md from claude-mem records
├── templates/
│   └── worklog-pointer.md     # WORKLOG.md pointer block injected into CLAUDE.md
├── skills/
│   └── <name>/SKILL.md        # Personal skills (one directory per skill)
├── settings.json.template     # Settings template (with path placeholders)
├── install.sh                 # Install script
└── sync.sh                    # Reverse sync script
```

## Quick Start

```bash
git clone https://github.com/ingeun92/claude-code-configs.git
cd claude-code-configs
./install.sh
```

`install.sh` performs the following:

1. Backs up existing settings to `~/.claude/backups/`
2. **Copies** `RTK.md`, `rules/`, `hooks/`, `scripts/`, `templates/`, `skills/` → `~/.claude`
3. **Copies** `CLAUDE.md` → `~/.claude/CLAUDE.md`
4. Renders `settings.json.template` with path substitution and **merges** into `~/.claude/settings.json` (preserving existing plugin settings)
5. **Reports** rules, hooks, scripts, templates, and skills that exist in `~/.claude` but not in the repo

```bash
./install.sh            # report-only (default)
./install.sh --prune    # also delete the reported entries (backed up first)
```

The asymmetry with `sync.sh` is deliberate: the repo is owned entirely by this project, so `sync.sh` deletes freely, while `~/.claude` is shared with plugins and Claude Code itself, so `install.sh` never deletes unless asked. Entries owned by a plugin (a matching name under `~/.claude/plugins`) are left alone even with `--prune`.

## Dependencies (Optional)

These settings work fully when combined with the tools below.
**Always install via official channels.** This repo only manages configuration, not tool installation.

| Tool | Purpose | Install |
|------|---------|---------|
| [RTK](https://github.com/rtk-ai/rtk) | Token-saving CLI proxy | `brew install rtk` |
| [claude-mem](https://github.com/thedotmack/claude-mem) | Cross-session memory | `claude plugin install claude-mem@thedotmack` |
| [jq](https://jqlang.github.io/jq/) | Hook script dependency | `brew install jq` |

> **Install order:** Install dependencies first → run `./install.sh`. Plugin-managed fields (`enabledPlugins`, `statusLine`, etc.) in `settings.json` are preserved during merge.

## Workflow

### Syncing local changes back to the repo

```
Edit/test settings locally in ~/.claude
    │
    └→ ./sync.sh && git add && git commit
```

`sync.sh` copies modified files from `~/.claude` back to the repo. `CLAUDE.md` and `RTK.md` are copied as-is. For `settings.json`, plugin-managed fields are stripped and absolute paths are replaced with `{{CLAUDE_HOME}}`. Only files already tracked in the repo are synced (plugin-installed hooks/rules are ignored).

Deletions propagate: a rule, hook, script, template, or skill removed from `~/.claude` is removed from the repo as well, so the repo mirrors the local machine rather than accumulating leftovers. Each removal is printed as a `[WARN]` line — review `git status` before committing if you keep machine-specific files elsewhere. `CLAUDE.md` and `RTK.md` are never deleted this way.

`skills/` is the exception: every skill directory under `~/.claude/skills` is mirrored, including ones the repo does not have yet, so newly written skills are picked up automatically. Each directory is replaced wholesale, so files deleted locally also disappear from the repo. Skills that are byte-identical to a copy under `~/.claude/plugins` are detected as plugin-managed and skipped — install them via the plugin on each machine instead.

### Syncing to another machine

```bash
cd claude-code-configs
git pull
./install.sh
```

## Customization

### settings.json.template

`{{CLAUDE_HOME}}` is automatically replaced with `~/.claude` at install time.

Fields you may want to customize:

- **`permissions.allow`** — Auto-allowed tool/command patterns. Add or remove domains and commands for your projects.
- **`permissions.defaultMode`** — `"acceptEdits"` (auto-approve file edits) or `"default"` (confirm all edits)
- **`hooks`** — Add or remove hook scripts. Place new hooks in the `hooks/` directory and register them here.
- **`language`** — Claude response language
- **`effortLevel`** — `"high"`, `"medium"`, or `"low"`

### rules/

Add `.md` files to the `rules/` directory and Claude Code will automatically pick them up. One file = one rule.

### skills/

One directory per skill, each containing a `SKILL.md` with `name`/`description` frontmatter. Create it in `~/.claude/skills/<name>/`, then run `./sync.sh` — new skills are added to the repo automatically. Helper scripts under `skills/<name>/scripts/` are made executable at install time.

### scripts/

Standalone helper scripts invoked by hand or from a skill, not registered in `settings.json`. Files are made executable at install time. `generate-worklog.py` builds a project's `WORKLOG.md` from claude-mem records:

```bash
~/.claude/scripts/generate-worklog.py --project <name> --out <path>/WORKLOG.md
```

To add another script, create it in `scripts/` here first, then run `./install.sh`. Like rules and hooks, `sync.sh` only syncs files that already exist in the repo — a brand-new file in `~/.claude/scripts/` is not picked up on its own.

### templates/

Reusable markdown fragments read by those scripts. `worklog-pointer.md` is the block `generate-worklog.py` writes into a project's `CLAUDE.md` so Claude knows the `WORKLOG.md` exists. Same seeding rule as `scripts/`: add the file to the repo first, then install.

### hooks/

To add a new hook script:

1. Create the script in `hooks/` (must be `chmod +x`)
2. Register it in the `hooks` section of `settings.json.template`
3. Re-run `./install.sh`

## Caveats

- **No secrets**: Never commit files containing tokens or keys (`.mcp.json`, `.env`, etc.).
- **Absolute paths**: `settings.json` contains machine-specific absolute paths. Always use the `{{CLAUDE_HOME}}` placeholder in `settings.json.template`.
- **Plugin settings**: `enabledPlugins`, `extraKnownMarketplaces`, and `statusLine` should be managed by official plugin installation on each machine.

## License

MIT
