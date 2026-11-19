# Performance-aware load balancing: revised proposal

Revised 2026-11-19. This revision keeps the frozen proposal in `final/` as the base: same question family, same four rules, same three-VM testbed, same three scenarios, same metrics. It changes wording that promised too much, fills in details the proposal left open, and states the novelty claim more carefully, using the literature in `paper/literature/gap-analysis.md`. Nothing here is a result. The system is not built yet.

The frozen deck and guides are not edited. Where this document and `final/` differ, this document is the current plan, and the reason is listed in the last section.

## Research question

Which routing rule keeps response time low when request sizes differ and workers have unequal speed, and does knowing each worker's recent processing time pay for the extra monitoring it needs?

The frozen slide 3 said "worker speed changes". Our slowed worker has a fixed CPU quota for the whole run, so we test unequal speed, not change over time. Change over time moves to future work.

## What is new, and what is not

The four rules are not new. The feedback rule, (unfinished + 1) × recent average processing time, is the known shortest expected delay (SED) rule with the processing time measured at run time. Prequal (NSDI 2024) motivates using requests in flight and latency instead of CPU load, but we do not reproduce Prequal.

The contribution is the comparison. In our search (18 papers, `paper/literature/gap-analysis.md`) we did not find a recent peer-reviewed study that does all three of these in one small testbed:

1. Runs round-robin, weighted round-robin, least unfinished requests, and an SED-style feedback rule in every scenario, so rule and scenario are never mixed up.
2. Reports p95 per run and p95 per image size class, so we can see whether small images wait behind large ones under each rule.
3. Charges the feedback rule for its monitoring cost: probe requests, dispatcher CPU, and time spent choosing a worker.

We claim this only for our setup: two workers and one dispatcher on one host, one image workload.

## Objectives

Unchanged from slide 4: build the testbed, implement the four rules, run repeatable tests, analyze and report.

## System

Unchanged from the frozen proposal. Three Ubuntu Server VMs on VirtualBox on one host (13.9 GB RAM, 12 logical CPUs per the frozen documents): a dispatcher (1 GB, 1 vCPU) and two workers (2 GB, 1 vCPU each) on a host-only network. Python asyncio, FastAPI, HTTPX on the dispatcher; FastAPI and Pillow on the workers. Each worker processes one image at a time and holds a bounded queue. The worker returns its processing time with every reply.

## The four rules

All four share one forwarding path in the dispatcher. Only the selection step changes. No rule retries a failed request. Ties alternate between workers.

1. Round-robin. Strict alternation.
2. Weighted round-robin. Fixed weights proportional to each worker's profiled throughput, following the throughput-aware weighting in Aslanpour et al. (FGCS 2024, Section 4.2): weight of a worker = its measured throughput ÷ the sum of both workers' throughput. Throughput is profiled in a separate calibration run for each scenario, with that scenario's image mix, before the main runs. Weights are not changed after that. When both workers are equal, the calibrated ratio will be close to 1:1 and weighted round-robin will behave like round-robin. We report that as an expected outcome and a check of the setup, not as a weakness.
3. Least unfinished requests. Pick the worker with fewer unfinished requests, counting running and waiting requests at the dispatcher. This is the least connections idea counted in requests, not TCP connections.
4. Feedback rule (SED-style). Pick the worker with the smaller (unfinished + 1) × recent average processing time. The averaging method and its size are fixed in the pilot and not tuned after the main runs. A worker with no completed request for a fixed time gets one small probe image. Probes are counted and reported as overhead.

Weighted round-robin gets advance knowledge of the slowed worker through calibration. The feedback rule has to learn it at run time. The paper states this difference.

## Scenarios and load

The three scenarios stay: uniform images, mixed sizes, mixed sizes with one worker slowed by a fixed Linux CPU quota. The quota is applied with systemd CPUQuota on the worker service inside the VM. The quota value and period are chosen in the pilot and recorded, and the throttling counters in cpu.stat are read before and after each run. We call this worker "CPU-quota-limited", not "a slower machine", because a quota pauses the worker in bursts.

The load generator runs open loop. Send times and image choices are generated from a seed before each run, and every rule gets the same schedule for the same scenario and rate. Requests are sent at their planned times whether or not earlier replies have arrived. Three rates are chosen in the pilot from the measured capacity: one light, one where queues form, one close to overload.

## Matrix and repetitions

4 rules × 3 scenarios × 3 rates = 36 conditions, every rule in every scenario. Five rounds give 180 main runs. Each round runs all 36 conditions once in an order shuffled with a saved seed. Pilot and calibration runs are extra.

## Metrics

