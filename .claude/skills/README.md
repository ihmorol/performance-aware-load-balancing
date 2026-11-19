# Project skills for Claude Code

Claude Code loads every folder here as a skill when you open this repository. Nothing to install.

## Matt Pocock's engineering skills

The 27 skill folders here come from https://github.com/mattpocock/skills at commit `abeeaf9` (19 Nov 2026). They are the skills that repo lists in `.claude-plugin/plugin.json`. The `in-progress/` and `misc/` skills were left out. License: MIT, copied to `LICENSE-mattpocock-skills`.

Run `/setup-matt-pocock-skills` once before using `/triage`, `/to-tickets` or the other issue skills. It asks which issue tracker and labels the team uses.

`code-review` and `research` share names with Claude Code built-ins. The copies here take their place inside this repository.

To update, copy the same folders again from a newer checkout of that repo, change the commit above, and commit the result in its own commit.

## Writing skills

The writing skills (`humanlike-writing`, `humanizer`) live in `skills/` at the repository root, not here. AGENTS.md says when to load them.
