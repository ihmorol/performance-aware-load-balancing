# Team guide: what this project is and what we have to do

Written 2026-11-21 for the three of us. It assumes you are new to load balancing and to virtual machines. It explains the ideas from the start, then the plan, then what is already built, what an AI agent can build, and what only we can do.

Read it in order the first time. Each section ends with a short Bangla summary. For slide-by-slide defense practice, the defense study guide in `final/` is still the place to go. Where the two differ, this guide follows the current plan (`paper/revised-proposal.md` and `implementation/spec.md`).

No experiment has run yet. Every number in this guide is either a setting from the plan or a made-up example, and the made-up ones are marked as examples.

## Contents

1. The project in a few sentences
2. Load balancing from zero
3. The four rules we compare
4. Why the feedback rule might help, and why it might not
5. Virtual machines from zero
6. Our testbed
7. How we slow one worker down
8. How one experiment run works
9. What we measure
10. The full experiment plan
11. What we expect to see
12. What is built and what is left
13. Who does what
14. Turning this into the term paper
15. What each of us must understand
16. Words you will see
17. Giving tasks to an agent

## 1. The project in a few sentences

We have a small image resizing service. Requests come in, each one carrying a photo, and the service sends back a smaller copy. Two machines (we call them workers) do the resizing. One more machine (the dispatcher) receives every request and decides which worker gets it.

The question is how the dispatcher should decide. We compare four ways of deciding, called rules. The simple ones don't look at the workers at all. The most informed one watches how long each worker has recently taken per image and uses that.

The research question, as it stands now:

> Which routing rule keeps response time low when request sizes differ and workers have unequal speed, and does knowing each worker's recent processing time pay for the extra monitoring it needs?

We don't invent a new rule. What we add is a fair, careful comparison: every rule is tested in every situation, with the same requests, repeated five times, and we count the cost of the extra monitoring against the rule that needs it.

বাংলায়: আমাদের একটা ছোট image resize service আছে। দুইটা worker ছবি ছোট করে, আর একটা dispatcher ঠিক করে কোন request কোন worker-এ যাবে। আমরা চারটা rule তুলনা করব। নতুন কোনো algorithm বানাচ্ছি না। আমাদের কাজ হলো একটা fair, repeatable তুলনা করা, আর feedback rule-এর monitoring খরচও হিসাবে রাখা।

## 2. Load balancing from zero

### The everyday version

Think of a shop with two counters and one person at the door who tells each customer which counter to go to. That person is the dispatcher. The counters are the workers. Each customer is a request.

If every customer needs the same small job, it hardly matters how the door person decides. Sending people to the counters in turn works fine. Trouble starts when jobs differ. One customer wants a quick photocopy, another wants a hundred pages bound. If the door person just alternates, the quick customer can end up stuck behind the long job while the other counter sits free.

That's the whole problem of load balancing in one picture: spread the work so nobody waits longer than they need to.

### The same thing in our system

- A request is one HTTP message that carries a JPEG image.
- A worker is a small program that resizes the image to half its width and height and sends it back.
- Each worker processes one image at a time. Requests that arrive while it is busy wait in a queue (a waiting line).
- The queue has a fixed size. If it is full, the worker refuses the request at once (HTTP status 503). We call that a rejection.
- The dispatcher sits in front of both workers. It forwards each request to one of them and passes the answer back.

### Why it matters

Response time is the time from when a request should have been sent until the answer comes back. It includes waiting in the queue and the actual processing. Most of the difference between good and bad routing shows up as waiting time. A rule that sends a small image to a worker with a long queue makes that small image wait for nothing.

Big real systems (Google, Meta, cloud providers) spend a lot of effort on this. We study a tiny version of it, two workers and one dispatcher, so we can see and explain every decision.

বাংলায়: দোকানে দুইটা counter আর দরজায় একজন লোক ভাবুন, যে বলে দেয় কে কোন counter-এ যাবে। সে-ই dispatcher, counter হলো worker, customer হলো request। সব কাজ সমান হলে পালা করে পাঠালেই চলে। কিন্তু কাজ ছোট-বড় হলে ছোট কাজ বড় কাজের পেছনে আটকে যেতে পারে। Load balancing মানে কাজ এমনভাবে ভাগ করা যাতে কেউ অকারণে অপেক্ষা না করে।

## 3. The four rules we compare

All four rules share the same code for receiving, forwarding, and replying. Only the one step that picks a worker changes. That way, a difference in results comes from the rule, not from some other code path. No rule retries a failed request.

