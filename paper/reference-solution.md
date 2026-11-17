# Reference solution

How we plan to solve the problem defined in [problem-definition.md](problem-definition.md). This is the build plan the three core papers point to. It contains no measured results and no invented parameter values; every number marked as a pilot decision gets fixed in `notes/decisions.md` before the main runs. Citations refer to [references.md](references.md).

## Approach in one paragraph

Build one dispatcher with four interchangeable routing rules behind a single forwarding path, two identical image-processing workers, and a host-side load generator, all on the three planned Ubuntu VMs. Collect per-request logs and resource samples under every rule, so the same evidence supports all comparisons. Run the 4 x 3 x 3 matrix with at least five repetitions per condition, then analyze with pandas and matplotlib. The contribution is the fairness of the comparison: one codebase, one measurement pipeline, four rules, honest variation reporting.

## Design principles the core papers imply

From Prequal (core paper 1):

- Route on estimated finish time, not on a scalar load score. This is the feedback rule's design basis.
- Keep estimates fresh with bounded, counted overhead: recent observations feed the average, and idle workers get probed so their estimates do not go stale. Probe traffic is logged and reported, never hidden.
- Report percentiles, not only means, and treat dispatcher overhead as part of the result.

From Join-Idle-Queue (core paper 2):

- Separate who decides (dispatcher) from who works (workers), and be explicit about which side holds which information. In our design the dispatcher holds counts and timing averages; workers report their own processing time in each response.
- Assume held information is stale and measure under conditions where staleness matters (heterogeneous jobs, unequal service rates).
- Keep the system simple enough to reason about: one processing slot per worker, bounded queues, explicit assignment and completion boundaries for every counter.

From The Tail at Scale (core paper 3):

- Evaluate with mean and p95 together, and report run-to-run variation, because tail behavior is what distinguishes rules.
- Create heterogeneity deliberately (mixed image sizes, a CPU-quota-slowed worker) to see how each rule behaves under the tail-inducing conditions the paper describes.

## Components

### Dispatcher (FastAPI + Uvicorn, asyncio)

- One POST endpoint receives an image upload, selects a worker with the active rule, forwards via HTTPX, and returns the result.
- Per-worker state, shared by all rules: `unfinished[worker]` (assigned minus completed), `avg_time[worker]` (recent average processing time), `last_seen[worker]` (when the estimate was last refreshed), plus a rotation index and calibrated weights for the two simpler rules.
- Counters update at exactly two points: on assignment to a worker, and on completion, failure, or timeout of that request. The defense guide's accounting rules apply here, including what happens when a client times out while worker-side work continues.
- All four rules share the same forwarding, logging, and error path. Only the selection function differs, which is the isolation the defense guide requires.
- A health check tracks availability separate from performance probes; an unavailable worker receives no new work.

### Worker (FastAPI + Pillow)

- One POST endpoint performs the chosen resize and recompression with Pillow, measures the operation with `time.perf_counter`, and returns the processed image plus the measured processing time.
- One processing slot at a time, with a bounded internal queue whose capacity and rejection behavior are pilot decisions.
- No output caching: every request performs the work, per the fairness controls.
- CPU quota applied via the service's cgroup setting for the slowed-worker scenario, with the exact quota value recorded before runs.

### Load generator (host)

- Sends images from a fixed, controlled set on a planned schedule, at one of the three pilot-chosen rates.
- Records, per request: planned send time, actual send time, response time, outcome (success, failure, timeout), and the image's identity.
- Reports planned versus achieved rate for every run, so a slow client never masquerades as a fast rule.
- No hidden retries. A failed request is logged as failed.

### Experiment runner

- Walks the condition matrix (rule x scenario x rate x repetition), randomizes run order, and applies the reset procedure between runs: drain outstanding work, clear counters and estimates, restore scenario settings, start a fresh log. Reset never reboots the VMs unless a pilot shows it is necessary.
- Logs the run order and configuration with each run's data.

### Analysis (pandas, matplotlib)

- Computes per-run metrics, then summarizes across repetitions with variation, not a single best run.
- Percentile method fixed once and applied everywhere.
- Produces comparison plots per scenario and rate, plus overhead plots from the resource samples.

