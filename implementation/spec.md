# Implementation spec: everything before the main runs

Written 2026-11-19 from a grilling session with the owner. It covers the work from an empty `implementation/` folder up to the point where the main runs can start: code and configuration frozen, the pilot done, and one short dry-run round passed. It follows `paper/revised-proposal.md` and `implementation/implementation-plan.md` and changes them only where the session settled something new. Those changes are listed in `notes/decisions.md`.

Nothing here is built yet, and no number in this file is a measurement. Values the pilot decides are marked "pilot" with the rule the pilot uses. A few starting candidates are given so the pilot has somewhere to begin; they are guesses to be replaced, not results.

## Problem statement

The team has a fixed research design (four rules, three scenarios, three rates, five shuffled rounds, 180 main runs) and no code. The implementation plan puts the pilot in week 1 and the build in weeks 2 to 3, but the pilot can't measure capacity, spread, or quota effects without a working worker, dispatcher, and load generator. Many details the proposal left open (request format, timeouts, how an estimate is averaged, how a run is reset, how logs are joined) have to be fixed before any run, or the comparison stops being fair and repeatable.

The machine used for writing code (4 cores, 7.9 GB RAM, Windows, no VirtualBox) is not the experiment host. The main runs happen on a teammate's PC with VirtualBox, the 12 logical CPU, 13.9 GB machine described in the frozen documents. Its host operating system is not confirmed yet.

## Solution

Build the whole system first as plain Python processes that run on localhost, test it there, then deploy it to the three VMs on the teammate's PC. Use the deployed system to run the pilot and the weighted round-robin calibration, write every chosen value into one config file, freeze code and config, and run one short dry-run round of all 36 conditions. When the dry run passes, the main runs can start.

The real order of work is: build and test locally, deploy to VMs, pilot, calibrate, freeze, dry run. The slide 4 week labels stay unchanged in the paper.

## User stories

