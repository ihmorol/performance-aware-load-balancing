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
| 2026-11-12 | Reference set for the paper: 12 verified papers in four tiers, listed with the claim each supports in `paper/references.md`. | Publisher records checked via USENIX, Crossref, OpenAlex on 2026-11-12 |
| 2026-11-12 | Core papers to start from: Prequal (NSDI 2024), Join-Idle-Queue (Performance Evaluation 2011), The Tail at Scale (CACM 2013). | `paper/research-notes.md`, ranking section |
| 2026-11-12 | Verified corrections over remembered and search-reported details: Sparrow authors are Ousterhout, Wendell, Zaharia, Stoica; the CSUR survey at DOI 10.1145/3281010 is by Pawan Kumar and Rakesh Kumar; the Detti and Funari LOR paper's final venue is IEEE ToNSM 2025 (DOI 10.1109/TNSM.2025.3593870), not IEEE Access; the ToN 2018 JIQ paper is by Chunpu Wang, Chen Feng, Julian Cheng (vol. 26, no. 5, pages 2309-2319), not Scully and Harchol-Balter as one search result claimed. Maglev NSDI 2016 as listed in the deck is correct. | `paper/research-notes.md`, verification record |
| 2026-11-12 | Problem definition and reference solution drafted in `paper/problem-definition.md` and `paper/reference-solution.md`; hypotheses H1 to H5 there are predictions to test, not results. | Working documents, 2026-11-12 |
| 2026-11-13 | PDF collection settled: 10 of 12 papers downloaded and content-verified in `paper/references/pdf/`. Shafiq et al. is open access but publisher-blocked from this network (manual fetch suggested in references.md). Kumar and Kumar CSUR survey is closed access; cited from DOI without a PDF. | `paper/references.md`, status table |
