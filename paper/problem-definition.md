# Problem definition

Working definition of the problem our project investigates, written before implementation starts. Sources for every factual claim are named. Nothing here describes a measured result; all experiments are planned. The verified citations live in [references.md](references.md).

## The research question

> When does knowing each worker's recent processing speed improve routing enough to justify the extra monitoring?

The defense study guide states this question and adds the honest position: we test whether feedback helps, and we do not assume it wins. This document expands the question into a form that can be implemented, measured, and defended.

## Layer 1: the general problem in the literature

Three established findings define the territory.

**Equal counts can hide unequal work.** A dispatcher that routes by position (round-robin) or by fixed shares (weighted round-robin) balances the number of requests each worker receives. It does not balance the amount of processing those requests need. One long image resize can hold a worker for many multiples of a short one. Prequal (NSDI 2024) makes exactly this argument at production scale: balancing a scalar "load" is the wrong target when request costs differ.

**Dispatcher information is stale.** Join-Idle-Queue (Performance Evaluation 2011) shows that the queue information a dispatcher holds lags the true state of workers, because assignments and completions propagate with delay. Mitzenmacher (TPDS 2001) gives the complementary theory: when job sizes are similar, counting unfinished work is a strong signal, and simple count-based selection captures most of the achievable benefit. Together these say where count-based routing works and why it fails.

**The simple rule has known limits.** Detti and Funari (ToNSM 2025) document measured failure modes of least outstanding request routing, the industry name for our least-unfinished rule, in service mesh deployments. Wang, Feng, and Cheng (ToN 2018) give the matching theory: distributed idle-feedback dispatching reaches low mean and tail response time in large systems, and does not always beat simpler policies. So the literature says the simple rule is good, not perfect, and says the feedback idea behind our fourth rule is sound, not universally superior.

## Layer 2: the specific gap our project fills

The published work evaluates at hyperscale, in simulation, or at theoretical extremes. What is missing for our purposes is a controlled, small-scale measurement that answers one question end to end: at two workers, three workload scenarios, and three request rates, how much does recent-speed feedback improve response time, and what does it cost to collect?

The gap is worth filling for three reasons.

1. The trade-off is genuinely two-sided. Monitoring adds per-request bookkeeping, possible probes of idle workers, and risk from stale estimates. At two workers the overhead may exceed the benefit. If it does, that is a finding.
2. The result is checkable. Two workers on one host make the comparison transparent: every routing decision, every queue state, and every estimate is inspectable in our logs.
3. The result is teachable. The four rules span the classic design space: no information, static information, current counts, and recent timing. A clean comparison of all four at matched conditions is a contribution a course paper can actually deliver.

## The dispatcher's decision, made precise

At each request arrival, the dispatcher picks one of two workers. Each rule uses different information:

| Rule | Information used | Information cost |
|---|---|---|
| Round-robin | Position in rotation | One counter |
| Weighted round-robin | Fixed weights from calibration | Two numbers, chosen before runs |
| Least unfinished | Per-worker count of assigned, unfinished requests | Per-worker counter updated at assignment and completion |
| Feedback | Unfinished count and recent average processing time per worker | Per-worker counter plus a timing average, plus probe traffic for idle workers |

The feedback rule computes `(unfinished + 1) x recent_average_processing_time` per worker and selects the smaller estimate. The plus one represents the incoming request. The estimate is deliberately rough: it does not know the size of the new image, how far the running image has progressed, or why a worker's speed changed. The research question is whether this rough estimate buys more than its bookkeeping costs.

The information costs are the second half of the question. Probe requests sent to idle workers, extra state updates, and any per-request arithmetic all belong on the cost side. The defense guide already requires that probe traffic be counted rather than hidden.

## System model

The planned testbed, from the frozen proposal in `final/`:

```text
Host (12 logical processors, 13.9 GB RAM)
├── Load generator: controlled image set, fixed request schedule
├── Dispatcher VM: 1 GB RAM, 1 vCPU, runs one of the four rules
├── Worker VM A: 2 GB RAM, 1 vCPU, resize and recompress
└── Worker VM B: 2 GB RAM, 1 vCPU, same code
```