1. As a team member, I want to run the worker, dispatcher, and load generator as localhost processes on any laptop, so that I can develop and test without VMs.
2. As a team member, I want one command that installs pinned package versions, so that the host and every VM run the same code with the same libraries.
3. As a team member, I want one config file that holds every tunable value, so that nobody changes a setting in one place and forgets another.
4. As a team member, I want the system to refuse to start a main run while any config value is still unset, so that a pilot placeholder never reaches the main data.
5. As a team member, I want the system to refuse to start a main run from uncommitted code, so that every main run maps to one commit.
6. As the paper writer, I want every run log to record the git commit id and a hash of the config, so that I can state exactly what code and settings produced each number.
7. As a team member, I want a seeded script that generates the image set, so that anyone can rebuild the same images from the seed.
8. As a team member, I want the images grouped into size classes from their measured processing time, so that p95 per size class means something.
9. As the load generator, I want to upload an image's bytes with each request, so that the workload looks like a real resize service.
10. As the load generator, I want the processed image bytes back, so that every request does the full round trip.
11. As a worker, I want to process one image at a time and hold the rest in a bounded queue, so that each worker behaves like one processing slot.
12. As a worker, I want to reject a request at once with HTTP 503 when my queue is full, so that overload shows up as rejections instead of unbounded waiting.
13. As a worker, I want to skip a queued request whose time budget has already passed, so that I don't spend CPU on a reply nobody is waiting for.
14. As a worker, I want to time only the image work and return that time with the reply, so that the feedback rule learns processing time, not queue wait or network time.
15. As a worker, I want image work to run off the event loop, so that I keep accepting and queueing requests while an image is being processed.
16. As a worker, I want a health endpoint that does no image work, so that checks never disturb measurements.
17. As a worker, I want to never cache output, so that two identical requests cost the same work.
18. As the dispatcher, I want one forwarding path shared by all four rules, so that only the selection step differs between rules.
19. As the dispatcher, I want to count each worker's unfinished requests from assignment until any terminal outcome, so that least unfinished requests and the feedback rule see the same count.
20. As the dispatcher, I want to keep each worker's recent processing time as an EWMA of worker-reported times, so that the feedback rule has a cheap and stable estimate.
21. As the dispatcher, I want to send the same warm-up requests to each worker before every run, for every rule, so that all rules start from the same state.
22. As the dispatcher, I want to probe a worker that has had no completion for T seconds and has nothing unfinished, under the feedback rule only, so that a worker the rule stopped using can be measured again.
23. As the dispatcher, I want to log one row per request with the state I saw when deciding, so that every routing choice can be explained afterwards.
24. As the dispatcher, I want to time `select()` itself, so that the paper can report the cost of choosing a worker for each rule.
25. As the dispatcher, I want to pass a worker's 503 back as "rejected" and never retry, so that the four rules are compared without hidden retries.
26. As the dispatcher, I want a fixed timeout per request and to return a timeout status when it passes, so that a stuck request ends with a known outcome.
27. As the load generator, I want a seeded Poisson schedule of send times and image choices, so that every rule in a round gets exactly the same requests at the same planned times.
28. As the load generator, I want to send each request at its planned time whether or not earlier replies have arrived, so that slow replies can't slow the arrival rate (open loop).
29. As the load generator, I want to measure response time from the planned send time, so that delays in my own sending count against the system, not in its favour.
30. As the load generator, I want to log the actual send time next to the planned one, so that the pilot can check how accurately I keep the schedule.
31. As the load generator, I want an optional spin-wait before each send, so that send times stay accurate on a Windows host where timers are coarse.
32. As the load generator, I want to wait until every request has a terminal outcome before the run ends, so that no request is silently cut off.
33. As the paper writer, I want response time measured only on the generator's clock and joined to the dispatcher log by request id, so that clocks on different machines never need to agree.
34. As a team member, I want a resource sampler on each VM and on the host that records CPU and RAM every second, so that I can see whether any machine was the bottleneck.
35. As the paper writer, I want the dispatcher's process CPU time at the start and end of each run, so that I can report the monitoring overhead of each rule.
36. As the paper writer, I want each worker's cpu.stat throttling counters before and after every run, so that I can show the quota was active in scenario 3 and absent elsewhere.
37. As a team member, I want one orchestrator command that runs a whole run end to end from the host, so that 180 runs follow the same steps every time.
38. As a team member, I want the orchestrator to reset by restarting the worker and dispatcher services, so that no queue or state leaks from one run to the next.
39. As a team member, I want the orchestrator to apply and remove the CPU quota on the slowed worker and verify it took effect, so that scenario 3 is set up the same way every time.
40. As a team member, I want a run ledger that records every run as started, finished, failed, or thrown out with a reason, so that the paper can account for every run.
41. As a team member, I want the round runner to resume from the ledger after a crash, so that one failure doesn't force us to redo a whole round.
42. As a team member, I want each round's run order shuffled with a saved seed, so that run order can't bias one rule.
43. As the paper writer, I want a per-run summary with mean and p95 response time, p95 per size class, throughput, failures by type, achieved rate, overhead, and throttling counts, so that the pilot and later the week 6 analysis start from the same numbers.
44. As the paper writer, I want p95 computed by nearest rank over successful requests, so that the method is easy to state and check by hand.
45. As the paper writer, I want requests planned in the first W seconds dropped from the summary, so that start-up effects don't enter the comparison.
46. As the paper writer, I want a run that misses its planned rate by more than the tolerance kept and flagged, not deleted, so that the paper can report it.
47. As a team member, I want pilot tools for image timing, calibration, a rate sweep, a quota check, a bottleneck check, a send-accuracy check, and a spread check, so that each pilot decision comes from a recorded measurement.
48. As a team member, I want the weighted round-robin calibration to keep each worker busy with the scenario's image mix and measure its throughput, so that the weights follow Aslanpour et al. (FGCS 2024, Section 4.2).
49. As a team member, I want a VM setup guide and scripts, so that a teammate can rebuild the testbed from scratch on their own PC.
50. As a team member, I want a script that records VirtualBox, Ubuntu, kernel, systemd, cgroup, Python, and package versions, so that the setup section of the paper is exact.
51. As a team member, I want a short dry-run round of all 36 conditions before the main runs, so that every part of the pipeline is proven once with final settings.
52. As a defense speaker, I want every rule's behaviour covered by tests built from the defense guide examples, so that what we say in the defense matches the code.

## Implementation decisions

### Machines and stack