### Rule 1: round-robin

Take turns: A, B, A, B, and so on. It looks at nothing. It is cheap and fair in count, but it ignores how busy each worker is.

### Rule 2: weighted round-robin

Take turns, but give one worker a bigger share. With weights 3:1, worker A gets 3 out of every 4 requests, spread out (for example A, A, B, A) rather than in a block.

Where do the weights come from? Before the main runs, we measure how many images per second each worker can finish when it is kept busy. The weight follows that throughput (the method from Aslanpour et al., FGCS 2024). We do this separately for each scenario. When both workers are equal, the weights come out close to 1:1, and this rule behaves like round-robin. That is expected, and we report it.

Weighted round-robin knows about a slow worker in advance, because the calibration measured it. The feedback rule has to discover it while running. The paper must say this openly.

### Rule 3: least unfinished requests

Send the request to the worker with fewer unfinished requests. Unfinished means assigned by the dispatcher and not yet answered, so it counts the image being processed plus the ones waiting.

```text
Worker A: 1 processing + 3 waiting = 4 unfinished
Worker B: 1 processing + 0 waiting = 1 unfinished
Choose B
```

This is the well-known least connections idea, but counted in requests instead of network connections. The dispatcher keeps this count itself: plus one when it sends a request, minus one when that request ends in any way (success, rejection, expiry, timeout, or error).

### Rule 4: the feedback rule

For each worker, compute:

```text
estimate = (unfinished + 1) × recent average processing time
```

and pick the smaller estimate. The "+ 1" stands for the new request itself. The recent average comes from the processing times the workers report with every answer.

The defense guide's two examples show why this can beat rule 3:

```text
Example A
Worker A: 2 unfinished, recent average 100 ms -> (2 + 1) × 100 = 300
Worker B: 0 unfinished, recent average 500 ms -> (0 + 1) × 500 = 500
Feedback picks A. Least unfinished requests picks B.

Example B
Worker A: 9 unfinished, recent average 100 ms -> (9 + 1) × 100 = 1000
Worker B: 0 unfinished, recent average 500 ms -> (0 + 1) × 500 = 500
Feedback picks B.
```

In example A, B is empty but very slow, so a short wait at fast A is still better. In example B, A's line is so long that slow but empty B wins.

This rule has a name in queueing theory: shortest expected delay, or SED. Using that name in the paper is honest and helps readers who know the theory.

#### How the recent average works

We use an EWMA (exponentially weighted moving average). Each new processing time moves the average part of the way toward it:

```text
new average = (1 − a) × old average + a × newest time
```

With a = 0.2, an old average of 100 ms, and a new time of 200 ms: 0.8 × 100 + 0.2 × 200 = 120 ms. A small a gives a calm average that reacts slowly. A big a reacts fast but jumps around. The pilot picks a, and it never changes after that.

A worker's very first measured time becomes its average directly. Before each run the dispatcher sends a few warm-up requests to both workers, so every rule starts with the same filled-in averages.

#### Probes

The feedback rule has a blind spot. If it stops sending work to a slow worker, it never gets new times from it, so its average can go stale. To fix that, when a worker has had no completed request for T seconds and has nothing unfinished, the dispatcher sends it one small test image, called a probe. Probes are extra work that only the feedback rule creates, so we count them as its cost.

বাংলায়: চারটা rule-এর পার্থক্য শুধু worker বাছাইয়ের ধাপে। Round-robin পালা করে পাঠায়। Weighted round-robin আগে মাপা ক্ষমতা অনুযায়ী বেশি সক্ষম worker-কে বেশি দেয়। Least unfinished requests যার অসমাপ্ত request কম তাকে দেয়, চলমান আর অপেক্ষমাণ দুটোই গোনা হয়। Feedback rule (unfinished + 1) × recent average processing time হিসাব করে ছোটটা বেছে নেয়; এর নাম SED। Recent average হলো EWMA। কোনো worker অনেকক্ষণ কাজ না পেলে feedback rule একটা ছোট probe image পাঠায়, আর সেটা overhead হিসেবে গোনা হয়।

## 4. Why the feedback rule might help, and why it might not

It might help when workers have different speeds. Round-robin and rule 3 don't know speed directly. A slow worker keeps getting its share under round-robin, and its queue grows.

It might not help, or might even lose, for several reasons:

- When both workers have the same speed, the feedback rule and rule 3 make the same choice. Theory says so (Selen et al., Queueing Systems 2016). So in our first two scenarios we expect no clear difference between them.
- Rule 3 adjusts on its own, too. A slow worker finishes later, so its unfinished count rises, and rule 3 sends it less. The gap between rule 3 and the feedback rule may be small.
- The average is always a bit old. It knows how the worker did recently, not how big the next image is.
- Probes and the extra bookkeeping cost CPU time on the dispatcher.
- At light load, there's hardly any waiting, so all four rules may look the same.

Our job is to measure which of these wins in our setup. If the feedback rule doesn't help, that is a real result and goes in the paper with the same care.

বাংলায়: Worker-দের গতি আলাদা হলে feedback rule সুবিধা দিতে পারে। কিন্তু গতি সমান হলে সেটা least unfinished requests-এর মতোই সিদ্ধান্ত নেয়। Least unfinished নিজেও ধীর worker-কে কম কাজ দেয়, কারণ তার অসমাপ্ত request বাড়ে। Average সবসময় একটু পুরোনো, আর probe-এর খরচ আছে। Feedback হারলে সেটাও সৎভাবে লিখতে হবে।

## 5. Virtual machines from zero

### What a virtual machine is

A virtual machine (VM) is a computer made of software that runs inside a real computer. The real computer is the host. Each VM is a guest. A guest gets its own operating system, its own share of CPU and memory, and its own network address. From inside, it looks and acts like a separate PC.

VirtualBox is the free program we use to create and run VMs. You tell it how much memory and how many virtual CPUs (vCPUs) each VM gets, attach an Ubuntu installer, and install Ubuntu the same way you would on a real PC.

### Why we use VMs instead of three programs on one laptop

- Each worker gets its own vCPU, so they don't fight over the same CPU core the way two programs on one laptop can.
- Requests really travel over a (virtual) network between machines, like in a real service.
- Linux inside the VM lets us limit one worker's CPU in a controlled, recorded way (section 7). That doesn't work on Windows or on Google Colab, and Colab can't run three VMs at all.
- It matches the plan in our frozen proposal.

### The pieces you will meet

- Ubuntu Server 24.04 LTS is the operating system inside each VM. "Server" means no desktop, only a text terminal.
- A host-only network is a private network that connects the host and the VMs. Nothing outside the PC can reach it. Each VM gets a fixed address on it.
- SSH is how you log in to a VM's terminal from the host, and how our scripts send commands to the VMs. Keys are used instead of typing passwords.
- systemd is the part of Ubuntu that starts and stops programs as services. Our worker and dispatcher run as services, so "reset" can simply mean "restart the service".
- sudo lets a user run admin commands. Our setup allows only the few exact commands the scripts need.
- Python 3.12 runs all our code, both on the VMs and on the host.

### What you don't need to master

You don't need to understand how VirtualBox works inside. You need to be able to create a VM, give it the right memory and CPU, install Ubuntu, connect it to the host-only network, and log in with SSH. The setup guide (issue #6) will list every step.

বাংলায়: Virtual machine হলো একটা আসল কম্পিউটারের ভেতরে software দিয়ে বানানো আলাদা কম্পিউটার। আসলটা host, ভেতরেরগুলো guest। VirtualBox দিয়ে VM বানাই, প্রতিটাকে নির্দিষ্ট RAM আর vCPU দেই, তারপর Ubuntu Server install করি। Host-only network দিয়ে host আর VM-গুলো নিজেদের মধ্যে যোগাযোগ করে। SSH দিয়ে VM-এ login করি, আর systemd service হিসেবে worker ও dispatcher চলে। VirtualBox-এর ভেতরের সব বোঝা লাগবে না; VM বানানো, install করা আর SSH দিয়ে ঢোকা জানলেই চলবে।

## 6. Our testbed

The main runs happen on a teammate's PC with VirtualBox (12 logical CPUs, 13.9 GB RAM, per the frozen documents). Its host operating system is not confirmed yet. Code is written and tested on any laptop first, as plain programs on localhost, without VMs.

```text
Teammate's PC (host)
├── Load generator   sends the requests on a fixed schedule, measures response time
├── Orchestrator     runs each experiment step by step, collects the files
│
├── Dispatcher VM    1 GB RAM, 1 vCPU   picks a worker with one of the four rules
├── Worker 1 VM      2 GB RAM, 1 vCPU   resizes images
└── Worker 2 VM      2 GB RAM, 1 vCPU   resizes images (slowed in scenario 3)
```

One request's path:

```text
load generator --image--> dispatcher --image--> worker
load generator <--result-- dispatcher <--result-- worker
```

Each worker does the same work for every request: decode the JPEG, resize to half width and half height with Pillow's LANCZOS filter, save as JPEG quality 80. It times only that work and sends the time back in a header. It never caches, so two identical requests cost the same.

The images are synthetic: a seeded script draws gradients, shapes, and noise at three sizes (small, medium, large). Seeded means the same seed number gives exactly the same images, so anyone can rebuild them.

A limit we must state in the paper: all three VMs share one physical PC. Other programs on that PC can disturb the results, so we close them during runs and record host CPU.

বাংলায়: Main run হবে একজন teammate-এর PC-তে, VirtualBox দিয়ে। Host-এ load generator আর orchestrator চলবে, আর তিনটা VM-এ dispatcher ও দুইটা worker। প্রতিটা worker একই কাজ করে: ছবি অর্ধেক করে, JPEG quality 80-তে save করে, আর শুধু সেই কাজের সময় মেপে ফেরত পাঠায়। ছবিগুলো seed দিয়ে বানানো, তাই একই seed দিলে হুবহু একই ছবি পাওয়া যায়। সব VM এক PC-তে, এটা limitation হিসেবে লিখতে হবে।

## 7. How we slow one worker down

Scenario 3 needs one worker slower than the other. Both worker VMs are identical, so we create the difference on purpose with a Linux CPU quota on worker 2's service.

A quota says: in every short period of time, this service may use only so much CPU. As an example only (the real values come from the pilot), a 50% quota with a 100 ms period means the worker may use 50 ms of CPU in each 100 ms. Once it has used its 50 ms, Linux pauses it until the next period starts.

So the slowed worker is not "a slower CPU". It runs at full speed in bursts and then gets paused. That's why we call it CPU-quota-limited in the paper. Linux keeps counters of how often it paused the service (in a file called cpu.stat). We read those counters before and after every run, in every scenario, to prove the quota was active in scenario 3 and absent in the others.

The quota is fixed for the whole run. A scenario where speed changes during a run is future work, not part of this project.

বাংলায়: Scenario 3-এ worker 2-কে ইচ্ছা করে ধীর করা হয় Linux CPU quota দিয়ে। Quota মানে প্রতি ছোট সময়ে service কতটুকু CPU পাবে তার সীমা। সীমা শেষ হলে Linux তাকে পরের period পর্যন্ত থামিয়ে রাখে। তাই এটা "ধীর CPU" না, বরং থেমে থেমে চলা worker। cpu.stat counter দেখে প্রমাণ করব quota কাজ করেছে। Run চলাকালীন গতি বদলানো future work।

## 8. How one experiment run works

A run is one rule, in one scenario, at one request rate, for a fixed length of time. The orchestrator does the same steps every time:

1. Write "started" in the run ledger (a list of every run and how it ended).
2. Apply the CPU quota to worker 2 for scenario 3, or clear it for scenarios 1 and 2, and check it took effect.
3. Restart both workers and the dispatcher, so no queue or old average carries over from the last run. The dispatcher sends its warm-up requests and only then reports itself ready.
4. Read the throttling counters and the dispatcher's CPU time. Start the resource samplers, which record CPU and RAM every second on each machine.
5. Run the load generator with that run's saved schedule and wait until every request has ended.
6. Read the counters again, stop the samplers, and collect every log file onto the host.
7. Write the run's details (code version, settings, seeds, counters) and a summary.
8. Mark the run "finished" in the ledger, or "failed" with the reason.

### Open loop: why the load generator doesn't wait

Before a run, the load generator makes a schedule: a list of send times and which image each request carries. The gaps between send times are random, averaging 1 ÷ rate (a Poisson schedule). Then it sends each request at its planned time, whether or not earlier answers have come back. This is called open loop.

The opposite, closed loop, sends the next request only after an answer arrives. That hides slowness: if the system slows down, the client sends less, and the system looks better than it is. Real users don't wait for each other, so we use open loop.

Response time is measured from the planned send time, not the actual one. If our own sender falls behind, that delay counts against the system instead of hiding. We also log how far behind schedule each send was, and the share of requests actually sent, to check the sender itself.

### Same requests for every rule

The schedule comes from a seed made from the scenario, the rate, and the round. So within one round, all four rules get exactly the same requests at exactly the same planned times. Different rounds get different schedules, so the five repeats aren't copies of each other.

### Time budget and expiry

