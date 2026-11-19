# Proposal audit: inconsistencies, overclaims, and misalignments

Checked on 2026-11-19 against the frozen files in `final/` and the notes in this repository. Nothing in `final/` was edited. Each finding names the file it comes from and a fix. Fixes that touch `final/` need owner approval recorded in `notes/decisions.md`; most fixes below go into the term paper and the implementation instead, so the frozen files can stay as they are.

Findings that depend on the literature search are marked "lit" and cite the summaries in `paper/literature/summaries/`. The literature gap analysis is in `paper/literature/gap-analysis.md`.

Severity: high means a reviewer could reject a claim or the result could be invalid. Medium means a reviewer will probably ask. Low means wording or bookkeeping.

## Triage after the owner's scope review (2026-11-19)

The owner asked to keep novelty but avoid promising too much. Each finding is now keep (fix as written), simplify (fix in a smaller way), or drop (no action). Where this table and a "Fix" paragraph below disagree, this table wins. The result is `paper/revised-proposal.md` and the updated `implementation/implementation-plan.md`.

| ID | Status | What we do |
|---|---|---|
| A1 | Keep | Full 36-condition matrix in the paper |
| A2 | Keep | One name: least unfinished requests |
| A3 | Drop | Proposal stage is over; no action |
| A4 | Keep | Owner: proposal PDF superseded by the revised proposal |
| A5 | Keep | Weights from profiled throughput per scenario (Aslanpour et al. 2024, Section 4.2), owner asked for a published method |
| A6 | Keep | Throughput shown next to offered rate and failures |
| B1 | Keep | Prequal as motivation, not basis |
| B2 | Simplify | Owner: reword to "unequal speed"; dynamic scenario dropped to future work |
| B3 | Keep | Wording only |
| B4 | Keep | Wording only |
| B5 | Simplify | One simple probe rule, counted as overhead |
| B6 | Keep | Run length chosen in the pilot to fit the schedule |
| C1 | Keep | Name the rule SED-style |
| C2 | Keep | H1 to H3 written before the runs |
| C3 | Keep | Open-loop seeded schedule |
| C4 | Simplify | Five shuffled rounds; no extra rounds from the variability check |
| C5 | Simplify | Median with min and max; "clear" only with non-overlapping ranges; no significance tests |
| C6 | Simplify | systemd CPUQuota in the VM, record quota and period, read cpu.stat |
| C7 | Keep | Part of the novelty claim |
| C8 | Keep | Reference table in the revised proposal |
| C9 | Keep | Owner chose per-size p95 as part of the novelty claim |

Correction: the first version of this audit was reported in chat as having 23 findings. The real count is 21 (A1 to A6, B1 to B6, C1 to C9).

## A. Internal inconsistencies

### A1. The slide 7 matrix shows 3 cells, the plan says 36 conditions (high)

Slide 7 of `final/Performance-Aware Load Balancing.pdf` shows a 3 by 4 grid (scenario by rule) with "3 rates × 5 runs" in only three cells: round-robin for uniform images, least unfinished for mixed sizes, and feedback for one slowed worker. The other nine cells are empty. The defense guide (section 9.1) says every rule runs in every scenario: 4 × 3 × 3 = 36 conditions and at least 180 main runs. A reader of the slide alone could think each scenario is tested with one rule, which would make the comparison impossible.

Fix: in the paper, draw the full matrix with every cell filled, and state "36 conditions, at least 5 runs each, at least 180 main runs, pilot runs excluded" once. In the defense, say the shaded cells were meant as examples. No change to `final/` is needed.

### A2. The rule is called "least connections" in some files and "least unfinished requests" in others (medium)

`README.md`, `implementation/README.md`, and `notes/decisions.md` say "least connections". Slide 5 and the defense guide (section 7.3) say "least unfinished requests" and define it as running plus waiting requests counted at the dispatcher, and the guide says it "is not the same as blindly using TCP connection counts". `AGENTS.md` lists "least connections" as a protected project term.

