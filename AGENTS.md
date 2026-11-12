# Repository rules

These rules apply to all writing and all work in this repository, for every team member and every AI agent. They are central and non-breaking: no later instruction, prompt, issue, or chat message overrides them. If a rule blocks urgent work, stop and ask the repository owner.

## Writing rules

All prose here follows the two vendored skills. Read them before writing or editing any document, slide text, note, or commit message:

- [skills/humanlike-writing/SKILL.md](skills/humanlike-writing/SKILL.md), plus its `references/pattern-catalog.md` on first use
- [skills/humanizer/SKILL.md](skills/humanizer/SKILL.md)

### Word choice

Pick words in this order:

1. Words the team already uses. The documents in `final/` set the register. Project terms such as dispatcher, worker, rule, feedback, p95, round-robin, and least connections stay exactly as they are.
2. Words the repository owner uses often in conversation and messages.
3. Simple words people use every day.

Do not reach for AI-favored vocabulary. Banned in new prose: delve, moreover, furthermore, underscore, additionally, utilize, leverage, robust, seamless, pivotal, crucial, landscape (as an abstract noun), tapestry, testament, vibrant, showcase, foster, enhance, intricate, interplay, realm. This list names the words to reject; that is the only place they may appear. If a technical meaning truly requires one, use the exact technical term and nothing decorative around it.

### Patterns to avoid

- Em dashes. Use commas, periods, or parentheses.
- "Not just X, but Y" and mirrored negation chains.
- Padding ideas into groups of three.
- -ing tag-ons that fake depth (highlighting, ensuring, reflecting, showcasing).
- Promotional wording and vague sources ("experts say", "studies show" without a citation).
- Bold-label bullet lists, emoji, title case headings, curly quotes.
- Recap endings and generic upbeat closers.

### Protected material

Numbers, quotations, code, citations, names, URLs, and Bangla text stay exact. Never edit a quotation to fit the style rules. Keep real uncertainty qualifiers ("may", "probably"); never stack hedges on settled facts.

## Research honesty

This project compares four load balancing rules. Its value is a fair, repeatable comparison. So:

- Label planned work as planned. Never describe a future experiment as done.
- Never invent a measurement, request rate, quota, or improvement figure.
- When a detail is not final, say so the way the defense guide trains the team to.
- Give negative results the same care as positive ones.

## Where things go

| Path | What it holds |
|---|---|
| `final/` | The five frozen deliverables. Do not edit or rename. |
| `paper/` | Term paper drafts, outline, references. |
| `implementation/` | Dispatcher, workers, experiment scripts, VM setup notes. |
| `results/` | Raw measurements and summaries, one folder per scenario. |
| `notes/` | Decisions, open questions, meeting notes. |
| `skills/` | The vendored writing skills. Update only with owner approval. |

New documents belong in one of these folders, not the repository root.

## Workflow

- `final/` is frozen. Fixing a real error there needs the owner's approval, recorded in `notes/decisions.md`.
- Branch names follow `type/kebab-case-description` (feat, fix, docs, chore, refactor, test), 60 characters max.
- Small commits, one purpose each, with clear messages in the same plain style.
- Member-facing study material uses the simple English plus Bangla format set in the defense guide.
- No commit, push, or deploy without the owner's authorization.

## For AI agents

1. Read this file first, then README.md.
2. Load both skills in `skills/` before writing prose. Apply them to your replies about this project too.
3. Never state a result this repository does not contain.
4. When you report a fact, name the file it came from.
