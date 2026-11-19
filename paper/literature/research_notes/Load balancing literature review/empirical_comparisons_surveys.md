# Empirical comparisons and surveys of load balancing rules

## Which recent papers compare RR, WRR, least connections, response-time rules on testbeds

### Takeaway
Few indexed recent papers. 3 usable. All report means. Repetition weak or missing.

### Cited Findings
- Ma, Chi 2022, IEEE Access 10:14311-14324. Verified (Crossref + PDF). Downloaded: papers/2022_Ma_NginxLoadBalancingEval.pdf. Nginx WRR, IP_HASH, LEAST_CONN, NEW_HASH. JMeter 200 to 3000 threads, 5 min per step. Mean response time, failure rate, throughput. No percentiles. No repetitions stated for load tests. [IEEE](https://doi.org/10.1109/ACCESS.2022.3146422)
- Aslanpour et al. 2024, FGCS 154:266-280, CC BY. Verified. Downloaded: papers/2024_Aslanpour_ServerlessEdgeLB.pdf. Real Pi/Jetson cluster, K3s, OpenFaaS, Envoy. RR, random, profiled WRR, least-request. At least 3 runs, 10 min, mean + SE. p90 shown; p95/p99 said similar, not shown. [FGCS](https://doi.org/10.1016/j.future.2024.01.020)
- Faridah, Suranegara 2026, JAIC 10(1):900-909, CC BY-SA. Verified. Downloaded: papers/2026_Faridah_HomogeneousHeterogeneousLB.pdf. Proxmox VMs, 2 vCPU, RAM 2/4/6 GiB. Nginx + Nginx Plus. RR, IP hash, random (equal servers); least response time, LC, WLC (unequal servers). 5 runs, means only. Indonesian national journal, lower tier. [JAIC](https://doi.org/10.30871/jaic.v10i1.11614)

### Inferences
- Testbeds: small VM or SBC clusters. Workloads: web pages or ML inference. None slows one worker with a CPU quota.
- Statistics: means, sometimes SE. No significance tests seen.

### Gaps
- No indexed 2023-2026 paper found that compares all four of our rule types in one design.

## When dynamic or feedback rules win, and when not

### Takeaway
Dynamic wins with unequal nodes and heavy load. Static fine on equal nodes. Overhead rarely measured.

### Cited Findings
- Least-request beat static throughput-weighted RR, mostly at heavy load; static lost success rate (Figs. 14, 15). Authors warn least-request state may cost overhead at scale. [Aslanpour 2024](https://doi.org/10.1016/j.future.2024.01.020)
- WLC lowest latency at high load on unequal RAM servers. Throughput nearly equal for all rules (190.72 to 194.76 kb/sec at high load). [Faridah 2026](https://doi.org/10.30871/jaic.v10i1.11614)
- WRR and LEAST_CONN had higher failure rates than hash rules at high thread counts. LEAST_CONN throughput overtook IP_HASH as load grew. [Ma 2022](https://doi.org/10.1109/ACCESS.2022.3146422)

### Inferences
- Dynamic gains show at high load plus heterogeneity. Our slowed-worker scenario hits that case.
- Ma 2022: least connections not always better (web pages, equal servers).

### Gaps
- No paper here tests a latency-feedback rule like (unfinished + 1) x avg time against least connections.

## Common methodological weaknesses

### Takeaway
Means only, few runs, confounded designs, no overhead measured, heavy simulation use.

### Cited Findings
- Load tests shown as single curves, means only. [Ma 2022](https://doi.org/10.1109/ACCESS.2022.3146422)
- Static rules tested only on equal servers, dynamic only on unequal: confounded. Heterogeneity is RAM only. [Faridah 2026](https://doi.org/10.30871/jaic.v10i1.11614)
- Dispatcher overhead discussed, not measured. [Aslanpour 2024](https://doi.org/10.1016/j.future.2024.01.020)
- 51% of 63 reviewed studies used CloudSim. [Devi 2024](https://doi.org/10.1007/s10462-024-10925-w)
- Reviewed work mostly CloudSim / Cloud Analyst (Fig. 11). [Lohumi 2023](https://doi.org/10.1109/ACCESS.2023.3337146)

### Inferences
- Our project can address: every rule in every scenario, 5+ runs, p95, CPU slowdown, dispatcher CPU/RAM.

### Gaps
- Did not check variance reporting inside the surveys' source studies.

## Recent surveys for taxonomy

### Takeaway
Two usable: Lohumi 2023 (taxonomy), Devi 2024 (SLR, simulation share).

### Cited Findings
- Lohumi et al. 2023, IEEE Access 11:134517-134530. Taxonomy: static, dynamic, hybrid, nature-inspired. Verified. Downloaded: papers/2023_Lohumi_CloudLoadBalancingReview.pdf. [IEEE](https://doi.org/10.1109/ACCESS.2023.3337146)
- Devi et al. 2024, Artificial Intelligence Review 57:276. SLR of 63 papers, 2014-2024. Verified. Downloaded: papers/2024_Devi_SLRLoadBalancingScheduling.pdf. [Springer](https://doi.org/10.1007/s10462-024-10925-w)

### Inferences
- Both focus on VM/task scheduling, not proxy request rules. Background only.

### Gaps
- Rejected or not kept:
  - Experimental setup HAProxy RR vs LC, Sensors 2020, 10.3390/s20247342. Before 2021.
  - Nguyen et al. Sensors 2022, 10.3390/s22082869 (RAP, Kubernetes). Downloaded, dropped on budget cut, PDF deleted.
  - Gao et al. IEEE Access 2023, 10.1109/ACCESS.2023.3313643 (K-TAHP). Dropped on budget cut, PDF deleted.
  - Bhattacharya et al. ACM TAAS 2024, 10.1145/3676167 (BLOC). No free PDF found.
  - Michaelis et al. Middleware 2024 (L3). Covered by parallel researcher (papers/2024_Michaelis_L3_LatencyAware_MultiCluster_ServiceMesh.pdf). My duplicate deleted.
  - Ma'arifah, Sarmini, JOIV 2024, 10.62527/joiv.8.2.1985. PDF behind Cloudflare. Not read.
  - HAProxy "Load Balancer Tuning" arXiv 2212.14198. Preprint only.
  - Many Indonesian national-journal RR vs LC papers in Crossref. Low tier. Not read.