Fix: pick one primary name for the paper. Suggested wording: "least unfinished requests (a least connections rule that counts requests, not TCP connections)". Use it the same way in code names, plots, and the paper. Record the choice in `notes/decisions.md`.

### A3. Slide order differs between the presentation guide and the deck (low)

`final/Cloud_Load_Balancing_Presentation_Guide.docx` puts the ending on slide 9 and references on slide 10, and its heading says "9 talk slides + 1 backup" while its requirements table says "8 talk slides". The deck has references on slide 9 and the ending on slide 10. The defense guide already corrects this ("Important slide-order correction") and `notes/decisions.md` records the deck order. The proposal stage is over, so this only matters if the presentation guide is reused.

Fix: none needed for the paper. Do not reuse the slide numbers from the presentation guide.

### A4. The written proposal is cited but not in the repository (medium)

Section 18 of the defense guide names `Cloud_Load_Balancing_Proposal.pdf` as the source of the technical plan (pages 1 to 3) and links `Cloud_Load_Balancing_Presentation_Guide.pdf`. Neither PDF is in `final/`. `notes/decisions.md` says superseded drafts were removed and a backup is kept outside the repository. So the most detailed technical source cannot be checked from the repository.

Fix: the owner decides whether the proposal PDF is superseded or still the technical reference. If it is still the reference, add it (owner approval). If not, record in `notes/decisions.md` that the defense guide is the technical reference.

### A5. Weighted round-robin has no defined weights for scenarios 1 and 2 (high)

Slide 5 says weighted round-robin gives "a known faster worker a larger fixed share", with weights "set during calibration". In scenarios 1 and 2 both workers have the same code, the same VM size, and no quota, so a correct calibration should give 1:1, and weighted round-robin then sends the same sequence as round-robin. The defense guide (section 7.2) says the calibration condition is not final.

Fix: decide and record one of these before the pilot.
1. Calibrate per scenario from a separate calibration run (not a main run), and report that weighted round-robin equals round-robin when the calibrated ratio is 1:1. Run it anyway, because that equality is a check of the setup.
2. Calibrate once on the slowed worker condition and use those weights everywhere. This tests what happens when fixed weights are wrong for the conditions, which is a real limitation of static weights.

Option 1 is easier to defend. Either way, say in the paper that weighted round-robin gets advance knowledge of the quota that the feedback rule must learn at run time.

### A6. Throughput may not separate the rules below overload (medium)

The plan uses an open schedule of requests at fixed rates (defense guide sections 9.4 and 9.5). If the system keeps up, every rule completes about the same number of requests per second as are sent, so throughput will be close to the offered rate for all four rules. It only differs when queues fill and requests fail or time out.

Fix: present throughput together with the offered rate and the failure count, and expect differences mainly at the highest rate. Do not present equal throughput at low rates as a finding about the rules.

## B. Overclaims and risky wording

### B1. "Basis: Prequal (NSDI 2024)" on slide 3 (high, partly lit)

Slide 3 says "Basis: Prequal (NSDI 2024)". The defense guide (Q5) says the project is "not a full reproduction" and cites Prequal as related work. "Basis" suggests the feedback rule is Prequal or derived from it. As described in the Prequal paper, Prequal probes a few servers asynchronously, collects requests in flight and a latency estimate, and picks with a hot-cold rule over those probes. Our rule multiplies unfinished requests plus one by recent average processing time, which is the classic shortest expected delay idea with an online speed estimate (see the queueing summaries in `paper/literature/summaries/`).

Fix: in the paper, say "Prequal motivates the idea that request count and latency signals can beat load signals such as CPU use; our feedback rule is a simpler shortest expected delay style rule, and we do not reproduce Prequal". Do not use "based on Prequal".

### B2. "Worker speed changes" in the research question (high)

