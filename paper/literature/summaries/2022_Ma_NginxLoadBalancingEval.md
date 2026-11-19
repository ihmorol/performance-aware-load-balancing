# Ma and Chi 2022, Nginx load balancing evaluation

## Citation
Chen Ma and Yuhong Chi. "Evaluation Test and Improvement of Load Balancing Algorithms of Nginx." IEEE Access, vol. 10, pp. 14311-14324, 2022. DOI: 10.1109/ACCESS.2022.3146422

## Source
https://ieeexplore.ieee.org/document/9693940 (open access). Local file: papers/2022_Ma_NginxLoadBalancingEval.pdf

## Problem
Nginx IP_HASH has hash collisions and slow node lookup. The authors test the built-in Nginx rules and propose NEW_HASH.

## Method and testbed
Nginx plus Keepalived in front of Tomcat servers (hardware in Table 4). Apache JMeter raised concurrent threads from 200 to 3000 in steps of 200, 5 minutes per step (Section V-A).

## Algorithms compared
WRR, IP_HASH, LEAST_CONN, NEW_HASH.

## Metrics and runs
Average response time, failure rate, throughput (equations 9 to 12). No percentiles. The load tests show one curve per rule with no stated repetitions or error bars. Only the hash-collision test was repeated 5 times (Section V-D).

## Key findings
At high thread counts WRR and LEAST_CONN had much higher failure rates than the hash rules (Fig. 14). WRR had the lowest throughput of the three native rules; LEAST_CONN overtook IP_HASH as threads grew (Fig. 15). NEW_HASH throughput was unstable between 2000 and 2600 threads.

## Limitations
Stated: NEW_HASH adds memory overhead and is not stable under heavy load. Observed: averages only; no repetitions or variance for load tests; workload not CPU-heavy; server heterogeneity not varied; authors explain failures by lookup cost without measuring it.

## Relevance
Shows a common pattern: Nginx rules compared on means from single runs.

## Gap our project could touch
Repeated runs, p95, a CPU-bound workload, and a slowed worker.
