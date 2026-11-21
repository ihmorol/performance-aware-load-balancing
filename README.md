# Performance-aware load balancing

A comparison of four load balancing rules on local virtual machines. Three Ubuntu Server VMs: one dispatcher and two image processing workers. The dispatcher routes resize and recompression requests by round-robin, weighted round-robin, least unfinished requests (least connections counted in requests), or a rule that tracks each worker's recent processing time. We measure response time, throughput, failures, and resource use across three scenarios: uniform images, mixed sizes, and mixed sizes with one slowed worker.

The research question: when does knowing each worker's recent speed improve routing enough to justify the extra monitoring?

Our contribution is a fair, repeatable comparison. Not a new algorithm, and no claim that the feedback rule always wins.

## Status

The proposal stage is done. Its artifacts are frozen in `final/`. The current plan is `paper/revised-proposal.md` (2026-11-19), which keeps the frozen theme and fixes wording and open details. The build follows `implementation/spec.md` in the issue order of `implementation/ORCHESTRATION.md`. As of 2026-11-21, issue #2 (the shared package, config loader, image set generator, and worker) is merged. The dispatcher (#3), load generator (#4), orchestrator (#5), VM setup (#6), and pilot tools (#7) are not built yet. No experiment has run and `results/` holds no measurements. After the build: the pilot, the three scenarios, and the term paper (10 to 15 pages, at least 8 references, per the course guidelines).

## Team and proposal slides

| Member | Slides | Focus |
|---|---|---|
| Mahim | 1 to 3 | Motivation and research question |
| Ikramul | 4 to 6 | Objectives, rules, architecture |
| Omlan | 7, 8, 10 | Experiment plan, contributions, closing |

Slide 9 (references) is backup only. The talk goes from slide 8 to slide 10.

## Finalized files

All five live in [final/](final/):

- `Performance-Aware Load Balancing.pptx`, the slide deck
- `Performance-Aware Load Balancing.pdf`, the same deck as PDF
- `Cloud_Load_Balancing_Presentation_Guide.docx`, the per-slide speaking guide
- `Performance_Aware_Load_Balancing_Defense_Study_Guide_EN_BN.md`, defense prep in simple English and Bangla
- `Cloud Computing Project_Term paper Guidelines.pdf`, the course requirements

New to the project? Read the defense study guide first, then the deck.

## Layout

| Path | Contents |
|---|---|
| `final/` | Frozen deliverables, do not edit |
| `paper/` | Term paper workspace |
| `implementation/` | Dispatcher, workers, experiments (worker built, the rest to be built) |
| `results/` | Measurements, one folder per scenario |
| `notes/` | Decisions and open questions |
| `skills/` | The writing rules used across this repo |

## Writing rules

Every document here follows [AGENTS.md](AGENTS.md). In short: use the words the team already uses, otherwise simple common words, skip AI-typical vocabulary and patterns, and never dress up planned work as finished work. The full rulebook is vendored in `skills/`.

## For AI agents

Read [AGENTS.md](AGENTS.md) before writing anything. It is binding.
