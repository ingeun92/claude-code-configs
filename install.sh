#!/bin/bash
set -euo pipefail

# Claude Code global settings installer
# Copies config files from this repo into ~/.claude with smart merging.

REPO_DIR="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_HOME="${CLAUDE_HOME:-$HOME/.claude}"

PRUNE=false

for arg in "$@"; do
  case "$arg" in
    --prune) PRUNE=true ;;
    -h|--help)
      echo "Usage: ./install.sh [--prune]"
      echo ""
      echo "  --prune  Also delete rules/hooks/scripts/templates/skills that exist"
      echo "           locally but not in this repo. Without it they are only"
      echo "           reported. Plugin-managed entries are never deleted."
      exit 0
      ;;
    *)
      echo "Unknown option: $arg (try --help)" >&2
      exit 1
      ;;
  esac
done

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# --- Validation ---

if [ ! -d "$CLAUDE_HOME" ]; then
  error "$CLAUDE_HOME does not exist. Install Claude Code first."
  exit 1
fi

# --- Backup ---

BACKUP_DIR="$CLAUDE_HOME/backups/config-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BACKUP_DIR"
info "Backing up existing settings: $BACKUP_DIR"

backup_if_exists() {
  local target="$1"
  if [ -e "$target" ] && [ ! -L "$target" ]; then
    cp -r "$target" "$BACKUP_DIR/"
    info "  Backed up: $(basename "$target")"
  fi
}

# --- Copy helper ---

copy_file() {
  local src="$1"
  local dest="$2"

  backup_if_exists "$dest"

  # Remove existing symlink if present (migration from old symlink approach)
  if [ -L "$dest" ]; then
    rm "$dest"
  fi

  cp "$src" "$dest"
  info "  Copied: $(basename "$dest")"
}

# --- Orphan check ---

# Unlike the repo, $CLAUDE_HOME is shared with plugins and Claude Code itself,
# so entries missing from the repo are reported rather than deleted by default.
# Anything a plugin owns is left alone even with --prune.
is_plugin_owned() {
  local kind="$1" name="$2"
  [ -d "$CLAUDE_HOME/plugins" ] || return 1
  find "$CLAUDE_HOME/plugins" -maxdepth 8 -path "*/$kind/$name" 2>/dev/null | grep -q .
}

report_orphans() {
  local sub="$1" glob="$2"
  local entry name
  [ -d "$CLAUDE_HOME/$sub" ] || return 0
  for entry in "$CLAUDE_HOME/$sub"/$glob; do
    [ -e "$entry" ] || continue
    name=$(basename "$entry")
    [ -e "$REPO_DIR/$sub/$name" ] && continue
    if is_plugin_owned "$sub" "$name"; then
      info "  Left alone: $sub/$name (plugin-managed)"
      continue
    fi
    if [ "$PRUNE" = true ]; then
      backup_if_exists "$entry"
      rm -rf "${entry:?}"
      warn "  Removed: $sub/$name (not in repo)"
    else
      warn "  Not in repo: $sub/$name (run with --prune to delete)"
    fi
  done
}

copy_dir() {
  local src="$1"
  local dest="$2"

  backup_if_exists "$dest"

  if [ -L "$dest" ]; then
    rm "$dest"
  fi

  # Replace wholesale so files removed upstream do not linger
  rm -rf "$dest"
  cp -R "$src" "$dest"
  info "  Copied: $(basename "$dest")/"
}

# --- 1. CLAUDE.md ---

info ""
info "=== CLAUDE.md ==="

if [ -f "$REPO_DIR/CLAUDE.md" ]; then
  copy_file "$REPO_DIR/CLAUDE.md" "$CLAUDE_HOME/CLAUDE.md"
fi

# --- 2. RTK.md ---

info ""
info "=== RTK.md ==="

if [ -f "$REPO_DIR/RTK.md" ]; then
  copy_file "$REPO_DIR/RTK.md" "$CLAUDE_HOME/RTK.md"
fi

# --- 3. Rules ---

info ""
info "=== Rules ==="

mkdir -p "$CLAUDE_HOME/rules"