- Development happens on any machine as localhost processes. The main runs happen on a teammate's PC with VirtualBox: a dispatcher VM (1 GB, 1 vCPU) and two worker VMs (2 GB, 1 vCPU each) on one host-only network with static addresses.
- The load generator and the orchestrator run on the host operating system of that PC, not in a VM.
- Ubuntu Server 24.04 LTS on all VMs with its Python 3.12. The host uses a Python 3.12 virtual environment so host and VMs match. Packages: FastAPI, Uvicorn, HTTPX, Pillow, psutil, pytest, pinned in one requirements file. Config is TOML, read with the standard library.
- Colab and similar notebook services are not used. They can't run three VMs, systemd, or a CPU quota.

### Code layout

- One shared Python package used by every part. It holds config loading and validation, the CSV row formats, the seeded image set generator, the nearest-rank percentile, and the per-run summary.
- Code lives in the folders AGENTS.md already names: `implementation/worker/`, `implementation/dispatcher/`, `implementation/experiments/` (load generator, orchestrator, pilot tools, summary), `implementation/setup/` (VM guide, systemd units, scripts).

### Config

- One TOML file holds every tunable value: addresses, worker queue capacity, dispatcher timeout, generator timeout, EWMA weight, probe threshold T, warm-up count, dropped window W, run length, rates per scenario, weights per scenario, image classes and mixed proportion, quota and period, sampler interval, achieved-rate tolerance, bottleneck threshold, the spin-wait switch, and all seeds.
- The config has a stage field: `pilot` or `main`. In `main`, every value must be set and the git working tree must be clean, or the orchestrator refuses to start.
- Every run records the commit id and a SHA-256 hash of the config file in its metadata.

### Image set and operation

- A seeded script draws synthetic JPEGs (gradients, shapes, noise) at several resolutions. No downloaded photos.
- Operation on every request: decode, resize to half width and half height with Pillow's LANCZOS filter, encode as JPEG quality 80. Same settings for every request.
- Size classes small, medium, and large are set in the pilot from measured processing time. Starting candidates for resolutions: 640×480, 1920×1080, 3840×2160 (pilot replaces these).
- Scenario 1 uses only the medium class. Scenarios 2 and 3 use all three classes in a proportion the pilot fixes.
- The generator holds the image bytes in memory. Workers don't need the image set.

### Request format

- Generator to dispatcher: POST with the JPEG bytes as the body and headers for request id, image id, and size class.
- Dispatcher to worker: the same body and headers, plus a time budget in milliseconds (equal to the dispatcher timeout) and a probe flag. The budget is relative because the machines' clocks differ.
- Worker reply: HTTP 200 with the processed JPEG bytes and headers for processing time and output size. HTTP 503 when the queue is full.
- Dispatcher to generator: the worker's status and body, plus headers naming the chosen worker and the worker's processing time. On a dispatcher timeout it returns 504, on a connection or other error 502.
- The dispatcher reads the whole request body before forwarding (no streaming) and uses one shared HTTPX client with keep-alive connections to both workers.

### Worker

- FastAPI under Uvicorn, one process.
- One consumer task reads a bounded asyncio queue. When the queue is full, the request gets 503 at once. Queue capacity C is a pilot value.
- The worker records the monotonic time a request arrives. Before starting a queued request, it checks whether the budget has passed since arrival. If it has, it skips the request, answers with an "expired" status, and logs it.
- Pillow work runs in a thread. Only decode, resize, and encode are timed, with `time.perf_counter`.
- No output caching.
- A health endpoint that does no image work.
- A per-request worker log (request id, arrival, queue wait, processing time, outcome: done, expired, rejected), held in memory and written to CSV when the orchestrator asks or the service stops.

### Dispatcher

