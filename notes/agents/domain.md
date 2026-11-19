# Domain docs

How the engineering skills in `.claude/skills/` read this repo's domain documentation. AGENTS.md keeps new documents out of the repository root, so the usual root `GLOSSARY.md` and `docs/adr/` live under `notes/` here.

## Before exploring, read these

- `notes/glossary.md`, the project's terms (dispatcher, worker, rule, feedback, p95, round-robin, least unfinished requests).
- `notes/adr/`, decision records that touch the area you are about to work in.
- `notes/decisions.md`, the dated decision log. It is the main record of settled choices in this repo.
- `implementation/spec.md`, the spec (PRD) for the build before the main runs.

If the glossary or ADR folder doesn't exist yet, carry on without flagging it. The `/domain-modeling` skill creates them when a term or decision actually gets settled.

## Layout

Single-context. One glossary, one ADR folder, no per-module glossaries.

## Use the project's words

Issue titles, test names, and proposals use the project terms exactly as AGENTS.md and the glossary give them. If a concept has no term yet, either the work is inventing language the project doesn't use, or there is a real gap to note for `/domain-modeling`.

## Flag conflicts

If an output contradicts `notes/decisions.md` or an ADR, say so openly instead of overriding it silently.