- Each worker processes one image at a time; additional accepted requests wait in a bounded queue.
- Responses return through the dispatcher to the client; processing time is measured at the worker on a monotonic clock.
- All three VMs share one physical host. This is a documented limitation, not a hidden one: shared CPU, RAM, and disk can affect both workers, and Felter et al. (ISPASS 2015) note virtualization overheads are real but usually small for CPU-bound work.

### Controlled factors

| Factor | Planned levels |
|---|---|
| Routing rule | round-robin, weighted round-robin, least unfinished, feedback |
| Job mix | uniform images; mixed sizes; mixed sizes with one slowed worker |
| Worker capacity | equal; unequal via Linux CPU quota on one worker |
| Offered request rate | three rates, fixed after the pilot |
| Repetitions | at least five per condition, run order varied |

### Measured quantities

Mean response time and p95 at the client; throughput in completed requests per second; failures and timeouts, reported with the latency sample rather than separately from it; CPU and RAM for dispatcher, workers, and load generator; planned versus achieved sending rate.

The p95 choice follows Dean and Barroso (CACM 2013): tail latency is what users feel, and a mean alone hides it. The p95 is not the maximum; an isolated extreme delay can fall outside it, which the defense guide now words correctly.

## The measurable form of the question

For each scenario and rate, the comparison produces a benefit number and a cost number:

- Benefit: response-time improvement of feedback over each baseline (mean and p95), plus any throughput or failure-rate difference, judged against run-to-run variation.
- Cost: dispatcher CPU and RAM attributable to state and arithmetic, probe traffic and its measured effect, plus implementation complexity.

The question has a defensible answer when, for each tested condition, we can state one of: feedback helped by more than the observed variation; feedback did not help under the tested conditions; or the difference was within variation and we cannot distinguish the rules there. All three are valid findings.

### Falsifiable hypotheses

These are predictions to test, not results. They come from the theory above.

- H1: with uniform images and equal workers, the four rules land within run-to-run variation of each other, especially below saturation (Mitzenmacher: counts are sufficient when jobs are similar).
- H2: with mixed sizes under load, least-unfinished and feedback beat round-robin and weighted round-robin on p95, because the count-based rules stop sending new work to a worker holding a long job.
- H3: with one slowed worker, feedback keeps p95 lowest among the rules, because its recent-average term discounts the slowed worker while least-unfinished adapts only after queues build.
- H4: at the lowest rate, all rules converge to similar response times because queueing is negligible (Wang, Feng, and Cheng: differences concentrate away from the idle extreme).
- H5: feedback overhead at this scale is negligible relative to image processing time, but probe traffic is measurable and must be reported.

H1 to H5 can each be refuted by our own runs. The paper reports what the runs show, including null results, per the repository's research honesty rules.

## Boundaries

What this problem definition does not cover:

- No claim about public clouds, real networks, or worker counts above two.
- No claim about dynamic adaptation: a fixed CPU quota tests unequal capacity. A mid-run slowdown and recovery experiment is not specified in the proposal, so adaptation time stays out of scope unless the team defines it.
- No new algorithm claim. The feedback rule is a simplified reading of published ideas, cited as such.
- No cost or energy claims. The project avoids paid cloud services and does not measure money or energy.

## Open parameters this definition leaves to implementation

The definition fixes the question, the model, and the hypotheses. It deliberately leaves numeric parameters open, because the proposal leaves them open and the team must decide them before the main runs. The full list is in [../notes/open-questions.md](../notes/open-questions.md): request rates, run duration, image set, weight ratio and calibration condition, averaging method for the recent mean, CPU quota value, queue capacity and rejection behavior, probe policy, timeouts, percentile calculation method, throughput definition, monitoring scope, reset procedure, and the criterion for a meaningful difference. Each decision gets recorded in `notes/decisions.md` with its source before the main runs, and stays fixed afterwards.