- One forwarding path: receive, select, forward, return. The rule is chosen at start-up from the run parameters.
- Per-worker state: unfinished count, EWMA estimate, last completion time, probe in flight. One shared tie counter.
- Unfinished count goes up by one when a request (or probe) is assigned and down by one on any terminal outcome: success, 503, expired, other error, or timeout.
- `select()` is a pure function: it takes a snapshot of the state and returns the chosen worker and the updated rule state. It is timed with `time.perf_counter_ns`.
- Round-robin: strict alternation.
- Weighted round-robin: smooth weighted round-robin with the calibrated integer weights for the scenario. Each pick adds each worker's weight to its current value, picks the larger current value, and subtracts the total weight from the chosen one.
- Least unfinished requests: the worker with fewer unfinished requests.
- Feedback rule: the worker with the smaller (unfinished + 1) × estimate.
- Ties in any rule alternate between workers using the tie counter.
- EWMA: estimate = (1 − a) × estimate + a × newest processing time. Samples are worker-reported processing times from successful replies, warm-up replies, and probe replies. The weight a is a pilot value. The estimate is updated under every rule (it is cheap), but only the feedback rule reads it.
- Warm-up: at start-up, before reporting healthy, the dispatcher sends the same K requests (one fixed medium image) to each worker. Their times seed the estimates. K is a pilot value. Warm-up requests are logged with a flag and never enter the summary.
- Probe, feedback rule only: a background check looks at each worker. If a worker has had no completion for T seconds, has no unfinished requests, and has no probe in flight, the dispatcher sends one fixed small image. The probe counts as unfinished, its time enters the estimate, and it is logged with a probe flag. T is a pilot value.
- No retries.
- Dispatcher timeout D is fixed per run from config.
- Dispatcher log, one row per request or probe: run id, rule, scenario, rate, request id, image id, size class, probe flag, warm-up flag, chosen worker, both unfinished counts and both estimates at decision time, select time in nanoseconds, worker processing time, worker status, outcome, time inside the dispatcher. Held in memory and written to CSV on the orchestrator's request and on shutdown.
- An admin endpoint returns the dispatcher's process CPU time, so the orchestrator can read it at the start and end of each run.

### Load generator

- Runs on the host. Before a run it builds the schedule from a seed: Poisson arrivals (exponential gaps) at the run's rate over the run length, and an image choice per request from the scenario's mix.
- The seed depends on scenario, rate, and round. Every rule in the same round, scenario, and rate gets the same schedule. Different rounds get different schedules.
- The schedule is saved as a CSV before sending.
- Sending is open loop: one asyncio task per request fires at its planned time. The HTTPX client allows enough connections that sending never waits for a free one.
- With the spin-wait switch on, the generator sleeps until shortly before the planned time and then busy-waits to it.
- Response time = time the reply arrived − planned send time. Actual send time is logged as a check.
- Generator timeout = D plus a margin, so the generator normally sees the dispatcher's 504 instead of timing out itself.
- The run ends when every request has a terminal outcome: success, rejected, expired, timeout, or error.
- Generator log, one row per request: run id, request id, image id, size class, planned offset, actual offset, send lag, status, outcome, response time, chosen worker and processing time (from reply headers), output size.

### Monitoring

- A psutil sampler on each VM and on the host writes one CSV row per second: timestamp, total CPU, CPU of the service process, RAM used.
- Dispatcher process CPU time read through the admin endpoint at start and end of each run.
- cpu.stat counters (nr_periods, nr_throttled, throttled_usec) read from each worker service's cgroup before and after every run, in every scenario. In scenarios 1 and 2 they should not change.

### Orchestrator

- Runs on the host and talks to the VMs with plain `ssh` and `scp` using keys. No extra service on the VMs. Sudo on the VMs is limited to the exact systemctl commands it needs.
- It has two backends with the same steps: a local backend that starts processes on localhost (no quota), used for tests and development, and an SSH backend for the VMs.
- Steps for one run:
  1. Write a "started" row to the ledger.
  2. Apply the quota to worker 2 for scenario 3 with `systemctl set-property --runtime` (CPUQuota and CPUQuotaPeriodSec), or clear it for scenarios 1 and 2. Read the cgroup's cpu.max to confirm.
  3. Restart both worker services, then the dispatcher service with the run's rule, scenario, weights, and run id. Wait until every health check passes. The dispatcher only reports healthy after its warm-up.
  4. Read cpu.stat on both workers and the dispatcher CPU time. Start the samplers.
  5. Run the load generator with the saved schedule and wait for it to finish.
  6. Read cpu.stat and dispatcher CPU time again. Stop the samplers. Ask the dispatcher and workers to write their logs. Copy every file to the host.
  7. Write the run metadata (commit, config hash, seeds, counters, CPU times, timings) and the per-run summary.
  8. Mark the run finished, or failed with a reason, in the ledger.
- A round runner shuffles the 36 conditions of each round with a saved seed and runs them in that order. On restart it reads the ledger and skips finished runs. A failed run is rerun at the end of its round and both attempts stay in the ledger.

