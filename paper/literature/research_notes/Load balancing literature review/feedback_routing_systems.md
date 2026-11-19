# Feedback-based request routing in real systems

## Which recent papers build on or evaluate latency or queue-aware routing?

### Takeaway
5 kept. L3 (Middleware 2024) is closest to our feedback rule. ServiceRouter and Horus cover stale load info. Hermod covers rule comparison on variable-size CPU work. Gardner gives SED-d.

### Cited Findings
- L3: weight = 1/((in-flight+1)^2 x latency est.), EWMA/PeakEWMA, 5 s Prometheus; p99 -26% vs RR, -22% vs C3 on DeathStarBench. Verified, CC BY, downloaded. Source: [L3, Middleware '24](https://doi.org/10.1145/3652892.3654793)
- ServiceRouter: Pick-2 on outstanding requests (77% of RPCs), CPU (18%); piggyback + cached load, poll if cheap, else random (50/25/25%). Verified, downloaded. Source: [ServiceRouter, OSDI '23](https://www.usenix.org/conference/osdi23/presentation/saokar)
- Horus: idle-first, else power-of-two; lazy drift-based updates against herding; up to 75% lower tail vs RackSched. Verified, downloaded. Source: [Horus, NSDI '24](https://www.usenix.org/conference/nsdi24/presentation/yassini)
- Hermod: least-loaded needed at high load with variable run times; equal scheduler overhead checked. Verified, downloaded (author page). Source: [Hermod, SoCC '22](https://doi.org/10.1145/3542929.3563468)
- Gardner: SED-d = queue length scaled by speed; close to JSQ-d at equal speeds, better as gap grows; can look unstable with few fast servers. Verified, downloaded (author page, likely accepted proof). Source: [Gardner et al., PEVA 2021](https://doi.org/10.1016/j.peva.2020.102151)

### Inferences
- Signals in use: in-flight/outstanding (all), latency EWMA (L3), CPU (SR option), queue length (Horus).
- Stale info fixes: floor weight (L3), piggyback + selective poll (SR), drift threshold (Horus). Our idle probe fits this group.

### Gaps
- No recent systems paper found that compares RR, WRR, least connections and SED on CPU-bound variable-size jobs with one slowed node.

## Does any recent paper evaluate (outstanding+1) x average latency?

### Takeaway
No exact match found. Our rule is SED with speed estimated online.

### Cited Findings
- Nearest: L3 uses (n+1)^2 x p99-based estimate, as a weight, not argmin. Source: [L3](https://doi.org/10.1145/3652892.3654793)
- SED-d defined with known speeds. Source: [Gardner et al.](https://doi.org/10.1016/j.peva.2020.102151)
- Peak EWMA as latency x (pending+1) is in Finagle/Linkerd docs and blog (2016), not peer-reviewed. Source: [Linkerd blog](https://linkerd.io/2016/03/16/beyond-round-robin-load-balancing-for-latency/)

### Inferences
- Name it "shortest expected delay (SED) with measured service time"; cite Gardner for SED, L3 for the systems form.

### Gaps
- Exact rule not found in 2021-2026 peer-reviewed systems work within this search budget.

## Limitations and gaps our project could touch

### Takeaway
Small scale, CPU-heavy work, per-request choice, fair baselines, overhead accounting are open.

### Cited Findings
- L3: emulated delays, 5 s freshness, no LC/WRR baseline, C3 adapted. Source: [L3](https://doi.org/10.1145/3652892.3654793)
- SR: no tail comparison across rules, no slow-node study. Source: [ServiceRouter](https://www.usenix.org/conference/osdi23/presentation/saokar)
- Horus: queue length only, equal-speed workers per setup. Source: [Horus](https://www.usenix.org/conference/nsdi24/presentation/yassini)
- Hermod: equal-speed workers, processor sharing. Source: [Hermod](https://doi.org/10.1145/3542929.3563468)
- Gardner: known speeds, exponential service, theory only. Source: [Gardner et al.](https://doi.org/10.1016/j.peva.2020.102151)

### Inferences
- Our test: LC vs SED on a slowed worker, p95, mixed sizes, two-node full view.

### Gaps
- Rejected / not kept:
  - Prequal NSDI '24: already a current reference.
  - Sujarwo et al. 2023, ELKOMIKA 11(2) 439-450, doi 10.26760/elkomika.v11i2.439: SED vs least connection in kube-proxy; small venue, abstract and body numbers disagree (214.257 vs 241.36 ms), no tail metrics; dropped for 5-paper cap. Read in full.
  - Aslanpour et al. 2024, FGCS 154:266-280, doi 10.1016/j.future.2024.01.020: response-time weights, heterogeneous edge; OA copy on Monash returned 403, not read, so not kept.
  - Dodoor (arXiv 2510.12889), GORGO (arXiv 2602.11688), Tower of Two Choices (arXiv 2302.04399): arXiv only.
  - Linkerd 2016 blog, Alibaba ASM docs, HAProxy peak-EWMA GitHub: not peer-reviewed.
  - Edge multi-replica traffic allocation, Springer chapter 2024: venue and access not confirmed.
  - MDPI Eng. Proc. 2025 RR/WRR/ML study: not checked in full; low relevance.
