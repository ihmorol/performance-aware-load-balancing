# Open questions

Parameters the proposal left open. Decide each before the main experiments and move it to `decisions.md` with the chosen value. Do not invent values during the defense; the honest answer is "not final yet, we fix it before the runs and keep it consistent". The full table is in the defense study guide, section 14.

The grilling session on 2026-11-19 settled the method for most items (see `decisions.md` and `implementation/spec.md`). What is still open is the value, and the pilot decides it by the rule in the spec's "Pilot and calibration" table. An item is ticked only when its value is recorded too.

- [ ] Request rates. Method: three fractions of the calibrated capacity (light, queues forming, near overload). Open: the fractions and the rates per scenario
- [ ] Run duration. Method: requests planned in the first W seconds are dropped; a run ends when every request has a terminal outcome. Open: run length, W, warm-up count K
- [ ] Image set. Method: seeded synthetic JPEGs, resize to half width and height with LANCZOS, JPEG quality 80. Open: final resolutions and images per class
- [x] Weighted round-robin method: profiled throughput per scenario, smooth weighted round-robin (see decisions.md). Still open: the measured ratio per scenario, from the pilot
- [ ] Feedback rule. Method: EWMA of worker-reported processing time from successful, warm-up, and probe replies. Open: the weight a
- [ ] Slow worker: method fixed (systemd CPUQuota, fixed during a run). Still open: quota value and period
- [ ] Worker queue. Method: bounded queue, 503 at once when full, unfinished counted from assignment to any terminal outcome. Open: capacity C
- [ ] Probes. Method: feedback rule only, one fixed small image after T seconds with no completion and nothing unfinished, counted as overhead. Open: T
- [ ] Timeouts. Method: the dispatcher sends a time budget and the worker skips queued requests past it; dispatcher timeout D = (C + 1) × large class p95 on the quota-limited worker; generator timeout = D plus a margin. Open: D and the margin
- [x] Latency reporting: successful requests only, p95 by nearest rank, measured on the generator's clock (see decisions.md)
- [x] Throughput: successful replies in the measured window divided by its length, next to the offered rate (see decisions.md)
- [ ] Resource monitoring. Method: psutil sampler every 1 second on each VM and the host, dispatcher process CPU time, cpu.stat before and after every run. Open: the bottleneck threshold
- [x] Reset: restart the worker and dispatcher services before every run (see decisions.md and the spec's "VM setup")
- [x] Analysis: median with min and max over five runs; "clear" means non-overlapping ranges (see decisions.md)
- [ ] Image size classes. Method: three classes with clearly separated median processing times. Open: class boundaries and the mixed proportion (needed for p95 per size class)
- [ ] Achieved-rate tolerance for flagging a run. Method: from the send-accuracy check at the top rate. Open: the value

## Cloud VMs (added 2026-11-23, issue #19)

These are not pilot parameters, but the runs can't start until they are answered. Details are in `implementation/cloud-deployment.md`.

- [ ] Payment card. Google Cloud's trial needs one. Open: whether a member's card is accepted. If none is, the provider becomes Azure for Students
- [ ] Quota. Open: the trial's CPU and in-use address quota in the chosen region (Google does not publish it), or the real vCPU limit on Azure for Students
- [ ] Machine type and zone. Plan: t2d-standard-1 in a us-central1 zone. Open: whether it is offered there for this account
- [ ] Sign-up date. Open: the date the 90-day trial clock starts, recorded in `decisions.md`
- [ ] Cost. Open: the real total, which depends on the run length the pilot sets
- [ ] Thrown-out runs. The ledger can mark a run thrown out, but nothing says who decides it or on what grounds. Open: the owner states the rule before the main runs, so no run is thrown out after its result is seen