### Results layout

- Main runs: one folder per run inside the scenario folders that `results/README.md` already lists. Pilot, calibration, and dry-run data go in their own folders next to them, never mixed with main runs.
- Each run folder holds the schedule, generator log, dispatcher log, both worker logs, sampler CSVs, metadata, and summary. Raw files are never edited.
- The ledger is one CSV in `results/`.

### Per-run summary

- Uses only requests planned after the first W seconds (the measured window).
- Mean and p95 response time over successful requests. p95 by nearest rank: sort, take the value at position ceil(0.95 × n).
- p95 per size class for scenarios 2 and 3.
- Successful throughput: successful replies in the measured window divided by its length, shown next to the offered rate.
- Failures by type: rejected, expired, timed out, error.
- Achieved sending rate and largest send lag. A flag when the achieved rate misses the plan by more than the tolerance.
- Dispatcher CPU seconds, mean select time, probe count, throttling counter changes.

### Pilot and calibration

Each pilot step is a command in the experiments tooling and writes its data to the pilot folder. Every value it decides goes into `notes/decisions.md` with the method, and into the config.

| Value | How the pilot decides it |
|---|---|
| Image resolutions and size class boundaries | Time each image alone on a worker several times; group into three classes with clearly separated median processing times |
| Mixed proportion (scenarios 2 and 3) | Team choice after seeing the class timings, recorded with the reason |
| Quota and period | Choose, apply, run, and confirm nr_throttled rises; record both values |
| Weighted round-robin weights | Per scenario, send that scenario's mix straight to each worker with two requests always in flight (quota on worker 2 in scenario 3); throughput = completions per second; weight = worker ÷ sum, rounded to a small integer ratio |
| Capacity per scenario | Sum of the two workers' calibrated throughputs, then checked with a short rate sweep through the dispatcher |
| Three rates per scenario | Fractions of capacity: light, queues forming, near overload; fractions recorded |
| Queue capacity C | Large enough that queues form at the middle rate without rejections; recorded with the reason |
| Dispatcher timeout D | (C + 1) × the large class p95 processing time on the quota-limited worker, rounded up |
| Generator timeout | D plus a fixed margin |
| EWMA weight a | Chosen from a small set (starting candidates 0.1, 0.2, 0.3) by how much the estimate jumps in a scenario 2 pilot run; never changed after the freeze |
| Probe threshold T | A multiple of the large class processing time on the quota-limited worker |
| Warm-up count K and dropped window W | Long enough that the estimates and queue lengths settle in pilot runs |
| Run length | Long enough for a stable p95 per size class, short enough that 180 runs plus resets fit in weeks 4 to 5 with spare time |
| Achieved-rate tolerance | From the send-accuracy check at the top rate |
| Bottleneck threshold | Generator host and dispatcher CPU at the top rate must stay below a stated level; fix or disclose otherwise |
| Spin-wait switch | On if the host's send lag is large without it |

The spread check repeats one condition five times and looks at per-run p95. If the spread is very wide, the paper says so; the number of rounds stays five.

### VM setup

- A written guide plus scripts in `implementation/setup/`: VirtualBox host-only network, static addresses, Ubuntu install, SSH keys, the limited sudo rule, the Python environment, and systemd units for worker and dispatcher.
- Unattended upgrades and other scheduled jobs that could wake up during a run are disabled on the VMs.
- A version script writes VirtualBox, Ubuntu, kernel, systemd, cgroup version, Python, and package versions to a file in `implementation/setup/`.
- The reset is the orchestrator's restart step. The guide lists exactly what it resets: worker queues, dispatcher state and estimates, rule counters, and the quota.

### Build order

Each slice ends with something runnable and tested. Slices 1 to 8 need only a laptop. Slices 9 to 11 need the teammate's PC.

1. Skeleton: shared package, pinned requirements, config loader with stage checks, pytest running.
2. Image set generator and worker: process endpoint, queue, 503, budget and expiry, health, worker log.
3. Dispatcher with round-robin end to end: forwarding path, unfinished accounting, timeout, warm-up, dispatcher log, admin CPU time endpoint.
4. The other three rules: smooth weighted round-robin, least unfinished requests, feedback rule with EWMA and probes.
5. Load generator: schedule, open-loop sender, spin-wait switch, generator log.
6. Per-run summary.
7. Monitoring: sampler, cpu.stat reader.
8. Orchestrator with the local backend, ledger, round runner, resume, and main-stage guards. A full local round of all four rules passes.
9. VM setup guide and scripts, SSH backend, deploy, smoke test on the VMs.
10. Pilot and calibration tools, then the pilot itself. Values recorded.
11. Freeze: config stage set to main, commit recorded, dry-run round, fixes, ready for main runs.

