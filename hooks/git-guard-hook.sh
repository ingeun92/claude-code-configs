#!/usr/bin/env bash
# Injects safety checklists for git commit and git push commands.
# - git commit: lightweight check (secrets, artifacts, dependencies)
# - git push: comprehensive check (required files, .gitignore completeness)

if ! command -v jq &> /dev/null; then
  exit 0
fi

INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

if [ -z "$CMD" ]; then
  exit 0
fi

if echo "$CMD" | grep -qE '(^|[;&|])\s*(git|rtk git)\s+push'; then
  cat ~/.claude/hooks/pre-push-checklist.md >&2
elif echo "$CMD" | grep -qE '(^|[;&|])\s*(git|rtk git)\s+commit'; then
  cat ~/.claude/hooks/pre-commit-checklist.md >&2
fi

exit 0
