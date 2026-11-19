# Literature review base and gap analysis

Prepared 2026-11-19 for the term paper. This file lists the papers we found, groups them by what they tell us, and states the gaps our planned experiment can address. Nothing here is a result of our own system, because nothing is built yet. Every gap is "not found within our search", not "does not exist".

Per-paper summaries are in `summaries/`, PDFs in `papers/`, and the raw search notes in `research_notes/Load balancing literature review/`.

## How the search was done

Four searches ran on 2026-11-19: latency-aware routing in real systems, queueing theory of dispatching, empirical comparisons and surveys, and experiment methodology. Rules applied to every paper:

- Published and peer reviewed, with a DOI or an official proceedings page. arXiv-only and other preprint-only work was rejected.
- Free to read from the publisher, the venue, or an author or institutional page that hosts the published version.
- 2021 to 2026 preferred. Three older papers were kept because nothing newer covers the same point; they are marked "older" below.
- Citation details were checked against Crossref or the publisher page. Spot checks against the PDF text were done by the coordinator for L3 (formula and the 26% p99 figure), Selen et al. (SED is not exactly optimal), and Prequal (hot-cold lexicographic rule over probed requests in flight and latency).

The searches ran on a fixed token budget, so each was capped at 4 or 5 papers. Some good candidates were left out for that reason or because the publisher blocked scripted download. They are listed at the end so the team can fetch them by hand.

## Papers found

| # | Paper | Venue, year | Access | Group |
|---|---|---|---|---|
| 1 | Michaelis, Schmid, Mostafaei, "L3: Latency-aware Load Balancing in Multi-Cluster Service Mesh" | Middleware 2024, doi 10.1145/3652892.3654793 | Publisher, CC BY | Systems |
| 2 | Saokar et al., "ServiceRouter: Hyperscale and Minimal Cost Service Mesh at Meta" | OSDI 2023 | USENIX open access | Systems |
| 3 | Yassini et al., "Horus: Granular In-Network Task Scheduler for Cloud Datacenters" | NSDI 2024 | USENIX open access | Systems |
| 4 | Kaffes, Yadwadkar, Kozyrakis, "Hermod: Principled and Practical Scheduling for Serverless Functions" | SoCC 2022, doi 10.1145/3542929.3563468 | Author page | Systems |
| 5 | Gardner et al., "Scalable load balancing in the presence of heterogeneous servers" | Performance Evaluation 145, 2021, doi 10.1016/j.peva.2020.102151 | Author page, likely accepted version | Theory |
| 6 | Abdul Jaleel, Doroudi, Gardner, Wickeham, "A general power-of-d dispatching framework for heterogeneous systems" | Queueing Systems 102, 2022, doi 10.1007/s11134-022-09736-z | Author page, published version | Theory |
| 7 | Tahir, Alt, Rizk, Koeppl, "Load balancing in compute clusters with delayed feedback" | IEEE Trans. Computers 72(6), 2023, doi 10.1109/TC.2022.3215907 | Publisher, CC BY | Theory |
| 8 | Xie, Grosof, Scully, "Heavy-traffic optimal size- and state-aware dispatching" | POMACS 8(1), 2024, doi 10.1145/3639035 | Author page, published version | Theory |
| 9 | Selen et al., "Steady-state analysis of shortest expected delay routing" (older) | Queueing Systems 84, 2016, doi 10.1007/s11134-016-9497-7 | Publisher, CC BY | Theory |
| 10 | Ma and Chi, "Evaluation test and improvement of load balancing algorithms of Nginx" | IEEE Access 10, 2022, doi 10.1109/ACCESS.2022.3146422 | Publisher open access | Empirical |
| 11 | Aslanpour et al., "Load balancing for heterogeneous serverless edge computing: A performance-driven and empirical approach" | Future Generation Computer Systems 154, 2024, doi 10.1016/j.future.2024.01.020 | Publisher, CC BY | Empirical |
| 12 | Faridah and Suranegara, "Performance of load balancing algorithms on homogeneous and heterogeneous servers in on-premise environments" | JAIC 10(1), 2026, doi 10.30871/jaic.v10i1.11614 | Publisher, CC BY-SA. National journal, written in Indonesian, lower tier | Empirical |
| 13 | Lohumi et al., "Load balancing in cloud environment: A state-of-the-art review" | IEEE Access 11, 2023, doi 10.1109/ACCESS.2023.3337146 | Publisher, CC BY-NC-ND | Survey |
| 14 | Devi et al., "A systematic literature review for load balancing and task scheduling techniques in cloud computing" | Artificial Intelligence Review 57, 2024, doi 10.1007/s10462-024-10925-w | Publisher open access | Survey |
| 15 | Papadopoulos et al., "Methodological principles for reproducible performance evaluation in cloud computing" | IEEE TSE 47(8), 2021, doi 10.1109/TSE.2019.2927908 | Institutional repository, author version in IEEE format | Method |
| 16 | Kogias, Mallon, Bugnion, "Lancet: A self-correcting latency measuring tool" (older) | USENIX ATC 2019 | USENIX open access | Method |
| 17 | Abedi and Brecht, "Conducting repeatable experiments in highly variable cloud computing environments" (older) | ICPE 2017, doi 10.1145/3030207.3030229 | SPEC-hosted proceedings | Method |
| 18 | Ugedal and Kumar, "Mitigating unnecessary throttling in Linux CFS bandwidth control" | SBAC-PAD 2022, doi 10.1109/SBAC-PAD55451.2022.00044 | Not downloaded. Author copy at hdl.handle.net/11250/3055366. Summary uses the abstract only | Method |