## Testing decisions

- Tests check behaviour seen from outside a module, not its internals. They are written first, using the `tdd` skill.
- First seam: each rule's `select()` as a pure function of a state snapshot.
  - Defense guide section 7.4 Example A: feedback picks A, least unfinished requests picks B.
  - Example B: feedback picks B.
  - Example C: with equal estimates, feedback picks what least unfinished requests picks.
  - Round-robin alternates strictly.
  - Smooth weighted round-robin gives exactly the weight ratio over each full cycle and spreads picks inside the cycle.
  - Ties alternate in every rule.
  - The EWMA update gives the hand-computed value.
- Second seam: the real dispatcher in process, in front of fake workers whose delay and outcome each test controls.
  - Unfinished count returns to zero after success, 503, expired, error, and timeout.
  - Every request produces one dispatcher log row with the state at decision time.
  - No request is retried.
  - The budget header reaches the worker.
  - Warm-up runs the same way for every rule and seeds the estimates.
  - A probe goes out only under the feedback rule, only after T seconds with no completion and nothing unfinished, and its time enters the estimate.
- Worker tests against the real worker with real Pillow work.
  - Output decodes as a JPEG at half the input width and height.
  - Two identical requests are both processed (no caching).
  - A full queue gets 503 at once.
  - A queued request past its budget is skipped and logged as expired.
  - The health endpoint does no image work.
- Load generator tests.
  - The same seed gives the same schedule.
  - Every rule in a round, scenario, and rate gets the same schedule.
  - The mean gap is close to 1/rate over a long seeded schedule.
  - Response time is counted from the planned send time.
- Summary tests on hand-made logs: nearest-rank p95, the dropped window, p95 per class, throughput, failure counts, the achieved-rate flag.
- Config tests: the main stage refuses unset values and a dirty working tree.
- End to end: the orchestrator's local backend runs one short run per rule on localhost, and the summary computes.
- The CPU quota can't be tested on localhost. It is checked in slice 9 on the VMs and again by the pilot's quota check.
- There is no code in the repository yet, so there is no prior art for tests to follow.

## Out of scope

- The 180 main runs themselves (weeks 4 to 5).
- Week 6 analysis beyond the per-run summary: per-condition medians, plots, the H1 to H3 verdicts, the overhead table.
- The term paper and demo.
- Everything listed under "Dropped from the earlier plan" in `implementation/implementation-plan.md`: a dynamic slowdown scenario, more than five rounds, significance tests, schedule statistics beyond the achieved-rate check, analysis of estimate age, the VirtualBox execution cap.
- Running the system on Colab, public clouds, or containers instead of VMs.
- Running the pilot, the freeze, and the dry run themselves. The issues build the tools; a person at the experiment PC runs them, following the manual checklist in `implementation/ORCHESTRATION.md`.

## Further notes

- The host OS of the teammate's PC is not confirmed. On Windows, Python's asyncio timers wake in steps of about 15 ms, which is why the spin-wait switch exists. The pilot's send-accuracy check decides whether it is turned on.
- Uploading image bytes means the 1 vCPU dispatcher handles every image twice (in and out). The pilot's bottleneck check has to show the dispatcher keeps up at the top rate. If it doesn't, the top rate comes down or the paper discloses it.
- Weighted round-robin gets advance knowledge of the slowed worker through calibration, and the feedback rule has to learn it at run time. The paper states this.
- Four choices were made while writing this spec, not in the grilling session. The owner confirmed all four on 2026-11-19:
  - A probe also requires the worker to have no unfinished requests, since probing a worker that still holds work tells the dispatcher nothing new.
  - Schedules differ between rounds (same within a round), so the five-run spread includes different arrival sequences.
  - Capacity comes from the sum of the calibrated throughputs, with a rate sweep only as a check.
  - cpu.stat is read in every scenario, not only scenario 3.
