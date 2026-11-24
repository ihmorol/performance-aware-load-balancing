# Team guide, short version

A 10 minute read. The full version, with examples and more detail, is [team-guide.md](team-guide.md). No experiment has run yet; numbers here are plan settings or marked examples.

> [!IMPORTANT]
> Update 2026-11-23: the teammate's PC will not be used, because it doesn't have enough free RAM for the VMs. The pilot, the dry run, and the main runs move to four cloud VMs (`plb-gen`, `plb-disp`, `plb-w1`, `plb-w2`, 1 vCPU each). Google Cloud is the first choice but needs a card; Azure for Students is the fallback. See [implementation/cloud-deployment.md](../implementation/cloud-deployment.md) and issue #19. Section 3 below still shows the old VirtualBox picture.
>
> বাংলায়: teammate-এর PC আর ব্যবহার হবে না। চারটা cloud VM-এ সব run হবে। Google Cloud-এ card লাগে, card না চললে Azure for Students। বিস্তারিত `implementation/cloud-deployment.md` আর issue #19-এ।

## 1. The project

We have a small image resizing service. A dispatcher receives every request (one JPEG each) and sends it to one of two workers. Each worker resizes one image at a time; the rest wait in a queue. We compare four ways the dispatcher can pick a worker, and ask: when images differ in size and workers differ in speed, does watching each worker's recent speed lower response time enough to pay for the extra monitoring?

We don't invent a new rule. Our contribution is a fair comparison: every rule in every scenario, same requests, five repeats, and the monitoring cost charged to the rule that needs it.

বাংলায়: Dispatcher ঠিক করে কোন ছবি কোন worker-এ যাবে। আমরা চারটা উপায় তুলনা করব। নতুন algorithm না, একটা fair তুলনাই আমাদের কাজ।

## 2. The four rules

| Rule | How it picks |
|---|---|
| Round-robin | Takes turns: A, B, A, B |
| Weighted round-robin | Takes turns with fixed shares, such as 3 of every 4 to A. Shares come from measuring each worker's speed before the runs |
| Least unfinished requests | The worker with fewer requests that are sent but not yet answered (processing plus waiting) |
| Feedback rule | The worker with the smaller (unfinished + 1) × recent average processing time |

Example: A has 2 unfinished and averages 100 ms, so 3 × 100 = 300. B has 0 unfinished and averages 500 ms, so 1 × 500 = 500. The feedback rule picks A; least unfinished requests picks B.

The recent average moves part of the way toward each new time (an EWMA). If a worker gets no work for a while, the feedback rule sends it one small test image (a probe) to refresh its average. Probes count as the rule's cost.

The feedback rule may not win. With equal workers it chooses like least unfinished requests, and that rule already sends less to a slow worker because its queue grows. A loss is still a result.

বাংলায়: Round-robin পালা করে দেয়, weighted round-robin আগে মাপা অনুপাতে দেয়, least unfinished কম অসমাপ্ত request-ওয়ালাকে দেয়, feedback rule (unfinished + 1) × average time ছোট যার তাকে দেয়। Feedback সবসময় জিতবে, এমন না।

## 3. Virtual machines in brief

A virtual machine (VM) is a computer made of software, running inside a real PC (the host). VirtualBox creates them. Each VM gets its own memory, a virtual CPU (vCPU), Ubuntu Server, and an address on a private network shared only with the host. We log in with SSH, and Ubuntu runs our programs as services that can be restarted.

We use VMs so each worker has its own CPU, requests travel over a network, and Linux can limit one worker's CPU.

```text
Teammate's PC (12 logical CPUs, 13.9 GB RAM)
├── Load generator and orchestrator
├── Dispatcher VM   1 GB, 1 vCPU
├── Worker 1 VM     2 GB, 1 vCPU
└── Worker 2 VM     2 GB, 1 vCPU (slowed in scenario 3)
```

To slow worker 2, we set a CPU quota: per short period, it may use only part of the CPU, then Linux pauses it until the next period. So it is a worker that stops and starts, not a slower CPU, and the paper says so. Linux counters prove the quota was active.

বাংলায়: VM হলো আসল PC-র ভেতরে software দিয়ে বানানো কম্পিউটার। VirtualBox দিয়ে তিনটা VM বানাব, SSH দিয়ে ঢুকব। Worker 2-কে CPU quota দিয়ে থেমে থেমে চালানো হবে, এটা ধীর CPU-র সমান না।

## 4. The experiment

- Three scenarios: same-size images; mixed sizes; mixed sizes with worker 2 slowed.
- Three request rates per scenario: light, queues forming, near overload.
- 4 rules × 3 scenarios × 3 rates = 36 conditions. Five rounds, each in a shuffled order, so 180 main runs.
- The load generator sends each request at a planned time without waiting for answers (open loop). In one round all four rules get exactly the same requests.
- Before each run the services restart, so nothing carries over.

We measure mean and p95 response time (95% of successful requests were this fast or faster), p95 per image size, successful requests per second, failures by type, CPU and RAM, and the feedback rule's cost (probes, dispatcher CPU, time to pick a worker).

A difference between two rules is "clear" only when their five-run ranges don't overlap.

Settings such as the rates, quota, and queue size are chosen in a pilot on the real VMs, written down in `notes/decisions.md`, then frozen. Nothing changes after that.

Expected, written before any run: H1, with equal workers, feedback and least unfinished requests show no clear difference. H2, with a slowed worker, feedback and weighted round-robin get lower p95 than the other two. H3, at the lightest rate, all four look the same.

বাংলায়: ৩৬টা condition, পাঁচ round, মোট ১৮০টা run। Pilot-এ মান ঠিক করে freeze করব। পাঁচ run-এর range না মিললে তবেই পার্থক্য "clear"।

## 5. Where we are and who does what

| Issue | Part | Status |
|---|---|---|
| #2 | Worker and shared code | Done |
| #3 | Dispatcher with the four rules | Done |
| #4 | Load generator and per-run summary | Done |
| #5 | Orchestrator, monitoring, run ledger | Done |
| #19 | Move the main runs to cloud VMs (docs) | Done |
| #6 | Cloud VM setup guide and scripts | Done, not yet run on cloud VMs |
| #7 | Pilot tools and dry run | Done, not yet run on cloud VMs |

Next for an agent: the week 6 analysis scripts and plots. Next for us: the cloud account, the pilot, and the main runs.

Only we can: check that a card works for Google Cloud (or use Azure for Students), sign up, and create the cloud VMs with the guide from #6, run the pilot and record the values, run the 180 runs in one stretch and stop the VMs between sessions, read the papers we cite, write and own the term paper (10 to 15 pages, at least 8 references), take screenshots for the demo, and explain every part in the defense. Check what the course allows for AI help in writing.

To hand out an issue, tell the agent: "Implement issue #3. Follow AGENTS.md and implementation/ORCHESTRATION.md, build it test-first, open a PR that closes #3, show the test output, and ask before merging."

বাংলায়: Agent কোড লিখবে, কিন্তু VM বানানো, pilot, ১৮০টা run, paper লেখা আর defense আমাদের কাজ।