Per run: mean and p95 response time over successful requests, p95 per image size class (scenarios 2 and 3), successful throughput next to the offered rate, failures by type (rejected, timed out, error), CPU and RAM per VM, dispatcher CPU time, time to choose a worker, probe count, and the achieved sending rate. A run that misses its planned rate by more than a tolerance set in the pilot is kept and flagged.

Below overload, throughput should be close to the offered rate for every rule, so throughput differences are expected mainly at the highest rate.

## Analysis

We compute each metric per run, then compare across the five runs of a condition. We report the median of the five values with their minimum and maximum. We call a difference between two rules clear only when their five-run ranges do not overlap. Otherwise we report "no clear difference under these conditions". We do not pool requests from different runs, and we do not claim statistical significance.

## Expected pattern

Written down before any run, to be reported as held, not held, or unclear.

- H1. In the uniform and mixed scenarios, the feedback rule and least unfinished requests show no clear difference, because SED reduces to join the shortest queue when worker speeds are equal (Selen et al., Queueing Systems 2016).
- H2. In the slowed-worker scenario, the feedback rule and weighted round-robin have lower p95 than round-robin and least unfinished requests, and the gap is larger at the highest rate (Abdul Jaleel et al., Queueing Systems 2022).
- H3. At the lightest rate, the four rules show no clear difference.

A result against any of these gets the same care in the paper as one that supports it.

## What we do not claim

- A new algorithm.
- Results for public clouds, clusters, or more than two workers.
- That a CPU quota behaves like a slower CPU.
- That SED is optimal. Theory says it is not exactly optimal.
- Adaptation to a worker whose speed changes during a run.
- Cost or energy savings.

## Deliverables

Source code, the seeded image set or its generator, configuration, raw CSV logs, analysis scripts, plots, the VM setup guide, the 10 to 15 page term paper, and a demo. "Reproducible" means others can rerun the procedure and inspect every step, not that they will get identical numbers on other hardware.

## Schedule

Unchanged from slide 4. Week 1 pilot and calibration, weeks 2 to 3 implementation, weeks 4 to 5 main runs, week 6 analysis, weeks 7 to 8 report and demo.

## References

The six frozen references stay. Felter et al. (ISPASS 2015) stays only if the paper discusses virtualization overhead. Added from `paper/literature/gap-analysis.md`, each for one claim:

| Reference | Claim it supports |
|---|---|
| Selen et al., Queueing Systems 84, 2016 | Our feedback rule is SED; SED equals join the shortest queue at equal speeds; SED is not exactly optimal |
| Gardner et al., Performance Evaluation 145, 2021 | SED-style dispatching with heterogeneous servers |
| Abdul Jaleel et al., Queueing Systems 102, 2022 | Speed-unaware rules do worse when speeds differ, most at heavy load |
| Michaelis et al., L3, Middleware 2024 | Closest recent systems use of (in-flight + 1) and latency |
| Aslanpour et al., FGCS 154, 2024 | How we set weighted round-robin weights; dynamic rules gained mainly under heavy load with unequal nodes |
| Devi et al., Artificial Intelligence Review 57, 2024 | Most load balancing studies use simulation |
| Papadopoulos et al., IEEE TSE 47(8), 2021 | Repeated runs and reporting the spread |
| Abedi and Brecht, ICPE 2017 | Shuffled run order |
| Kogias et al., Lancet, USENIX ATC 2019 | Open-loop load generation and achieved-rate checks |

## Changes from the frozen proposal

| Frozen wording or gap | Revised | Why |
|---|---|---|
| "worker speed changes" (slide 3) | "workers have unequal speed" | The quota is fixed during a run |
| "Basis: Prequal (NSDI 2024)" (slide 3) | Prequal motivates the signals; our rule is SED-style | Prequal uses probing and a hot-cold rule, not our formula |
| "Feedback rule" with no name in the literature | SED-style feedback rule | A reviewer will recognize SED |
| Weights "set during calibration", method open | Profiled throughput per scenario, Aslanpour et al. Section 4.2 | A published, simple method |
| Slide 7 shows 3 filled cells | Full 36-condition matrix | Every rule runs in every scenario |
| "Least connections" in some repo files | Least unfinished requests (least connections counted in requests) | One name, matching the deck |
| "Timed requests" | Open-loop seeded schedule | A closed-loop client hides slow replies |
| "Varied run order" | Five rounds, each fully shuffled with a saved seed | Back-to-back runs can show false differences |
| Mean and p95 overall | Plus p95 per image size class | Shows the slide 2 problem directly |
| "Extra overhead" not defined | Dispatcher CPU, select time, probe count | Makes the overhead question answerable |
| No rule for "meaningful difference" | Non-overlapping five-run ranges | Simple and stated before the runs |
| Written proposal PDF cited by the defense guide | Superseded by this document | Owner decision, 2026-11-19 |