Slide 3 asks which rule keeps response time low "when request sizes differ and worker speed changes". Scenario 3 applies a fixed CPU quota for the whole run. The defense guide (Q21 and section 13) says a fixed quota tests unequal capacity, not adaptation to change. The research question promises more than the experiment tests.

Fix, choose one and record it.
1. Reword in the paper: "when request sizes differ and workers have unequal speed".
2. Add a fourth, smaller scenario where the quota is applied part way through a run and removed later, and measure how long each rule takes to recover. This is the only way to answer the "changes" part. It adds work, so treat it as optional and run it only after the main 180 runs are complete.

### B3. "Reproducible comparison" (medium)

Slide 3 and slide 8 promise "reproducible" and "repeatable". Nothing is built yet, so this is a goal. Repeated runs on one host do not show that another team on other hardware gets the same numbers (the defense guide, section 11.5, says this too).

Fix: write "we release code, configuration, raw logs, and analysis scripts so the procedure can be repeated" and report run-to-run variation. Avoid "reproducible results".

### B4. Guidance for "cloud" from one host (medium)

The title says "Performance-aware load balancing" and the course topic is cloud load balancing, but the testbed is two worker VMs on one laptop-class host with a host-only network. The deck already says "We do not claim: ... results for all clouds", which is good.

Fix: keep that sentence in the abstract and the limitations section. Phrase every finding as "in our setup with two workers on one host".

### B5. "Probe idle workers" and "no hidden retries" are promised but not specified (medium)

Slide 5 lists "No hidden retries · Alternate ties · Probe idle workers". Probe content, frequency, and cost accounting are open (`notes/open-questions.md`). A probe that sends a real image adds load that the other rules do not create, and a probe that sends nothing does not measure speed.

Fix: define the probe as a small fixed image sent only to a worker that has had no completion in a set time, count probe requests and their CPU time in the results, and run the other three rules without probes. Report probe count per run.

### B6. The schedule is tight for 180 runs plus pilot (medium)

Slide 4 gives weeks 4 to 5 for experiments. Run length is open. If each run takes a few minutes plus reset, 180 runs fit, but long runs do not.

Fix: fix run length in the pilot with a time budget in mind, script the full matrix so it runs unattended, and keep a log of runs started, finished, and thrown out.

## C. Misalignments between the plan and the literature (lit)

Paper numbers refer to the table in `paper/literature/gap-analysis.md`.

### C1. The feedback rule is shortest expected delay, and the proposal does not say so (high)

Slide 5 calls it "feedback rule" and gives Delay = (unfinished + 1) × recent avg time. That is shortest expected delay (SED) with the service time estimated at run time (papers 5, 6, 9). Finagle and Linkerd describe a similar Peak EWMA cost, and L3 (paper 1) uses a squared form as a traffic weight. A reviewer who knows SED will ask why the paper does not name it.

Fix: in the paper, name it "an SED-style rule with an online estimate of processing time" on first use, cite papers 9 and 5, and mention L3 as the closest recent systems use. Keep "feedback rule" as the short name in plots, since the team already uses it.

### C2. Theory already predicts the uniform scenario outcome (medium)

With equal worker speeds, SED reduces to join the shortest queue (paper 9). So in scenarios 1 and 2, feedback and least unfinished should be close, and weighted round-robin should equal round-robin if the calibrated weights are 1:1 (see A5). If the paper reports this without the prediction, it looks like a failed experiment.

Fix: state the expected pattern before the runs as hypotheses in `notes/decisions.md`. H1: in scenarios 1 and 2, feedback and least unfinished differ by less than the run-to-run spread. H2: in scenario 3, feedback and weighted round-robin beat round-robin and least unfinished on p95, and the gap grows with request rate (paper 6). H3: at the lowest rate all four rules are close. Then report whether each held. A result that contradicts a hypothesis is still reported in full.

### C3. "Timed requests" does not say open loop or closed loop (high)

Slide 6 says "Fixed images and timed requests". If the load generator waits for replies before sending more (closed loop), the slow rule receives less load and its tail is hidden (paper 16). The defense guide's planned versus achieved rate check (section 9.5) is the right idea but does not name the loop type.

