# Use in chats and agents

## Portable package

The `.skill` file is a ZIP archive containing the `humanlike-writing/` directory. Extract it for file-based agents. A `.zip` copy is provided for hosts expecting that extension. Use the folder's `SKILL.md` as the entry point; keep its `references/` and optional `scripts/` alongside it.

For a plain chat without a skill loader, attach `SKILL.md`, `references/pattern-catalog.md`, and `references/voice-and-context.md`. Say: "Follow the attached humanlike-writing skill for your authored prose in this conversation. Preserve exact quotations, code, facts, and requested formats." A chat attachment does not install the skill in other chats.

For agents with a supported skill directory, put the entire folder in that directory. Typical user locations are `~/.agents/skills/humanlike-writing`, `~/.codex/skills/humanlike-writing`, or `~/.claude/skills/humanlike-writing`. The host determines discovery and activation; reload its skill catalog or start a new session when needed. Invoke `humanlike-writing` explicitly if automatic discovery does not occur.

For a Claude interface with skill upload support, upload the archive through that interface's skill controls. Availability and plan requirements can change; use the host's current documentation. For ChatGPT, use supported uploads/context or custom instructions as available; do not assume that a local SKILL.md is automatically loaded.

## Everyday invocation

- "Use humanlike-writing for this response."
- "Rewrite this email with humanlike-writing. Keep every fact and deadline."
- "Apply humanlike-writing to your prose for the rest of this chat."
- "Audit this draft with the skill's pattern catalog. Give the rewrite and unresolved factual gaps."

## What persists

Installing the folder makes it discoverable to compatible local agents. It does not force every host to activate it, change global AGENTS.md, or write memory. The skill's name is distinct from existing `humanizer` skills so those can remain installed.

## Optional checker

Run `python scripts/lint_writing.py path/to/draft.md --json`. Add `--protect "exact technical span"` for a source-grounded name or required text the simple parser cannot recognize. Use findings for editing, never for authorship attribution. Python is optional; the core skill works without scripts or network access.