## The four rules, concretely

```text
round_robin():        next worker in rotation
weighted_rr():        next worker per calibrated weight sequence
least_unfinished():   argmin over workers of unfinished[w]
feedback():           argmin over workers of (unfinished[w] + 1) * avg_time[w]
```

All rules first restrict the candidate set to available workers (health check passed, queue not full). Ties alternate, so neither worker is favored systematically, as the proposal already plans.

The feedback rule's `avg_time[worker]` is the one parameter the proposal leaves open. The plan: use an exponentially weighted moving average with the smoothing factor fixed before the main runs and recorded in `notes/decisions.md`. Prequal's account of refreshing estimates from recent completions is the design reference; the exact factor is ours to fix in the pilot, not to tune after seeing results.

### Initialization and probes (feedback rule)

- Startup: pilot calls initialize each worker's average so the first decisions are not blind. The procedure is fixed and documented.
- Idle workers: if a worker has been idle longer than a pilot-chosen interval, the dispatcher sends a small probe request and updates the average with its result. Probes are counted, their cost appears in the overhead measurements, and they are distinct from health checks.

## Experiment protocol

1. **Pilot.** Verify the pipeline end to end, choose the three request rates and the run duration, confirm the dispatcher and client are not the bottleneck (their CPU stays well below the workers' at the chosen rates), set the CPU quota for the slowed worker, and fix every open parameter from `notes/open-questions.md`.
2. **Main matrix.** 4 rules x 3 scenarios x 3 rates x at least 5 repetitions, order randomized, reset between runs, caching disabled, no hidden retries.
3. **Overhead accounting.** Every run logs dispatcher CPU and RAM, probe counts, and planned versus achieved rate alongside latency and throughput.
4. **Validation runs.** Correctness checks from the proposal (routing behavior, timeout accounting, output properties) run separately from the measurement matrix.

## Analysis plan

- For each condition: mean response time, p95, throughput, failure and timeout counts, and their variation across repetitions.
- Variation is reported with the results. A difference smaller than run-to-run variation is not called an improvement.
- Latency, throughput, failures, and overhead stay together in every conclusion, per the defense guide's guidance.
- Each hypothesis from [problem-definition.md](problem-definition.md) is checked against the matrix, and refuted hypotheses are reported as refuted.
- The decision criterion for a meaningful benefit is fixed before the main runs, so the standard cannot move after seeing results.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| Shared-host interference distorts comparisons | Monitor host resource pressure, keep scenario settings fixed, report variation; state the limitation openly |
| Dispatcher or client becomes the bottleneck | Pilot checks resource use; if the wrong component saturates, fix or disclose before interpreting routing differences |
| EWMA factor badly chosen | Fix via pilot reasoning and report sensitivity as an extra validation run, not as post-hoc tuning |
| Feedback oscillates between workers | Alternating ties plus the estimate formula dampen thrashing; watch assignment logs during validation |
| Probe traffic skews overhead | Count probes per run and include their latency and CPU in the overhead report |
| Client cannot sustain planned rate | Log planned versus achieved rate per run; exclude or rerun affected conditions honestly |
| Timeout accounting drifts counters | Explicit state machine per request with validation tests for timeout and failure paths |

## Build order

1. Worker service with Pillow processing, timing, and quota support.
2. Dispatcher with state tracking and the round-robin rule, validated end to end.
3. Remaining three rules behind the shared selection interface.
4. Load generator with schedule control and planned-versus-achieved rate logging.
5. Experiment runner with reset and order randomization.
6. Analysis scripts and plots.
7. Pilot, parameter fixing, then the main matrix.

## How the core papers guide each phase

| Phase | Guidance from |
|---|---|
| Choosing the feedback formula and probe policy | Prequal |
| Architecting dispatcher-worker state and its staleness handling | Join-Idle-Queue |
| Choosing metrics (mean, p95) and heterogeneity scenarios | The Tail at Scale |
| Predicting where differences appear across rates | Wang, Feng, and Cheng; Mitzenmacher |
| Motivating the comparison (limits of least outstanding request) | Detti and Funari |
| Justifying the VM testbed and its limits | Felter et al. |
| Writing the literature review | Kumar and Kumar; Shafiq et al. |
