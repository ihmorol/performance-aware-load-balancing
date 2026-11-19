# ServiceRouter: hyperscale and minimal cost service mesh at Meta

## Citation
Saokar, H., Demetriou, S., Magerko, N., Kontorovich, M., Kirstein, J., Leibold, M., Skarlatos, D., Khandelwal, H., Tang, C. 2023. ServiceRouter: Hyperscale and Minimal Cost Service Mesh at Meta. OSDI '23, USENIX, pp. 969-985. https://www.usenix.org/conference/osdi23/presentation/saokar (verified on proceedings PDF).

## Free PDF
USENIX open access: https://www.usenix.org/system/files/osdi23-saokar.pdf. Local: `2023_Saokar_ServiceRouter.pdf`

## Problem
Route RPCs across Meta's regions at low cost while keeping latency low and load even.

## Method
Client library does power-of-two (Pick-2) on a load metric. Default metric is outstanding requests (77% of RPCs); CPU is used by 18% (Sec. 3.4.3). Load is piggybacked on responses and cached; if stale, poll only when RTT is small versus processing time; else pick at random.

## Setup
Meta production; 15 services for in-region balance (Sec. 4.3.1).

## Key findings
Cached, polled, and random paths serve about 50%, 25%, 25% of requests (Sec. 3.4.3). Load CV median 0.18 at C50, 0.6 at C95 (Sec. 4.3.1). Sidecar proxy used 273% extra CPU versus 80% for the library in a worst case (Sec. 4.2.1).

## Limitations stated
Locality rings lack a global view; stale routing info is unavoidable; space limits scope.

## Relevance
Production evidence for outstanding requests as the default signal (our least connections rule) and a measured design for stale load info (our idle probes).

## Gap
No tail latency comparison of rules; no latency-weighted rule; no single degraded server.
