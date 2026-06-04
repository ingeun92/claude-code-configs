#!/usr/bin/env bash
# Auto-allow most Bash commands, require manual approval for dangerous ones.
# A matched command falls through (exit 0) WITHOUT an allow decision, so Claude
# Code prompts the user. This is defense-in-depth, not a hard block — keep the
# patterns broad, since a missed approval prompt is the failure mode we care about.

INPUT=$(cat)
CMD=$(echo "$INPUT" | jq -r '.tool_input.command // empty')

[ -z "$CMD" ] && exit 0

# (1) Dangerous leading commands: destructive, privilege escalation, disk ops.
if echo "$CMD" | grep -qE '^\s*(rm\s+-[a-zA-Z]*[rf]|sudo\s|doas\s|shutdown|reboot|halt|poweroff|mkfs|dd\s|:\(\)\s*\{|chmod\s+-?R?\s*777|chown\s+-R|>\s*/dev/sd|git\s+push\s+.*(--force|-f\b)|git\s+reset\s+--hard|git\s+clean\s+-[a-z]*f)'; then
  exit 0
fi

# (2) Dangerous patterns ANYWHERE in the command (chained after ; && || |).
#     A leading-token check (above) is trivially bypassed by `ls; python3 -c ...`,
#     so these match regardless of position. Covers: inline interpreters,
#     encoded-payload decoding, pipe-to-shell, and reverse-shell primitives.
if echo "$CMD" | grep -qE '(python[0-9.]*\s+-c|node\s+(-e|--eval)|perl\s+-[a-zA-Z]*e|ruby\s+-e|php\s+-r|(^|[^a-zA-Z])(ba)?sh\s+-c|\beval\b|base64\s+(-d|--decode|-D)|\bxxd\s+-r\b|\|\s*(ba)?sh\b|\|\s*python|\|\s*node\b|\|\s*perl\b|\|\s*ruby\b|\|\s*php\b|\bnc\s+-[a-z]*[le]|/dev/tcp/)'; then
  exit 0
fi

# (3) Writes that tamper with shell startup or Claude config (persistence vectors).
if echo "$CMD" | grep -qE '(>>?|\btee\b)\s+[^|;&]*(\.bashrc|\.bash_profile|\.profile|\.zshrc|\.claude/settings|\.claude\.json|\.env|crontab|authorized_keys)'; then
  exit 0
fi

jq -n '{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "permissionDecisionReason": "bash-auto-allow"
  }
}'
