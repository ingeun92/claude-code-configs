---
description: Safety guardrails for structural refactors and bulk renames
globs:
  - "**/*.ts"
  - "**/*.tsx"
  - "**/*.js"
  - "**/*.jsx"
  - "**/*.py"
  - "**/*.go"
  - "**/*.rs"
---

# Refactor Safety

- Before any structural refactor on a file over 300 LOC, first remove all dead code (unused imports, exports, props, debug logs) and commit the cleanup separately.
- Split multi-file refactors into phases of 5 files or fewer. Complete each phase, run verification, and wait for explicit user approval before proceeding to the next. In autonomous execution modes (autopilot, ralph, ultrawork, etc.), a passing verification for the phase substitutes for explicit user approval.
- Never report a task as complete until the project's type-checker and linter pass with zero errors. If none are configured, state that explicitly.
- When renaming any function, type, or variable, search separately for: direct calls, type-level references, string literals containing the name, dynamic imports/require(), re-exports and barrel files, and test files/mocks.
