# L3: latency-aware load balancing in multi-cluster service mesh

## Citation
Michaelis, O., Schmid, S., Mostafaei, H. 2024. L3: Latency-aware Load Balancing in Multi-Cluster Service Mesh. Middleware '24, ACM, pp. 49-61. https://doi.org/10.1145/3652892.3654793 (verified on TU/e portal and Crossref).

## Free PDF
Publisher's version, CC BY, TU/e portal: https://research.tue.nl/p/file/document/348853970/3652892.3654793.pdf. Local: `2024_Michaelis_L3_LatencyAware_MultiCluster_ServiceMesh.pdf`

## Problem
Service mesh round-robin ignores changing latency and failures of replicas spread over clusters.

## Method
Every 5 s, read p99 latency, success rate, RPS and in-flight requests from Prometheus; smooth with EWMA or PeakEWMA. Weight = 1 / ((n + 1)^2 x l), n = in-flight normalized by RPS, l = p99 plus a failure penalty (Eq. 3-4, Sec. 3.1). A floor weight keeps slow backends sending metrics.

## Setup
Three AWS EKS clusters, m6.xlarge nodes; DeathStarBench at 200 RPS and replayed production latency traces with artificial delays (Sec. 5.1). Baselines: round-robin, adapted C3.

## Key findings
DeathStarBench p99: 93.0 ms round-robin, 88.3 ms C3, 68.8 ms L3 (Sec. 5.3.1). Trace scenarios: 9% to 35% lower p99 than round-robin (Fig. 10). EWMA beat PeakEWMA by 2.3% (Sec. 5.2.2). L3 used under 1.5% of a vCPU (Sec. 4).

## Limitations stated
5 s metric freshness; no server capacity awareness; very slow replicas left to health checks; static penalty factor; C3 adapted, not original.

## Relevance
Closest recent paper to our feedback rule: same (in-flight + 1) x latency structure, plus a fix for stale estimates.

## Gap
No least connections or weighted round-robin baseline; delays are emulated, not CPU work; decisions are aggregate every 5 s, not per request.