Full author lists and page numbers are in each summary file. Copy citations into `paper/references.md` from the summaries.

Quality notes. Paper 12 is from a lower-tier national journal; use it only as an example of a confounded design, not as evidence about which rule is better. Paper 18 should not be cited for anything beyond its abstract until someone reads the full text. Papers 9, 16, and 17 are older and should be cited as background.

## What the literature says, grouped

### Our feedback rule already has a name

The rule on slide 5, (unfinished + 1) × recent average processing time, is shortest expected delay (SED) routing with the service rate estimated at run time. Selen et al. (paper 9) solve the two-server SED system exactly. Gardner et al. (paper 5) and Abdul Jaleel et al. (paper 6) study SED-style rules inside power of d dispatching. No 2021 to 2026 peer-reviewed systems paper was found that uses exactly this rule. The closest is L3 (paper 1), which sets a traffic weight of 1 / ((in-flight + 1)² × latency estimate) using EWMA or PeakEWMA. The same (pending + 1) × latency form is described for Finagle and Linkerd's Peak EWMA, but only in documentation and a 2016 blog post, which are not peer reviewed.

Prequal, our current main reference, does something different. Its own text says it probes a few servers asynchronously, collects requests in flight and a latency estimate, and picks with a "hot-cold lexicographic" rule. It is the motivation for using requests in flight and latency instead of CPU load. It is not the source of our formula.

### What theory predicts for two workers

These are predictions from the papers, to be checked by our runs, not results.

- When both workers have the same speed, SED reduces to join the shortest queue (paper 9). So in scenarios 1 and 2 the feedback rule should behave close to least unfinished requests, apart from estimate noise.
- When speeds differ, rules that ignore speed do worse, and speed information matters most at heavy load (paper 6).
- SED is not exactly optimal. It does well at low and high utilization and slightly worse than the optimal threshold policy at medium utilization (paper 9, citing earlier work).
- Delayed feedback costs little when the dispatcher accounts for the delay (paper 7). Our dispatcher only learns a processing time when a request completes, so estimates always lag.
- Size-aware dispatching can do much better than size-blind rules at high load (paper 8). All four of our rules are size-blind, so this is a ceiling we will not reach, not a competitor.

All theory papers above assume known or exponential service times and report means, not p95.

### How real systems handle stale information and probe cost

ServiceRouter (paper 2) picks the better of two on outstanding requests, and uses piggybacked or cached load with polling when it is cheap. Horus (paper 3) updates load lazily when it drifts, to avoid many dispatchers sending to the same idle worker. L3 floors weights so a backend never gets zero traffic and so keeps producing fresh samples. Our "probe idle workers" rule belongs to this group.

### What empirical comparisons show and how they are done

Dynamic rules beat static ones mainly when servers differ and load is high (papers 11, 12). On equal servers, least connections was not always better than simpler rules (paper 10). Reporting is weak: papers 10 and 12 report means only, paper 11 shows p90 and says p95 and p99 were similar, L3 repeats each experiment twice, and paper 10 states no repetitions for its load tests. 51% of the 63 studies reviewed by Devi et al. used CloudSim (paper 14).

### Methodology rules we should follow

