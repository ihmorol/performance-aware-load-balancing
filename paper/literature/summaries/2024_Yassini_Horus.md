# Horus: granular in-network task scheduler for cloud datacenters

## Citation
Yassini, P., Diab, K., Zangeneh, S., Hefeeda, M. 2024. Horus: Granular In-Network Task Scheduler for Cloud Datacenters. NSDI '24, USENIX. https://www.usenix.org/conference/nsdi24/presentation/yassini (verified on proceedings PDF; page range not recorded).

## Free PDF
USENIX open access: https://www.usenix.org/system/files/nsdi24-yassini.pdf. Local: `2024_Yassini_Horus.pdf`

## Problem
JSQ is ideal but needs fresh queue lengths; stale data causes herding onto the server last seen as least loaded (Sec. 2.1).

## Method
Switch schedulers send to an idle node if known; if all busy, pick the shorter of two sampled queues. Lazy updates: track drift per node and refresh only when drift could change a decision (Sec. 3.3).

## Setup
Tofino switch, seven servers, 32 or 48 workers; RocksDB GET (40 us) and SCAN (650 us) mixes, TPC-C model; Poisson arrivals; p99 metric (Sec. 4.1). Simulation of 27,648 servers.

## Key findings
Up to 75% lower tail response time and 1.9X throughput versus RackSched in one rack (Sec. 1). Rack scheduler plus uniform LB degrades past 50% load; ideal JSQ stays low near 90% (Fig. 2).

## Limitations stated
Failure handling and overhead analysis in appendix; multi-rack baselines are author-built extensions of RackSched.

## Relevance
Explains why stale load info hurts and how idle-first plus queue length handles it; informs our tie-break and idle probes, and the mixed-size scenario.

## Gap
Queue length only, no speed term; microsecond scale with special hardware; no slowed worker.