The dispatcher gives up on a request after a fixed timeout and answers "timeout". It also tells the worker how long it will wait (a time budget). If a request has waited in the worker's queue past its budget, the worker skips it instead of resizing an image nobody is waiting for. That ending is called expired.

বাংলায়: একটা run মানে একটা rule, একটা scenario, একটা rate। Orchestrator প্রতিবার একই ধাপ মানে: quota ঠিক করা, service restart, warm-up, counter পড়া, load পাঠানো, ফাইল সংগ্রহ, summary লেখা। Load generator open loop, মানে উত্তরের জন্য না থেমে নির্ধারিত সময়ে request পাঠায়। Response time মাপা হয় planned send time থেকে। একই round-এ চারটা rule হুবহু একই request পায়। Queue-তে budget-এর বেশি অপেক্ষা করলে worker সেই request বাদ দেয়, একে expired বলে।

## 9. What we measure

- Mean response time: the average, over successful requests.
- p95 response time: 95% of successful requests were at or faster than this value. It shows the slow tail that a mean hides. We use the nearest-rank method: sort the times and take the one at position ceil(0.95 × n). With 20 requests, that's the 19th smallest. p95 is not the maximum.
- p95 per image size class in scenarios 2 and 3. This shows whether small images get stuck behind large ones under each rule.
- Successful throughput: successful answers per second, shown next to the rate we offered. Below overload, every rule should finish about what we send, so throughput differences are expected mainly at the highest rate.
- Failures by type: rejected (queue full), expired (budget passed while waiting), timeout (dispatcher gave up), error (anything else).
- CPU and RAM on each machine, every second.
- The feedback rule's cost: number of probes, dispatcher CPU time, and the time spent choosing a worker, reported for all four rules so they can be compared.
- The achieved sending rate. A run that misses the planned rate by more than a set tolerance is kept and flagged, never deleted.

Requests planned in the first W seconds of each run are left out of the summary, because the system is still settling. This dropped window is separate from the warm-up requests, and the pilot sets W.

বাংলায়: আমরা মাপব mean আর p95 response time, ছবির size অনুযায়ী p95, successful throughput, failure-এর ধরন (rejected, expired, timeout, error), প্রতিটা machine-এর CPU ও RAM, আর feedback rule-এর খরচ (probe সংখ্যা, dispatcher CPU, worker বাছাইয়ের সময়)। p95 মানে ৯৫% request এই সময়ের মধ্যে বা আগে শেষ হয়েছে; এটা সর্বোচ্চ মান না। শুরুর কয়েক সেকেন্ড বাদ দেওয়া হয়।

## 10. The full experiment plan

| Part | Values |
|---|---|
| Rules | round-robin, weighted round-robin, least unfinished requests, feedback |
| Scenarios | 1 uniform images (medium only), 2 mixed sizes, 3 mixed sizes with worker 2 CPU-quota-limited |
| Rates | three per scenario: light, queues forming, near overload (chosen in the pilot) |
| Conditions | 4 × 3 × 3 = 36 |
| Rounds | 5, each running all 36 conditions once in a shuffled order |
| Main runs | 180 |

Every rule runs in every scenario. The frozen slide 7 showed only three filled cells; the revised plan fills the whole table.

### Why shuffle

If we ran all round-robin runs first and all feedback runs last, anything that changed over time on the PC (heat, a background update) would look like a rule difference. Shuffling each round's order with a saved seed spreads that out.

### How we decide a difference is real

For each condition we have five runs. We report the median of the five values with the smallest and largest. We call a difference between two rules clear only when their five-run ranges don't overlap. Otherwise we write "no clear difference under these conditions". We don't run significance tests.

Made-up numbers, only to show the rule:

```text
Rule X p95 over five runs: 210 to 260 ms
Rule Y p95 over five runs: 300 to 340 ms   -> no overlap, clear difference
Rule Z p95 over five runs: 240 to 310 ms   -> overlaps X, no clear difference
```

### The pilot comes first

Many settings can't be guessed: the rates, the image sizes, the quota, the queue size, the timeout, the EWMA weight, the probe time T, the run length. The pilot is a set of short measurement steps on the real VMs that decides each of them by a written rule (the table in `implementation/spec.md`). Every value goes into `notes/decisions.md` with how it was chosen. Then the settings are frozen in one config file, and the code refuses to start a main run if any setting is still empty or the code has uncommitted changes. That stops anyone from tuning after seeing results.

The real order of work is: build and test on a laptop, set up the VMs, pilot, calibrate weights, freeze, one short dry run of all 36 conditions, then the 180 main runs.

