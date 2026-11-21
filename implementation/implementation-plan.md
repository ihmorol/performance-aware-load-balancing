# Implementation plan

Updated 2026-11-19 after the owner's scope review. This plan builds what `paper/revised-proposal.md` describes and nothing more. Audit items (A1 to C9) are in `notes/proposal-audit.md`, with a keep, simplify, or drop status for each. Nothing is built yet, and no value here is a measured result. Where a number is still open, the plan says how the pilot decides it.

The grilling session later the same day produced `implementation/spec.md`, which settles many details this plan leaves open (expired requests, the generator log, cpu.stat in every scenario, the real order of work). Where the two differ, the spec wins. Since 2026-11-19 the worker and shared package are built (issue #2); the rest is not.

The weeks follow slide 4: week 1 pilot, weeks 2 to 3 implementation, weeks 4 to 5 main runs, week 6 analysis, weeks 7 to 8 report and demo.

## Decisions already made

All recorded in `notes/decisions.md`.

| Topic | Decision | Audit link |
|---|---|---|
| Novelty | Full comparison, per-run p95, p95 per image size class, overhead charged to the feedback rule | C7, C9 |
| Research question | "workers have unequal speed"; no dynamic slowdown scenario | B2 |
| Weighted round-robin | Weights proportional to profiled throughput per scenario (Aslanpour et al. 2024, Section 4.2) | A5 |
| Proposal PDF | Superseded by `paper/revised-proposal.md` | A4 |
| Rule 3 name | Least unfinished requests | A2 |
| CPU quota | systemd CPUQuota on the worker service inside the VM | C6 |
| Analysis | Five rounds; median with min and max; "clear" only when five-run ranges do not overlap | C4, C5 |

## Week 1: testbed, pilot, calibration

### Testbed

1. Create the three VMs in VirtualBox (dispatcher 1 GB, 1 vCPU; workers 2 GB, 1 vCPU each) on one host-only network.
2. Write `implementation/setup/README.md` with VirtualBox, Ubuntu, kernel, cgroup, and Python versions. Pin packages in `requirements.txt`.
3. Write a reset script: stop services, clear worker queues, reset dispatcher state, remove any quota, restart services. List in the README exactly what it resets.
4. Close other host applications during runs. Log host CPU with a simple sampler.

### Pilot (not part of the 180 main runs)

1. Image set. A seeded script builds the set. Time each image alone on a worker several times, group images into size classes (for example small, medium, large), and fix the mixed proportion.
2. Capacity. Increase the open-loop rate against the two-worker system until queues grow without limit. Do this for the uniform mix, the mixed mix, and with the quota on.
3. Rates. Pick three rates per scenario from that capacity: light, queues forming, near overload. Record the method and values in `notes/decisions.md`.
4. Bottleneck check. At the top rate, the load generator and dispatcher must keep up (achieved rate matches plan, their CPU well below full). Fix or disclose before main runs.
5. Spread check. Repeat one condition 5 times and look at per-run p95. This tells us whether the "non-overlapping ranges" rule can show anything; if the spread is huge, say so in the paper rather than adding runs.
6. Quota. Choose quota and period, apply, and confirm the cpu.stat throttling counters increase during a run.
7. Feedback estimate. Choose the averaging method (window or EWMA) and its size. Fix it.
8. Run length, warm-up, and drain. Choose so 180 runs plus resets fit in weeks 4 to 5 with spare time.

### Weighted round-robin calibration

For each scenario, run a calibration with that scenario's image mix and measure each worker's throughput when kept busy. Weight = worker throughput ÷ sum of both. Round to a small integer ratio and record it. Expect close to 1:1 in scenarios 1 and 2.

## Weeks 2 to 3: build

### Worker (`implementation/worker/`)

- FastAPI under Uvicorn, one process.
- One processing slot: a bounded asyncio queue feeding one consumer. A full queue returns HTTP 503 at once.
- Pillow work runs in a thread so the server keeps accepting requests. Time only that work with time.perf_counter and return it in a response header.
- No output caching.
- A health endpoint that does no image work.

### Dispatcher (`implementation/dispatcher/`)

- One forwarding path: receive, select, forward with one shared HTTPX client and a fixed timeout, return. Only `select()` differs per rule.
- Per-worker state: unfinished count, recent processing time estimate, last completion time, tie counter.
- Unfinished count rises on assignment and falls on any terminal outcome (success, 503, error, timeout).
- Rules: round-robin; smooth weighted round-robin with the calibrated weights; least unfinished requests; feedback = smallest (unfinished + 1) × estimate.
- Start-up: the same few warm-up requests to each worker before every run, for every rule, so all rules start from the same state.
- Probe (feedback rule only): a worker with no completion for a fixed time gets one small fixed image. Probes are logged with a flag.
- No retries.
- Log one CSV row per request: run id, rule, scenario, rate, request id, image id, size class, planned and actual send time, chosen worker, unfinished counts and estimates at decision time, select time, worker processing time, status, response time, probe flag.

### Load generator (`implementation/experiments/`)

- Seeded open-loop schedule, identical for every rule in a scenario and rate.
- Sends at planned times regardless of replies.
- Response time measured from the planned send time; actual send time logged as a check.
- Achieved rate per run; runs that miss the tolerance are flagged, not dropped.

### Monitoring

- psutil sampler on each VM writing CPU and RAM to CSV.
- Dispatcher process CPU time at start and end of each run.
- cpu.stat throttling counters before and after each scenario 3 run.

### Tests (pytest)

- Each rule on hand-made states, including Examples A and B from the defense guide section 7.4.
- Weighted round-robin proportions over many picks.
- Tie alternation.
- Unfinished accounting under success, 503, error, and timeout.
- Worker output matches settings and is never cached.
- One short end-to-end run through all four rules.

## Weeks 4 to 5: main runs

1. Freeze code and configuration. Record the commit id in every run's log.
2. Five rounds. Each round runs all 36 conditions once, in an order shuffled with a saved seed.
3. Reset between runs. Drop the warm-up window.
4. Keep a run ledger in `results/`: started, finished, failed, thrown out, with reasons. Keep raw files of thrown-out runs.

## Week 6: analysis

Scripts in `implementation/experiments/analysis/` read only raw CSVs.

1. Per run: mean and p95 (percentile method named in the paper), p95 per size class for scenarios 2 and 3, successful throughput, failures by type, achieved rate, dispatcher CPU time, mean select time, probe count, throttling counters.
2. Per condition: median of five runs with min and max.
3. Rule comparison: "clear" only when the five-run ranges do not overlap.
4. H1 to H3: held, not held, or unclear, with the numbers.
5. Overhead table for the feedback rule next to the other three.
6. Plots: p95 against rate per scenario, one line per rule, min to max band; p95 per size class as grouped bars; per-run dots so outliers show.

## Weeks 7 to 8: paper and demo

| Course section | Content |
|---|---|
| Abstract | Question, setup, what was measured, main finding with its conditions |
| Introduction | Slide 2 motivation, revised research question |
| Objectives | Slide 4 objectives |
| Background and literature review | SED theory, real systems, empirical comparisons, methodology, from the gap analysis |
| Main discussion | Setup, full matrix, results, H1 to H3, overhead, per-size p95 |
| Challenges and limitations | One host, two workers, one workload, quota is not a slower machine, five runs |
| Future trends or recommendations | Which rule fits setups like ours; dynamic slowdown; size-aware rules; more workers |
| Conclusion | What held and what did not |
| References | At least 8, each tied to a claim, from the revised proposal table |

The demo shows the live testbed or screenshots, plus the week 6 plots.

## Dropped from the earlier plan

These were in the first version of this plan and are out of scope now. They can go into the paper's future work section.

- A dynamic scenario that switches the quota on and off during a run.
- More than five rounds, paired designs, Mann-Whitney or other significance tests, bootstrap intervals.
- Statistical checks of the send schedule beyond the achieved-rate check.
- Logging and analyzing the age of each worker's estimate.
- The VirtualBox execution cap as an alternative way to slow a worker.

## Risks

| Risk | Sign | Response |
|---|---|---|
| Load generator or dispatcher saturates | Achieved rate below plan, high CPU | Lower the top rate or move the generator; disclose |
| Host noise | Host CPU log shows other load, wide spread | Rerun that round; shuffled order limits bias |
| All rules look the same | Ranges overlap everywhere | Report it; compare with H1 to H3 |
| Feedback loses | Higher p95 than least unfinished | Report it with probe and select cost |
| Quota pauses dominate scenario 3 | High throttling counts, all rules poor | Report the counters and the period |
| Schedule slips | Main runs unfinished by end of week 5 | Shorten run length set in the pilot; never cut rounds below five without saying so |
