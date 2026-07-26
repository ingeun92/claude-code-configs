---
name: cli-checklist
description: Quality checklist for building CLI tools that AI agents or scripts will consume. Use whenever designing, implementing, or reviewing a command-line tool's interface — flags, output format, exit codes, error messages. Triggers on tasks like "build a CLI", "add a subcommand", "make this scriptable/agent-friendly", or reviewing CLI UX.
---

# Quick Reference Checklist when building a CLI tool that agents will use

[ ]  --json flag for structured output
[ ]  JSON to stdout, messages to stderr
[ ]  Meaningful exit codes (not just 0/1)
[ ]  Idempotent operations (or clear conflict handling)
[ ]  Comprehensive --help with examples
[ ]  --dry-run for destructive commands
[ ]  --yes/--force to bypass prompts
[ ]  --quiet for pipe-friendly bare output
[ ]  Consistent field names and types across commands
[ ]  Consistent noun-verb hierarchy (e.g., `noun verb`)
[ ]  Actionable error messages with error codes
[ ]  Batch operations for bulk work
[ ]  Non-interactive TTY detection