বাংলায়: চারটা rule × তিনটা scenario × তিনটা rate = ৩৬টা condition, পাঁচ round মিলিয়ে ১৮০টা main run। প্রতি round-এ order shuffle করা হয় যাতে সময়ের প্রভাব কোনো rule-এর ঘাড়ে না পড়ে। পাঁচটা run-এর range একটার সঙ্গে আরেকটার না মিললে তবেই পার্থক্যকে "clear" বলব। Rate, image size, quota, queue size ইত্যাদি pilot-এ মেপে ঠিক করা হবে, তারপর config freeze। এরপর আর কিছু বদলানো যাবে না।

## 11. What we expect to see

We wrote these down before any run. The paper reports each one as held, not held, or unclear.

- H1. In scenarios 1 and 2 (equal workers), the feedback rule and least unfinished requests show no clear difference.
- H2. In scenario 3 (one slowed worker), the feedback rule and weighted round-robin have lower p95 than round-robin and least unfinished requests, and the gap is larger at the highest rate.
- H3. At the lightest rate, the four rules show no clear difference.

H2 might well fail for least unfinished requests, since that rule already sends less to a worker whose queue grows. If it does, we say so. A hypothesis that doesn't hold is still a result.

বাংলায়: Run-এর আগেই তিনটা প্রত্যাশা লিখে রেখেছি। H1: সমান worker-এ feedback আর least unfinished-এর মধ্যে clear পার্থক্য থাকবে না। H2: ধীর worker থাকলে feedback আর weighted round-robin-এর p95 কম হবে। H3: সবচেয়ে কম rate-এ চারটা rule প্রায় একই। কোনোটা না মিললে সেটাও ফল হিসেবে লিখব।

## 12. What is built and what is left

The build is split into GitHub issues. Issue #1 holds the full spec, and issue #8 tracks progress. The order is in `implementation/ORCHESTRATION.md`.

| Issue | What it is, in plain words | Status |
|---|---|---|
| #2 | The shared settings code, the image generator, and the worker service | Done, merged |
| #3 | The dispatcher with all four rules, warm-up, probes, and its log | Not started |
| #4 | The load generator (schedule, open-loop sending) and the per-run summary | Not started |
| #5 | The orchestrator that runs one whole run or a whole round on a laptop, plus the CPU and RAM samplers and the ledger | Not started |
| #6 | The VM setup guide, service files, scripts, and the SSH version of the orchestrator | Not started |
| #7 | One command per pilot step, plus the dry-run check | Not started |

#3 and #4 can be built at the same time. #5 needs both. #6 and #7 come after #5 and can be built together.

What is not an issue yet, and will need one later:

- The week 6 analysis scripts: medians across five runs, the H1 to H3 verdicts, the overhead table, and the plots.
- The term paper itself.

What only works on the teammate's PC, after #6 and #7:

- Building the three VMs from the guide and checking that the quota really pauses worker 2.
- Running the pilot steps and recording each value.
- Freezing the config and running the dry run until it passes.
- The 180 main runs.

বাংলায়: কাজগুলো GitHub issue-তে ভাগ করা। #2 (worker আর shared code) শেষ। বাকি আছে #3 dispatcher, #4 load generator ও summary, #5 orchestrator, #6 VM setup, #7 pilot tools। #3 আর #4 একসঙ্গে করা যায়। Analysis script আর term paper-এর জন্য এখনো issue নেই। VM বানানো, pilot, freeze, dry run আর ১৮০টা run teammate-এর PC-তে আমাদেরই করতে হবে।

## 13. Who does what

### What an AI agent can do

