# Research notes: reference ranking and core papers

Working notes from the literature search on 2026-11-12. The verified bibliographic details for every paper live in [references.md](references.md). This document answers three questions: how the papers were ranked, which two or three we start from, and what each one contributes to the build and the paper.

## How papers were selected and ranked

Selection criteria, in order:

1. Direct relevance to the research question: when does knowing each worker's recent speed improve routing enough to justify the extra monitoring?
2. Venue strength: top systems venues (NSDI, OSDI, SOSP, SIGCOMM) and strong journals (CACM, IEEE/ACM ToN, ACM Computing Surveys, IEEE TPDS).
3. Impact: citation counts and adoption in production systems.
4. Recency: 2024-2025 work preferred for the literature review, with older papers kept when they are the founding result.
5. The phase of our work the paper supports: motivation, design, implementation, evaluation, or writing.

Rejected on purpose:

- Round-robin versus least-connections comparisons in minor venues (IJCSMC, GESJ, regional journals). They overlap with our experiment but do not meet the venue bar, and our own runs are the comparison that matters.
- An RL or ML-based load balancer. Our project is explicitly not a machine-learning project, and one such citation would promise something we do not do.
- "Duet: local and global load balancing, SIGCOMM 2018". This paper does not exist in that form. The real Duet is SIGCOMM 2014 on hardware and software cloud load balancing, which overlaps with Maglev, so we dropped it.
- A commonly circulated attribution error: the CSUR survey at DOI 10.1145/3281010 is by Pawan Kumar and Rakesh Kumar, confirmed via Crossref. Some web sources attach it to Dhinesh Babu and Venkata Krishna, who wrote an earlier, different survey. We cite the Crossref record.

Verification record: every title, author list, volume, and page number in references.md was checked against USENIX pages, Crossref, or OpenAlex on 2026-11-12. Four sources failed verification and were corrected before writing anything down: the Prequal title and author list and the Sparrow author list came out different from first memory (Schwarzkopf and Konwinski are Omega authors, not Sparrow authors); the CSUR survey authorship above; and the ToN 2018 JIQ paper. Search results attributed that paper to Scully and Harchol-Balter with volume 26, number 6, pages 2804-2817, but the downloaded arXiv preprint (1709.10119) and the Crossref record for DOI 10.1109/TNET.2018.2869092 both show Chunpu Wang, Chen Feng, and Julian Cheng, volume 26, number 5, pages 2309-2319. Reading the downloaded PDF caught it; no Scully and Harchol-Balter JIQ paper exists on Crossref.

## The ranking

| Rank | Paper | Venue, year | Role in our project |
|---|---|---|---|
| 1 | Prequal | NSDI, 2024 | The feedback rule's direct ancestor |
| 2 | Join-Idle-Queue | Performance Evaluation, 2011 | The dispatcher-worker information problem |
| 3 | The Tail at Scale | CACM, 2013 | Metrics and the slow-worker motivation |
| 4 | Distributed JIQ (Wang, Feng, Cheng) | IEEE/ACM ToN, 2018 | Theory of when idle-feedback routing wins or degrades |
| 5 | The power of two choices | IEEE TPDS, 2001 | Theory behind count-based routing |
| 6 | Least Outstanding Request limitations | IEEE ToNSM, 2025 | Recent evidence that the simple rule fails |
| 7 | Sparrow | SOSP, 2013 | Stale state and sampling |
| 8 | Slicer | OSDI, 2016 | Production latency-aware balancing |
| 9 | Maglev | NSDI, 2016 | Network-layer background |
| 10 | Kumar and Kumar survey | ACM CSUR, 2019 | Literature review anchor |
| 11 | Shafiq et al. survey | JKSU-CIS, 2022 | Recent survey for freshness |
| 12 | VMs versus containers | ISPASS, 2015 | Testbed justification |

Ranks 1 to 3 are the core papers. Ranks 4 to 6 are the ones most likely to enter the design or discussion sections in depth. Ranks 7 to 12 are context and support.

## Core paper 1: Prequal

Wyrowski, Kleinberg, Rumble, and Archer describe Google's request dispatcher for latency-sensitive services at NSDI 2024. Three facts make it our starting point.

First, it states our research question at production scale. The paper's central argument is that balancing a scalar "load" is the wrong target when requests differ in cost and workers differ in speed. Our project asks the small-scale version of the same question, with the same terminology.

