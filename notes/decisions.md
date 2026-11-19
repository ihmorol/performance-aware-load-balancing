# Decisions

Confirmed choices, newest last. Each entry names its source.

| Recorded | Decision | Source |
|---|---|---|
| 2026-11-12 | Compare four rules: round-robin, weighted round-robin, least connections, recent processing time feedback. | Defense study guide, `final/` |
| 2026-11-12 | Three local VMs: dispatcher (1 GB RAM, 1 vCPU), two workers (2 GB RAM, 1 vCPU each), Ubuntu Server. | Slide deck, `final/` |
| 2026-11-12 | Workload: image resize and recompression. | Slide deck, `final/` |
| 2026-11-12 | Three scenarios: uniform images, mixed images, mixed images with one slowed worker (Linux CPU quota). | Defense study guide |
| 2026-11-12 | Metrics: response time (mean and p95), throughput, failures, CPU and RAM use. | Defense study guide |
| 2026-11-12 | Contribution framed as a fair, repeatable comparison. No new algorithm claimed. | Defense study guide |
| 2026-11-12 | Talk slides are 1 to 8 and 10; slide 9 (references) is backup only. | Defense study guide |
| 2026-11-12 | Speaker split: Mahim 1 to 3, Ikramul 4 to 6, Omlan 7, 8, and 10. | Defense study guide |
| 2026-11-12 | Repository structure and writing rules set; superseded proposal drafts removed (backup kept outside the repo). | Owner instruction, 2026-11-12 |
| 2026-11-19 | Research question reworded to "workers have unequal speed". The slowed worker has a fixed quota; a dynamic slowdown scenario is future work, not planned. | Owner, scope review 2026-11-19 |
| 2026-11-19 | Novelty claim: every rule in every scenario, p95 per run and per image size class, monitoring overhead charged to the feedback rule. No new algorithm. | Owner, scope review 2026-11-19 |
| 2026-11-19 | Weighted round-robin weights proportional to profiled throughput, calibrated per scenario before main runs (Aslanpour et al., FGCS 2024, Section 4.2). | Owner asked for a published method; `paper/literature/gap-analysis.md` |
| 2026-11-19 | The written proposal PDF cited by the defense guide is superseded. `paper/revised-proposal.md` is the technical reference; `final/` stays frozen. | Owner, scope review 2026-11-19 |
| 2026-11-19 | Rule 3 is named "least unfinished requests" (least connections counted in requests). | Triage default from `notes/proposal-audit.md` A2; owner may change |
| 2026-11-19 | Slowed worker uses systemd CPUQuota on the worker service inside the VM; quota and period set in the pilot. | Triage default, audit C6; owner may change |
| 2026-11-19 | Five shuffled rounds of 36 conditions (180 main runs). Report median with min and max; a difference is "clear" only when five-run ranges do not overlap. No significance tests. | Triage default, audit C4 and C5; owner may change |
| 2026-11-19 | Load generator is open loop with a seeded schedule shared by all rules. | Audit C3 |