- Write the code for issues #3 to #7, test-first, one issue per branch, with a pull request each. Each issue already lists what "done" means and how to check it.
- Write the VM setup guide and scripts (part of #6).
- Later, write the analysis scripts and plots from the raw files, once we open an issue for them.
- Explain any part of the code or a result when we ask, and help us check a draft of the paper for mistakes.

An agent can't touch the teammate's PC or the VMs, can't press buttons in VirtualBox, and can't run the real experiments. It also can't decide things that are ours to decide.

### What only we can do

- Get the PC ready: VirtualBox installed, hardware virtualization turned on in the BIOS if it's off, enough free disk space for three VMs.
- Build the three VMs by following the guide, and tell the agent exactly what went wrong if a step fails (copy the error text).
- Run the pilot commands and read their output. Some choices are a team decision, such as the mix of small, medium, and large images. Record each value and the reason in `notes/decisions.md`.
- Approve the frozen config, and from then on change nothing.
- Run the 180 main runs. Keep the PC quiet while they run: other programs closed, no updates, plugged in, sleep turned off. A failed run is rerun at the end of its round; never delete it.
- Read the papers we cite, at least the parts behind each claim. A reviewer may ask.
- Write the term paper, or at least own it: decide what it says, check every number against the result files, and be able to explain every part.
- Take screenshots of the VMs and runs for the demo.
- Prepare for questions. The course says every member must understand and explain the submitted work.

One more thing to check: find out what your course allows for AI help in writing the paper, and follow it. If you're unsure, ask the instructor and say in the paper how AI was used.

বাংলায়: Agent কোড লিখতে পারবে (#3 থেকে #7), setup guide লিখতে পারবে, পরে analysis script আর plot বানাতে পারবে, আর ব্যাখ্যা দিতে পারবে। কিন্তু PC আর VM-এ হাত দিতে পারবে না, আসল experiment চালাতে পারবে না, আর আমাদের সিদ্ধান্তও নিতে পারবে না। আমাদের কাজ: PC তৈরি করা, guide দেখে VM বানানো, pilot চালিয়ে মান লিখে রাখা, config freeze করা, ১৮০টা run চালানো, paper পড়া ও লেখা, screenshot নেওয়া, আর প্রশ্নের জন্য প্রস্তুত হওয়া। AI ব্যবহারের নিয়ম course-এ কী, সেটা জেনে নিতে হবে।

## 14. Turning this into the term paper

The course wants 10 to 15 pages with these sections and at least 8 references (`paper/README.md`). Here is where each section's material comes from.

| Section | What goes in | Where it comes from |
|---|---|---|
| Abstract | The question, the setup, what was measured, the main finding with its conditions | Written last, from the results |
| Introduction | Why equal counts can hide unequal work; the research question | Slide 2, section 2 of this guide, `paper/revised-proposal.md` |
| Objectives | Build the testbed, implement the four rules, run repeatable tests, analyze | Slide 4 |
| Background and literature review | Load balancing basics, SED theory, real systems, earlier comparisons, how to run fair experiments | `paper/references.md`, `paper/literature/gap-analysis.md`, the summaries |
| Main discussion | The setup, the full 36-condition matrix, results, H1 to H3, the overhead table, p95 per size | Results and plots from week 6 |
| Challenges and limitations | One host, two workers, one workload, a quota is not a slower machine, five runs per condition | Sections 6, 7, and 10 of this guide |
| Future trends or recommendations | Which rule fits setups like ours; speed changing during a run; size-aware rules; more workers | Results plus the dropped items in the implementation plan |
| Conclusion | What held and what didn't | H1 to H3 verdicts |
| References | At least 8, each tied to a claim | `paper/references.md` (15 planned) |

Things to bring from our side, which no tool can give:

- Our own explanation of the results in plain words. Why did a rule win or lose in a given cell? The dispatcher log records the counts and averages behind every decision, so we can look at real cases.
- Honest limits. Write what our setup can't show.
- A clear story: the problem (section 2), the rules (section 3), the test (sections 8 to 10), what happened, what it means for someone choosing a rule.
- Our own pictures: the testbed diagram, a screenshot of VirtualBox with the three VMs, the plots.

Rules for the writing itself are in `AGENTS.md`: plain words, no inflated claims, never present a planned run as done, and never invent a number.

বাংলায়: Course চায় ১০ থেকে ১৫ পৃষ্ঠার paper আর কমপক্ষে ৮টা reference। Introduction আসবে slide 2 আর এই guide থেকে, literature review আসবে `paper/references.md` আর gap analysis থেকে, main discussion আসবে week 6-এর ফল থেকে। আমাদের নিজেদের কাজ: ফলের সহজ ব্যাখ্যা, সৎ limitation, একটা পরিষ্কার গল্প, আর নিজেদের ছবি ও screenshot। কোনো সংখ্যা বানানো যাবে না।

## 15. What each of us must understand

Each of us should be able to answer these without notes. If one is hard, reread the section in brackets.

1. What problem does load balancing solve, and why do unequal jobs make it harder? (2)
2. How does each of the four rules choose a worker? Work out examples A and B by hand. (3)
3. Why might the feedback rule not win? (4)
4. What is a VM, and why do we use three VMs instead of three programs on a laptop? (5)
5. How does the CPU quota slow worker 2, and why isn't it the same as a slower CPU? (7)
6. What is open loop, and why do we measure from the planned send time? (8)
7. What does p95 mean, and how is it computed? (9)
8. How many runs are there, why are they shuffled, and when do we call a difference clear? (10)
9. What are H1 to H3? (11)
10. What did the pilot decide, and why can't we change it after the freeze? (10)
11. What can our results say, and what can't they say? (6, 7, and the revised proposal's "What we do not claim")

The speaker split from the defense stays as a starting point for paper ownership: Mahim knows the motivation and question best, Ikramul the rules and architecture, Omlan the experiment plan. Everyone still needs all eleven answers.

বাংলায়: উপরের এগারোটা প্রশ্নের উত্তর সবার নোট ছাড়া দিতে পারা উচিত। কোনোটা কঠিন লাগলে বন্ধনীর section আবার পড়ুন। Defense-এর speaker ভাগ paper-এর দায়িত্বের শুরু হিসেবে রাখা যায়, তবে সবাইকে সবকিছু বুঝতে হবে।

## 16. Words you will see

| Word | Meaning |
|---|---|
| Dispatcher | The machine that receives every request and picks a worker |
| Worker | A machine that does the image work |
| Rule | The way the dispatcher picks a worker |
| Request | One image sent for resizing |
| Queue | Requests waiting at a worker while it is busy |
| Unfinished | Sent to a worker by the dispatcher and not yet answered |
| Response time | Planned send time to answer received |
| p95 | 95% of successful requests were at or below this time |
| Throughput | Successful answers per second |
| Rejected | Worker queue was full, answered 503 at once |
| Expired | Waited in the worker queue past its time budget, skipped |
| Timeout | The dispatcher stopped waiting |
| EWMA | A running average where each new value moves it part of the way |
| SED | Shortest expected delay, the theory name for our feedback rule |
| Probe | A small test image sent by the feedback rule to an idle worker |
| Warm-up | A few requests sent to both workers before every run |
| Open loop | Sending at planned times without waiting for answers |
| Seed | A number that makes random choices repeatable |
| Scenario | One of the three test situations |
| Condition | One rule in one scenario at one rate |
| Round | All 36 conditions once, in a shuffled order |
| Pilot | Short measurements that decide the settings before the main runs |
| Calibration | Measuring each worker's throughput to set the weights |
| Freeze | Locking code and settings before the main runs |
| Host / guest | The real PC / a VM running on it |
| vCPU | A virtual CPU given to a VM |
| Host-only network | A private network between the PC and its VMs |
| SSH | Logging in to another machine's terminal over the network |
| systemd service | A program Ubuntu starts, stops, and restarts for us |
| CPU quota | A Linux limit on how much CPU a service may use per period |
| cpu.stat | The Linux file that counts how often the quota paused a service |
| Ledger | The list of every run and how it ended |

## 17. Giving tasks to an agent

The issues are written so an agent can pick one up and finish it. A good task message names the issue, points to the rules, and says what you want back. For example:

```text
Implement issue #3 (dispatcher with the four routing rules) in this repository.
Follow AGENTS.md and implementation/ORCHESTRATION.md. Work on a branch named
feat/3-dispatcher-four-rules, build it test-first, run every verification
step in the issue, open a pull request that says "Closes #3", and show me the
test output. Ask me before merging.
```

For two issues at once (#3 and #4 are allowed to run in parallel), give each to its own agent or session, each on its own branch.

A few habits that keep things clean:

- One issue per task. Don't ask for #3 and #5 together; #5 needs #3 and #4 finished first.
- Ask for the test output and the verification commands in the pull request, and read them.
- If the agent says a check can't pass in its environment, believe it, and decide with the owner what to do. Don't let it skip the check.
- Anything that happens on the teammate's PC is ours. The agent can tell us the commands, and we run them and paste back the output.
- When a value has to be decided, the agent should propose and explain; we decide and record it in `notes/decisions.md`.

বাংলায়: Agent-কে কাজ দেওয়ার সময় issue নম্বর বলুন, AGENTS.md আর ORCHESTRATION.md মানতে বলুন, আর test output দেখাতে বলুন। এক task-এ এক issue। #3 আর #4 আলাদা agent-কে একসঙ্গে দেওয়া যায়। PC-তে যা চালাতে হবে তা আমরা চালাব, output agent-কে দেব। কোনো মান ঠিক করতে হলে agent প্রস্তাব দেবে, সিদ্ধান্ত আমাদের।