for rule_file in "$REPO_DIR"/rules/*.md; do
  [ -f "$rule_file" ] || continue
  name=$(basename "$rule_file")
  copy_file "$rule_file" "$CLAUDE_HOME/rules/$name"
done

report_orphans rules '*.md'

# --- 4. Hooks ---

info ""
info "=== Hooks ==="

mkdir -p "$CLAUDE_HOME/hooks"

for hook_file in "$REPO_DIR"/hooks/*; do
  [ -f "$hook_file" ] || continue
  name=$(basename "$hook_file")
  copy_file "$hook_file" "$CLAUDE_HOME/hooks/$name"
done

report_orphans hooks '*'

# Ensure scripts are executable
chmod +x "$CLAUDE_HOME"/hooks/*.sh 2>/dev/null || true

# --- 5. Scripts ---

info ""
info "=== Scripts ==="

if [ -d "$REPO_DIR/scripts" ]; then
  mkdir -p "$CLAUDE_HOME/scripts"

  for script_file in "$REPO_DIR"/scripts/*; do
    [ -f "$script_file" ] || continue
    name=$(basename "$script_file")
    copy_file "$script_file" "$CLAUDE_HOME/scripts/$name"
  done

  report_orphans scripts '*'

  chmod +x "$CLAUDE_HOME"/scripts/* 2>/dev/null || true
else
  warn "scripts/ not found in repo. Skipping."
fi

# --- 6. Templates ---

info ""
info "=== Templates ==="

if [ -d "$REPO_DIR/templates" ]; then
  mkdir -p "$CLAUDE_HOME/templates"

  for template_file in "$REPO_DIR"/templates/*; do
    [ -f "$template_file" ] || continue
    name=$(basename "$template_file")
    copy_file "$template_file" "$CLAUDE_HOME/templates/$name"
  done

  report_orphans templates '*'
else
  warn "templates/ not found in repo. Skipping."
fi

# --- 7. Skills ---

info ""
info "=== Skills ==="

if [ -d "$REPO_DIR/skills" ]; then
  mkdir -p "$CLAUDE_HOME/skills"

  for skill_dir in "$REPO_DIR"/skills/*/; do
    [ -d "$skill_dir" ] || continue
    skill_dir="${skill_dir%/}"
    name=$(basename "$skill_dir")
    copy_dir "$skill_dir" "$CLAUDE_HOME/skills/$name"
  done

  report_orphans skills '*'

  # Skill bundles may ship helper scripts
  chmod +x "$CLAUDE_HOME"/skills/*/scripts/* 2>/dev/null || true
else
  warn "skills/ not found in repo. Skipping."
fi

# --- 8. Merge settings.json ---

info ""
info "=== Settings ==="

TEMPLATE="$REPO_DIR/settings.json.template"
TARGET="$CLAUDE_HOME/settings.json"

if [ ! -f "$TEMPLATE" ]; then
  warn "settings.json.template not found. Skipping."
else
  # Replace {{CLAUDE_HOME}} placeholder with actual path
  RENDERED=$(sed "s|{{CLAUDE_HOME}}|$CLAUDE_HOME|g" "$TEMPLATE")

  if [ -f "$TARGET" ]; then
    # Merge: use template as base, overlay plugin-managed fields from existing settings
    backup_if_exists "$TARGET"

    EXISTING="$TARGET"
    PLUGIN_FIELDS=$(jq '{
      enabledPlugins: .enabledPlugins,
      extraKnownMarketplaces: .extraKnownMarketplaces,
      statusLine: .statusLine
    } | with_entries(select(.value != null))' "$EXISTING" 2>/dev/null || echo '{}')

    echo "$RENDERED" | jq --argjson plugins "$PLUGIN_FIELDS" '. + $plugins' > "$TARGET"
    info "  settings.json merged (template + existing plugin settings preserved)"
  else
    # No existing file — create from template
    echo "$RENDERED" > "$TARGET"
    info "  settings.json created"
  fi
fi

# --- Done ---

info ""
info "=== Installation complete ==="
info ""
info "Install the following dependencies via official channels:"
info "  - oh-my-claudecode: claude plugin install oh-my-claudecode@omc"
info "  - RTK:              cargo install rtk"
info "  - claude-mem:       claude plugin install claude-mem@thedotmack"
info "  - jq:               brew install jq"
info ""
info "Backup location: $BACKUP_DIR"
info ""
info "To update after git pull: re-run ./install.sh"
