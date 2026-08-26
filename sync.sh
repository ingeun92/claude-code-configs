#!/bin/bash
set -euo pipefail

# Reverse sync: ~/.claude -> repo
# Copies modified config files back to the repo for committing.

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

# Files deleted from ~/.claude are deleted from the repo too, so the repo stays
# a faithful mirror instead of accumulating leftovers.
prune() {
  local repo_sub="$1" home_sub="$2" glob="$3"
  local entry name
  for entry in "$REPO_DIR/$repo_sub"/$glob; do
    [ -e "$entry" ] || continue
    name=$(basename "$entry")
    [ -e "$CLAUDE_HOME/$home_sub/$name" ] && continue
    rm -rf "${entry:?}"
    warn "  $repo_sub/$name removed (gone from $CLAUDE_HOME/$home_sub)"
  done
}

# --- 1. CLAUDE.md ---

if [ -f "$CLAUDE_HOME/CLAUDE.md" ] && [ ! -L "$CLAUDE_HOME/CLAUDE.md" ]; then
  cp "$CLAUDE_HOME/CLAUDE.md" "$REPO_DIR/CLAUDE.md"
  info "CLAUDE.md synced"
fi

# --- 2. RTK.md ---

if [ -f "$CLAUDE_HOME/RTK.md" ] && [ ! -L "$CLAUDE_HOME/RTK.md" ]; then
  cp "$CLAUDE_HOME/RTK.md" "$REPO_DIR/RTK.md"
  info "RTK.md synced"
fi

# --- 3. Rules ---

info ""
info "=== Rules ==="
for rule_file in "$CLAUDE_HOME"/rules/*.md; do
  [ -f "$rule_file" ] || continue
  name=$(basename "$rule_file")
  if [ -L "$rule_file" ]; then continue; fi
  if [ -f "$REPO_DIR/rules/$name" ]; then
    cp "$rule_file" "$REPO_DIR/rules/$name"
    info "  rules/$name synced"
  fi
done

prune rules rules '*.md'

# --- 4. Hooks ---

info ""
info "=== Hooks ==="
for hook_file in "$CLAUDE_HOME"/hooks/*; do
  [ -f "$hook_file" ] || continue
  name=$(basename "$hook_file")
  if [ -L "$hook_file" ]; then continue; fi
  if [ -f "$REPO_DIR/hooks/$name" ]; then
    cp "$hook_file" "$REPO_DIR/hooks/$name"
    info "  hooks/$name synced"
  fi
done

prune hooks hooks '*'

# Ensure scripts are executable
chmod +x "$REPO_DIR"/hooks/*.sh 2>/dev/null || true

# --- 5. Scripts ---

info ""
info "=== Scripts ==="
mkdir -p "$REPO_DIR/scripts"
for script_file in "$CLAUDE_HOME"/scripts/*; do
  [ -f "$script_file" ] || continue
  name=$(basename "$script_file")
  if [ -L "$script_file" ]; then continue; fi
  if [ -f "$REPO_DIR/scripts/$name" ]; then
    cp "$script_file" "$REPO_DIR/scripts/$name"
    info "  scripts/$name synced"
  fi
done

prune scripts scripts '*'

chmod +x "$REPO_DIR"/scripts/* 2>/dev/null || true

# --- 6. Templates ---

info ""
info "=== Templates ==="
mkdir -p "$REPO_DIR/templates"
for template_file in "$CLAUDE_HOME"/templates/*; do
  [ -f "$template_file" ] || continue
  name=$(basename "$template_file")
  if [ -L "$template_file" ]; then continue; fi
  if [ -f "$REPO_DIR/templates/$name" ]; then
    cp "$template_file" "$REPO_DIR/templates/$name"
    info "  templates/$name synced"
  fi
done

prune templates templates '*'

# --- 7. Skills ---

info ""
info "=== Skills ==="

# A skill in ~/.claude/skills may be a copy a plugin dropped there. Those are
# managed by plugin installation, so they must not be committed. Detect them by
# comparing against ~/.claude/plugins.
is_plugin_skill() {
  local name="$1" src="$2" candidate
  [ -d "$CLAUDE_HOME/plugins" ] || return 1
  while IFS= read -r candidate; do
    diff -rq "$src" "$candidate" >/dev/null 2>&1 && return 0
  done < <(find "$CLAUDE_HOME/plugins" -maxdepth 8 -type d -path "*/skills/$name" 2>/dev/null)
  return 1
}

mkdir -p "$REPO_DIR/skills"

for skill_dir in "$CLAUDE_HOME"/skills/*/; do
  [ -d "$skill_dir" ] || continue
  skill_dir="${skill_dir%/}"
  name=$(basename "$skill_dir")
  if [ -L "$skill_dir" ]; then continue; fi
  if is_plugin_skill "$name" "$skill_dir"; then
    warn "  skills/$name skipped (plugin-managed)"
    continue
  fi
  # Mirror the whole directory so files deleted locally disappear from the repo
  rm -rf "${REPO_DIR:?}/skills/$name"
  cp -R "$skill_dir" "$REPO_DIR/skills/$name"
  info "  skills/$name synced"
done

prune skills skills '*'

# --- 8. settings.json -> settings.json.template ---

info ""
info "=== Settings ==="

SOURCE="$CLAUDE_HOME/settings.json"
TARGET="$REPO_DIR/settings.json.template"

if [ -f "$SOURCE" ]; then
  if ! command -v jq &>/dev/null; then
    warn "jq is required for settings.json sync: brew install jq"
  else
    # Strip plugin-managed fields + replace absolute paths with placeholder
    jq 'del(.enabledPlugins, .extraKnownMarketplaces, .statusLine, .permissions.allow)' "$SOURCE" \
      | sed "s|$CLAUDE_HOME|{{CLAUDE_HOME}}|g" \
      > "$TARGET"
    info "  settings.json.template synced"
  fi
else
  warn "settings.json not found in $CLAUDE_HOME. Skipping."
fi

# --- Done ---

info ""
info "=== Reverse sync complete ==="
info ""
info "Review changes: cd $REPO_DIR && git diff"
