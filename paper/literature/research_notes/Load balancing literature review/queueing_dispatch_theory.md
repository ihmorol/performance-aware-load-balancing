# Queueing theory of dispatching to heterogeneous servers

Scope cut by coordinator to 4 papers. Summaries in paper/literature/summaries/.

## JSQ vs SED vs power-of-d vs round-robin with heterogeneous servers

### Takeaway
Speed-unaware JSQ is weak when speeds differ. SED is near-optimal for 2 servers, not exactly optimal. Speed info matters most at heavy load.

### Cited findings
- Selen et al. 2016 (foundational, older). Queueing Syst 84:309-354. DOI 10.1007/s11134-016-9497-7. Verified on PDF. Downloaded (Springer OA, CC BY). 2 exp servers, SED exact solution. JSQ not optimal with unequal rates; SED not exactly optimal either; per cited work SED good at low/high load, slightly worse at medium load; heavy-traffic optimal (pp. 310-311). Source: [Springer PDF](https://link.springer.com/content/pdf/10.1007/s11134-016-9497-7.pdf)
- Abdul Jaleel, Doroudi, Gardner, Wickeham 2022. Queueing Syst 102:431-480. DOI 10.1007/s11134-022-09736-z. Verified on PDF. Downloaded (published version, author page). JSQ-d poor under heterogeneity; SED-d and BR better; querying rule drives light load, assignment rule drives heavy load (Sect. 1). Source: [Author PDF](https://kgardner.people.amherst.edu/papers/gardner_questa_22a.pdf)

### Inferences
- 2 workers, CPU-quota scenario: feedback (SED) and WRR should beat RR and least-unfinished. Gap likely grows with load.
- Uniform scenario: SED = JSQ if rates equal; expect near tie.

### Gaps
- No verified 2023-2026 paper showing SED worse than JSQ. Not found within budget.
- No result for 2-server SED with high size variability or bounded queues.

## Unknown rates, stale info, probing cost

### Takeaway
Delayed state can still give near full-information results if the dispatcher models the delay. Learning-rate papers exist but not read in budget.

### Cited findings
- Tahir, Alt, Rizk, Koeppl 2023. IEEE TC 72(6):1610-1622. DOI 10.1109/TC.2022.3215907. Verified on PDF. Downloaded (IEEE OA, CC BY). Finite buffers, delayed acks, POMDP + MCTS policy POL. Beats limited-info baselines; comparable to full-info JSQ, JSQ(d), SED (abstract, Sect. 5). 2-server case: favors faster server, acts like JSQ/SED (Fig. 3). Source: [IEEE PDF](https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber=9925099)

### Inferences
- Our dispatcher sees completions with delay. Expect small loss vs ideal SED at 2 servers.
- Bounded queue: track rejections; Tahir uses drops as a main metric.

### Gaps
- Online rate learning (bandit) not summarized. See rejected list.
- Herding from stale info: only old or unverified sources found.

## Job-size-aware dispatching and tail latency

### Takeaway
Knowing job sizes helps a lot at high load. Our rules are size-blind, so this is a ceiling, not a competitor.

### Cited findings
- Xie, Grosof, Scully 2024. POMACS 8(1) Art. 9, 36 pp. DOI 10.1145/3639035. Verified on PDF. Downloaded (published version, author page). Identical FCFS servers, sizes known. CARD heavy-traffic optimal; example at high load: >75% lower mean delay than LWL, >50% lower than SITA (Sect. 1, Fig. 1.2). SITA can be much worse than LWL (Sect. 1). Source: [Author PDF](https://ziv.codes/pdf/sigmetrics2024-xie.pdf)

### Inferences
- Mixed-size scenario: small images behind large ones inflate mean and p95. Size-blind rules all pay this.

### Gaps
- No tail (p95) theory paper read. All 4 papers report means.
- None covers: 2-server finite systems with real overhead, CPU-quota slowdown, measurement noise in rate estimates.

## Rejected or not pursued
- Abdul Jaleel, Doroudi, Gardner 2024, Queueing Syst 108:125-184, DOI 10.1007/s11134-024-09918-x. Very relevant (queue-length-aware hetero dispatching). Paywalled. Dropped.
- Bhambay, Büke, Mukhopadhyay 2025, Stochastic Systems 15(2):147-193, DOI 10.1287/stsy.2023.0054. CC BY, relevant (speed-aware JSQ). Publisher blocks curl. Not read; budget cut.
- Choudhury, Joshi, Wang, Shakkottai 2021, MobiHoc, DOI 10.1145/3466772.3467047. CC BY, unknown service rates. ACM blocks curl. Not read; budget cut.
- Bhambay, Mukhopadhyay 2022, Perf Eval 157-158:102320. Not OA at publisher.
- Gardner et al. 2021, Perf Eval 145:102151. Covered by another researcher's summary (2021_Gardner_ScalableLB_HeterogeneousServers.md).
- Fu, Modiano 2023, IEEE/ACM ToN 31(5):1997-2012. Not OA.
- Hyytiä, Righter 2024, Perf Eval 164:102396. Not OA (SSRN preprint only).
- Goldsztajn et al. 2025, Math OR 50(2). Identical server pools; off topic; not OA checked.
- "Learning Adaptive SED" (van Kempen et al.). arXiv only. Rejected.
- Vargaftik et al. LSQ, ToN 2020. Relevant to stale info, but 2020; not checked.
