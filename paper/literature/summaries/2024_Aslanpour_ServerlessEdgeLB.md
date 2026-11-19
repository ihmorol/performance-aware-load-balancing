# Aslanpour et al. 2024, heterogeneous serverless edge load balancing

## Citation
Mohammad Sadegh Aslanpour, Adel N. Toosi, Muhammad Aamir Cheema, Mohan Baruwal Chhetri, Mohsen Amini Salehi. "Load balancing for heterogeneous serverless edge computing: A performance-driven and empirical approach." Future Generation Computer Systems, vol. 154, pp. 266-280, 2024. DOI: 10.1016/j.future.2024.01.020 (CC BY 4.0)

## Source
Published version mirrored at https://digital.library.unt.edu/ark:/67531/metadc2376492/m2/1/high_res_d/1-s2.0-S0167739X24000207-main.pdf. Local file: papers/2024_Aslanpour_ServerlessEdgeLB.pdf

## Problem
Edge nodes differ in hardware, so equal-weight balancing wastes the fast nodes.

## Method and testbed
Real cluster of Raspberry Pi 3/4 (some with TPU) and a Jetson Nano, K3s plus OpenFaaS, Envoy as balancer. Object detection functions. Nodes are profiled first, then weights are set from the profiles (Section 6.2.1).

## Algorithms compared
Round-robin (baseline), random, profile-weighted round-robin (single and multi-objective), and Envoy least-request (Section 6.2.5).

## Metrics and runs
Throughput, latency, success rate, energy, cost, precision. Each rate run at least 3 times, 10 minutes each; mean and standard error reported (Section 6.1). Tail latency at p90 shown; p95 and p99 "not reported" because they behaved the same.

## Key findings
Least-request beat the static throughput-weighted round-robin, mainly under heavy load where the static rule lost success rate (Figs. 14 and 15).

## Limitations
Stated: least-request keeps per-endpoint state that may cost overhead at scale; it focuses on throughput only. Observed: overhead not measured; no significance tests.

## Relevance
Closest match to our design: profiled fixed weights versus a dynamic rule on unequal nodes.

## Gap our project could touch
Measure dispatcher overhead; add a latency-based feedback rule; report p95.
