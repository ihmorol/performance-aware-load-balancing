# Experiment methodology

Scope cut by coordinator to 4 papers. Terse notes. Summaries in paper/literature/summaries/.

Papers kept:
- P1. Papadopoulos et al., "Methodological Principles for Reproducible Performance Evaluation in Cloud Computing", IEEE TSE 47(8):1528-1543, 2021, doi 10.1109/TSE.2019.2927908. Verified (Crossref). Downloaded (MDU repo author version, IEEE format): papers/2021_Papadopoulos_MethodologicalPrinciples.pdf
- P2. Kogias, Mallon, Bugnion, "Lancet: A self-correcting Latency Measuring Tool", USENIX ATC 2019. Verified (USENIX page). Downloaded: papers/2019_Kogias_Lancet.pdf. Foundational, older.
- P3. Abedi, Brecht, "Conducting Repeatable Experiments in Highly Variable Cloud Computing Environments", ICPE 2017, pp. 287-292, doi 10.1145/3030207.3030229. Verified (Crossref). Downloaded (SPEC-hosted proceedings): papers/2017_Abedi_RepeatableExperimentsCloud.pdf. Foundational, older.
- P4. Ugedal, Kumar, "Mitigating Unnecessary Throttling in Linux CFS Bandwidth Control", IEEE SBAC-PAD 2022, pp. 336-345, doi 10.1109/SBAC-PAD55451.2022.00044. Verified (Crossref, SBC page). Not downloaded; abstract only; author copy at https://hdl.handle.net/11250/3055366

## Reproducible cloud performance experiments

### Takeaway
Repeat runs, justify the count, report the distribution with confidence, test differences statistically, interleave and shuffle run order.

### Cited Findings
- P1 principle: decide repetitions after finding variability sources, quantify confidence. Source: [Papadopoulos 2021](https://www.es.mdu.se/pdf_publications/5558.pdf)
- Survey: repetition counts often not justified, sometimes not reported. Source: [Papadopoulos 2021](https://www.es.mdu.se/pdf_publications/5558.pdf)
- P5: report distribution, not only mean; mean only fits data clustered around center. P6: statistical test when comparing. Source: [Papadopoulos 2021](https://www.es.mdu.se/pdf_publications/5558.pdf)
- Few surveyed studies (2012-2017) follow the eight principles. Source: [Papadopoulos 2021](https://www.es.mdu.se/pdf_publications/5558.pdf)
- Single trial / consecutive trials falsely showed 38% gap between identical systems at 95% confidence. Source: [Abedi 2017](https://research.spec.org/icpe_proceedings/2017/proceedings/p287.pdf)
- RMIT: random order of alternatives each round (randomized block design); periodic noise still hurt plain interleaving. Source: [Abedi 2017](https://research.spec.org/icpe_proceedings/2017/proceedings/p287.pdf)

### Inferences
- 5 runs ok only if justified; show per-run p95 + CI or bootstrap interval; nonparametric test between rules.
- Run rules in rounds, shuffle order per round. Not all runs of one rule back to back.
- Publish scripts, configs, raw CSVs.

### Gaps
- No fixed minimum repetition count in these papers.
- Verified but not used: Henning et al., "When Should I Run My Application Benchmark?", FSE Companion 2025, doi 10.1145/3696630.3728563 (verified Crossref, CC BY on ACM). ACM site blocks scripted download behind a bot check; not read. Team can download by hand. arXiv copy not used.
- Rejected: "Should I Run My Cloud Benchmark on Black Friday?" (arXiv only). Uta et al. NSDI 2020 and Maricq et al. OSDI 2018 (older; quota of 2 older items used). SPEC RG 2019 tech report (replaced by journal version).

## Tail latency and load generation pitfalls

### Takeaway
Closed-loop clients hide tail latency; check achieved rate and send gaps, warmup, sample independence before trusting percentiles.

### Cited Findings
- Open loop: rate + inter-arrival distribution (e.g., Poisson). Closed loop caps outstanding requests, tail bounded by cap. Source: [Lancet 2019](https://www.usenix.org/system/files/atc19-kogias-lancet.pdf)
- Mutilate with 144 connections acted closed-loop, could not reach target rate (Fig. 1). Source: [Lancet 2019](https://www.usenix.org/system/files/atc19-kogias-lancet.pdf)
- Checks: target load reached; send gaps match planned distribution (Anderson-Darling); iid via Spearman autocorrelation; stationarity via ADF, +10,000 samples if not. Source: [Lancet 2019](https://www.usenix.org/system/files/atc19-kogias-lancet.pdf)
- CIs on non-iid samples underestimate size. Source: [Lancet 2019](https://www.usenix.org/system/files/atc19-kogias-lancet.pdf)
- Above 70% load, 99th percentile CI target not met. Source: [Lancet 2019](https://www.usenix.org/system/files/atc19-kogias-lancet.pdf)

### Inferences
- Use open-loop schedule from host; time each request from its planned send time (avoids coordinated omission).
- Log planned vs actual send time, achieved rate, failures. Flag runs that miss rate.
- Drop warmup window. Compute CIs across runs, not across correlated requests inside one run.
- Check generator host CPU stays well below saturation.

### Gaps
- No recent (2023+) peer-reviewed, free, non-arXiv paper on coordinated omission found.
- Rejected: Antoniou et al., "Taming Performance Variability caused by Client-Side Hardware Configuration", IISWC 2024, doi 10.1109/IISWC63097.2024.00018 (verified). Only free copy is arXiv. Treadmill ISCA 2016, TailBench IISWC 2016 (older). Tene "How NOT to Measure Latency" (talk, not peer-reviewed).

## CPU quota throttling and noisy neighbors

### Takeaway
CFS bandwidth control can throttle more than intended and adds overhead; quota slowdown is bursty, not a smooth slower CPU.

### Cited Findings
- Runtime accounting in bandwidth control causes unnecessary throttling; overhead can be high; fixes removed nearly all of it, up to 12% gain, overhead cut up to 24x (abstract). Source: [Ugedal 2022](https://doi.org/10.1109/SBAC-PAD55451.2022.00044)
- Kernel doc: quota per period; smaller period gives more consistent latency, less burst. Source: [kernel.org sched-bwc](https://docs.kernel.org/scheduler/sched-bwc.html)

### Inferences
- Record quota, period, kernel version, cgroup version per run; read cpu.stat throttle counters before/after.
- Keep period fixed across all runs; state it in the paper.
- Host noise: close other apps, pin or note VM vCPU placement, log host CPU; shuffle order handles slow drift.

### Gaps
- Ugedal full text not read; setup details unknown.
- No peer-reviewed free paper found tying fixed CFS quota to p95 of a web service; blogs only (not used).
- Rejected: Lin et al., "Performance Interference of Virtual Machines: A Survey", ACM CSUR 55(12), 2023, doi 10.1145/3573009 (verified). Not downloadable by script (ACM bot check), not read.
- Rejected: ThrottleBot (arXiv only).
