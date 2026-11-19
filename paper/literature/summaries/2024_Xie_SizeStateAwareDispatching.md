# Heavy-traffic optimal size- and state-aware dispatching

## Full citation
Runhan Xie, Isaac Grosof, Ziv Scully. "Heavy-traffic optimal size- and state-aware dispatching." Proceedings of the ACM on Measurement and Analysis of Computing Systems (POMACS) 8(1), Article 9, 36 pages, March 2024. https://doi.org/10.1145/3639035

## Free PDF
Published version on author's page: https://ziv.codes/pdf/sigmetrics2024-xie.pdf. Local file: papers/2024_Xie_SizeStateAwareDispatching.pdf

## Problem
Minimize mean response time when the dispatcher knows each job's size and the work left at each FCFS queue.

## Model and method
k identical FCFS servers, Poisson arrivals, general job sizes (Sect. 2). Proposes CARD: keep one queue short and send as few jobs as possible to one long queue. Proves an upper bound for CARD and a lower bound for any policy; they match in heavy traffic (abstract, Sect. 3 to 6). Simulation in Sect. 7.

## Key results
- CARD is heavy-traffic optimal and beats LWL and SITA in heavy traffic (abstract).
- Example at high load: over 75% lower mean delay than LWL and over 50% lower than SITA (Sect. 1, Fig. 1.2).
- SITA can sometimes be much worse than LWL (Sect. 1, citing Harchol-Balter et al.).

## Assumptions and limitations
Identical servers, exact sizes known, size distribution known to tune CARD. Bounds not tight away from heavy traffic.

## Relevance to our project
Mixed image sizes: when small jobs wait behind large ones, mean delay rises. Our rules ignore job size, so this marks a ceiling we do not reach.

## Gap our project could touch
Heterogeneous speeds, unknown sizes, moderate load, p95.