Second, its selection metric is the estimated finish time per worker, computed from requests in flight and the worker's recent speed. Our feedback rule, `(unfinished + 1) x recent average processing time`, is a deliberately simplified version of that metric. When an examiner asks where the formula comes from, Prequal is the citation.

Third, it documents the operational details our implementation plan needs: how estimates are refreshed, how idle workers are probed so their information does not go stale, and what overhead monitoring adds. Our probe policy and initialization plan are modeled on what it describes.

## Core paper 2: Join-Idle-Queue

Lu, Xie, Kliot, Geller, Larus, and Greenberg, published in Performance Evaluation in 2011. It is the paper that explains the structural problem behind our testbed.

Its first contribution is architectural: keep dispatchers and workers separate, and think hard about what information each side holds. Our three-VM layout is exactly this separation.

Its second contribution is the warning our project tests: dispatcher-held queue information is stale by the time it is used, because of propagation delay between assignment and completion. That staleness is the reason a dispatcher with perfect-sounding information can still route badly. Our feedback rule tries to compensate with recent timing, and our third scenario creates the strongest version of the problem by slowing one worker mid-life.

Its third contribution is the evaluation discipline: heterogeneous job sizes and unequal service rates, not only uniform work. Our three scenarios (uniform images, mixed sizes, mixed sizes with a slowed worker) follow that prescription directly.

## Core paper 3: The Tail at Scale

Dean and Barroso, Communications of the ACM, 2013. This paper shapes how we measure and report.

It establishes that users experience tail latency, so percentiles belong next to the mean in any report. Our metric list (mean response time, p95, throughput, failures, CPU and RAM) follows from it, and the corrected p95 wording in the defense guide matches its treatment.

It also names the mechanism our third scenario isolates: heterogeneity and interference in a multi-component system create long response-time tails even at moderate utilization. A slowed worker on a shared host is a small, controlled instance of exactly that mechanism.

## How the rest connect the dots

- Wang, Feng, and Cheng (ToN 2018) give the theory that calibrates our expectations: distributed idle-feedback routing reaches low response time in large systems and does not always beat simpler policies. This predicts where, across our three request rates, differences should appear, and it tells us that "feedback wins everywhere" is not what theory predicts. If our runs show that, we will say so.
- Mitzenmacher (TPDS 2001) is the theory for our least-unfinished baseline: sampling or choosing by queue count is provably strong when job sizes are similar. This frames the uniform-images scenario, where we expect the simple rules to hold their own.
- Detti and Funari (ToNSM 2025) document measured failure modes of least outstanding request routing in service meshes. This is the freshest evidence that the rule our feedback extends has known limits, which is the gap our comparison probes.
- Sparrow (SOSP 2013) reinforces the stale-state lesson from a scheduling angle and gives the sampling design point between blind and fully informed routing.
- Slicer (OSDI 2016) and Maglev (NSDI 2016) give production context: request-level and network-level balancing in real datacenters, with tail percentiles as the success metric.
- The two surveys (CSUR 2019, JKSU-CIS 2022) anchor the literature review section required by the course guidelines, one established and one recent.
- Felter et al. (ISPASS 2015) justify the VM testbed: virtualization overhead for CPU-bound work is small, with the shared-host caveat we already document.

## Mapping to the term paper sections

| Paper section | Main sources | Support |
|---|---|---|
| Introduction | Prequal, Tail at Scale | Motivation and research question |
| Background and literature review | Kumar and Kumar, Shafiq et al., Mitzenmacher, JIQ, Sparrow | Taxonomy and classical theory |
| Design discussion | Prequal, JIQ, Wang, Feng, and Cheng | Feedback formula, dispatcher-worker split, expected behavior |
| Comparative analysis | our runs, with Detti and Funari, Mitzenmacher, Tail at Scale | Interpreting where each rule helps |
| Challenges and limitations | Felter et al., Tail at Scale, Wang et al. | Shared host, virtualization, load regime |
| Future trends | Prequal, Slicer, Maglev | Production practice beyond our scope |

## What still needs doing

- The PDF collection is settled as of 2026-11-13: ten of twelve papers are downloaded and content-verified in `paper/references/pdf/`. The Shafiq et al. survey is open access but its publisher blocks this network's address, so a team member should save it from the article page in a normal browser (see the status table in references.md). The Kumar and Kumar CSUR survey is closed access; the citation stands from the DOI.
- Before drafting the paper's background section, read the downloaded PDFs of the three core papers and record which specific claims we reuse. The defense guide already notes that its own reference table does not independently verify the papers; references.md and this document are where verification gets recorded.
