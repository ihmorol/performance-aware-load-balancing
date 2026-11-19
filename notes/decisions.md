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
| 2026-11-19 | Real order of work: build and test locally, deploy to VMs, pilot, calibrate, freeze, dry run. Slide 4 week labels stay unchanged in the paper. | Owner, grilling session; `implementation/spec.md` |
| 2026-11-19 | Main runs on a teammate's PC with VirtualBox (the 12 logical CPU, 13.9 GB machine). Code is developed and tested as localhost processes on any laptop. Colab is not used. | Owner, grilling session |
| 2026-11-19 | Load generator and orchestrator run on the host OS of the experiment PC. Orchestrator uses plain ssh with keys and limited sudo. | Owner, grilling session |
| 2026-11-19 | Stack: Ubuntu Server 24.04 LTS, Python 3.12 on VMs and host, FastAPI, Uvicorn, HTTPX, Pillow, psutil, pytest, pinned. One shared package, one TOML config; runs record commit id and config hash. | Owner, grilling session |
| 2026-11-19 | Requests upload the image bytes; the worker returns the processed bytes. The dispatcher buffers the whole body. | Owner, grilling session |
| 2026-11-19 | Image set: seeded synthetic JPEGs. Operation: resize to half width and height (LANCZOS), JPEG quality 80. Scenario 1 uses the medium class only. | Owner, grilling session |
| 2026-11-19 | Seeded Poisson open-loop schedule. Response time from the generator's clock only; dispatcher log joined on request id. | Owner, grilling session |
| 2026-11-19 | Dispatcher sends a time budget with each request; the worker skips queued requests whose budget has passed. | Owner, grilling session |
| 2026-11-19 | Feedback estimate: EWMA of worker-reported processing time from successful and probe replies; weight chosen in the pilot. Probe after T seconds with no completion. | Owner, grilling session |
| 2026-11-19 | Reset restarts the services. A run ends when every request has a terminal outcome. Requests in the first W seconds are dropped. p95 by nearest rank over successes; throughput is successes per second. Samplers every 1 second. | Owner, grilling session |
| 2026-11-19 | Weighted round-robin calibration keeps each worker busy directly with the scenario's mix. Queue capacity set in the pilot by a stated rule. | Owner, grilling session |
| 2026-11-19 | Tests: pure select() tests plus dispatcher with fake workers, built test-first. Build in ordered slices. Spec ends with a short dry-run round of all 36 conditions. | Owner, grilling session |