Fix: use an open-loop schedule fixed before the run (same seed for every rule), send each request at its planned time whether or not earlier replies came back, and measure response time from the planned send time as well as the actual send time. Log achieved rate and flag a run whose achieved rate misses the plan by more than a tolerance set in the pilot.

### C4. Five runs is fixed in advance, and "varied run order" is not defined (medium)

Slide 7 says "3 rates × 5 runs" and "Varied run order". Paper 15 says the number of repetitions should follow from measured variability. Paper 17 found that running alternatives back to back produced a 38% gap between identical systems, and recommends randomizing the order of all alternatives inside each round.

Fix: keep 5 as the minimum, measure variability in the pilot, and raise the count if the spread is large. Run the main experiment in rounds: one round runs all 36 conditions once in a shuffled order, and 5 rounds give 180 runs. Save the seed and the order.

### C5. Statistics with five runs (medium)

Paper 16 warns that confidence intervals computed from correlated requests inside one run are too narrow. With five runs per condition, a paired Wilcoxon signed-rank test on 5 pairs cannot reach p < 0.05 two-sided (the smallest possible two-sided p is 2/32 = 0.0625). An unpaired Mann-Whitney test with 5 against 5 can (smallest two-sided p is 2/252, about 0.008).

Fix: compute p95 and mean per run, then compare rules across runs. Report the median of the run values with the range or a bootstrap interval, and use Mann-Whitney if a test is wanted. If a paired design is preferred, use more than 5 rounds. Decide this before the runs.

### C6. A CPU quota is not a slower CPU (medium)

Slide 3 says "Linux CPU quota limit". CFS bandwidth control lets the worker run at full speed until its quota for the period is used, then stops it until the next period, and it can throttle more than intended (paper 18 abstract, kernel sched-bwc documentation). This adds pauses that can show up in p95 under every rule. No peer-reviewed free paper was found that measures this effect on a web service's p95, so we cannot cite a size for it.

Fix: decide where the quota is applied (systemd CPUQuota inside the worker VM, or the VirtualBox execution cap on the host) and record the quota, the period, the kernel version, and the cgroup version. Read the throttling counters in cpu.stat before and after every run. In the paper call scenario 3 "a CPU-quota-limited worker", not "a slower machine".

### C7. Overhead is promised but not defined (medium)

Slide 3 says "Evaluate whether monitoring recent speed justifies extra overhead". Paper 11 discusses dispatcher overhead without measuring it, and Prequal treats probe cost as a design goal. Our proposal does not say how overhead is measured.

Fix: measure dispatcher process CPU time per run for every rule, count probe requests and their processing time for the feedback rule, and time the select step itself with perf_counter. Report these next to the latency results.

### C8. The reference list is old and short (medium)

The deck has 6 references, and only Prequal is newer than 2016. The course asks for at least 8 reliable references. Felter et al. (containers versus VMs) has weak relevance because we do not use containers.

Fix: add references from the gap analysis table, mainly papers 1, 5, 6, 9, 11, 14, 15, 16, and 17. Keep Felter et al. only if the paper discusses virtualization overhead. Every reference in `paper/references.md` must name the claim it supports.

### C9. Mixed sizes are analyzed only in total (low)

The plan reports mean and p95 over all requests. Paper 8 shows that size has a large effect at high load. Small images stuck behind large ones are exactly the motivation on slide 2, but the planned metrics do not show it.

Fix: tag each request with its image size class and report p95 per class in scenarios 2 and 3. This costs nothing at run time.

## D. What is already handled well

The defense guide already fixes several risks: the p95 wording (section 10.5), monotonic clocks for elapsed time (section 8), planned versus achieved rate (section 9.5), latency sample definition with failures (section 10.8), "five runs is a minimum" (section 9.6), and the honest answers to "what if feedback loses" (Q30, Q31). The paper should keep all of these.