- Decide the number of repetitions from measured variability, report the distribution and not only the mean, and use a statistical test when comparing (paper 15).
- Running alternatives back to back can show false differences: consecutive trials showed a 38% gap between identical systems (paper 17). Randomize the order of the alternatives in each round (their RMIT method).
- Use an open-loop load generator. Closed-loop clients cap outstanding requests and hide the tail. Check that the target rate was reached, and remember that confidence intervals computed from correlated samples inside one run are too narrow (paper 16).
- A CFS CPU quota throttles in bursts within each period and can throttle more than intended (paper 18 abstract, Linux kernel sched-bwc documentation). A quota-limited worker is not the same as a uniformly slower CPU.

### How published work sets weighted round-robin weights

Added 2026-11-19 after the owner asked for a published basis for our weights.

- Aslanpour et al. (paper 11, Section 4.2) profile each node and set its weight to its measured value for one metric divided by the sum of that metric over all nodes. Their throughput-aware policy uses observed throughput. This is a static, calibrated weight, which matches slide 5 ("Fixed weights set during calibration"). We use this method, calibrated per scenario.
- Prequal (NSDI 2024, Section 2) describes Google's weighted round-robin, which recomputes each replica's weight periodically as its recent queries per second divided by its CPU utilization. That is a dynamic weight, so we do not use it, but it is worth one sentence in the paper because it shows weighted round-robin in production is often not static.

With two equal workers both methods give close to 1:1, so weighted round-robin will behave like round-robin in scenarios 1 and 2. That is expected and reported.

## Gaps our project can address

G1. One design that runs RR, WRR, least connections, and an SED-style feedback rule in every scenario. Paper 12 tested static rules only on equal servers and dynamic rules only on unequal ones, so rule and server type are mixed up. Paper 10 has no feedback rule. Paper 11 has no SED-style rule. L3 compares only with round-robin and an adapted C3. Our full 4 × 3 × 3 matrix covers this, if every cell is actually run.

G2. Tail latency in small empirical comparisons. Papers 10 and 12 report means only and paper 11 shows p90. We plan mean and p95 per run.

G3. Repetition and statistics. The empirical papers repeat runs two or three times or do not say. We plan at least five runs per condition in randomized blocks, with spread reported across runs.

G4. Overhead accounting. Paper 11 discusses dispatcher overhead but does not measure it. Prequal's design goals include cutting probe overhead. We can measure dispatcher CPU and RAM, count probe requests, and charge them to the feedback rule.

G5. Theory under real conditions. SED results assume known service rates, exponential service times, and usually unlimited queues. Our two-server setup is the case that paper 9 solves exactly, but with estimated rates, real image job sizes, a bounded queue, and one CPU-quota worker. Checking whether the predicted pattern (near tie at equal speed, benefit at unequal speed and heavy load) holds there is a small, honest contribution.

G6. How heterogeneity is created. Papers 11 and 12 create it with different hardware or RAM sizes, and L3 with emulated delays. We found no peer-reviewed, free paper that relates a fixed CFS quota to p95 of a web service. Scenario 3 touches this, provided the quota period and throttling counters are recorded.

G7. Size effects inside mixed workloads. Paper 8 shows that size matters a lot at high load. A cheap analysis we can add is latency per image size class, to show whether small images wait behind large ones under each rule.

G8. Stale estimates. Dropped from scope on 2026-11-19 except for counting probes. We log probe count but do not analyze estimate age. Papers 2, 3, and 7 show this matters, but at scales and settings very different from ours.

## What the literature does not let us claim

- That the feedback rule is new. It is SED with an online speed estimate.
- That our results hold for clusters, service meshes, or public clouds. Every system paper above runs at a much larger scale.
- That a CPU quota is a faithful model of a slower machine.
- That SED is optimal. Paper 9 says it is not exactly optimal.

## Candidates the team can fetch by hand

These looked relevant and free but the publisher blocked scripted download, or the search budget ran out. Each needs the same check before use: published version, not a preprint.

- Henning et al., "When should I run my application benchmark?", FSE Companion 2025, doi 10.1145/3696630.3728563 (CC BY on ACM).
- Lin et al., "Performance interference of virtual machines: a survey", ACM Computing Surveys 55(12), 2023, doi 10.1145/3573009.
- Bhambay, Büke, Mukhopadhyay, speed-aware JSQ, Stochastic Systems 15(2), 2025, doi 10.1287/stsy.2023.0054 (CC BY).
- Choudhury, Joshi, Wang, Shakkottai, dispatching with unknown service rates, MobiHoc 2021, doi 10.1145/3466772.3467047 (CC BY).
- Ugedal and Kumar 2022, full text from hdl.handle.net/11250/3055366, to replace the abstract-only summary.
