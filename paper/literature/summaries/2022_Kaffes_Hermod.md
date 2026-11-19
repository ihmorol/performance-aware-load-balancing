# Hermod: principled and practical scheduling for serverless functions

## Citation
Kaffes, K., Yadwadkar, N. J., Kozyrakis, C. 2022. Hermod: Principled and Practical Scheduling for Serverless Functions. SoCC '22, ACM, pp. 289-305. https://doi.org/10.1145/3542929.3563468 (verified on Crossref). Older than 2023 but within range.

## Free PDF
Author's Columbia page, SoCC layout: https://www.cs.columbia.edu/~kkaffes/papers/hermod-socc22.pdf. Local: `2022_Kaffes_Hermod.pdf`. ACM open access status not checked.

## Problem
Serverless jobs have highly variable run times; common choices (late binding, random or locality balancing) may not fit.

## Method
Simulate a taxonomy of policies (Sec. 3), then build Hermod on OpenWhisk: early binding, processor sharing per worker, consolidation at low load, least-loaded at high load.

## Setup
Nine Xeon E5-2630 machines, 96 invoker cores, one-hour runs, CPU busy-spin functions with log-normal times (Sec. 6.1). Baselines: OpenWhisk, oracle late binding, least-loaded.

## Key findings
Up to 85% lower slowdown and 60% higher load than existing schedulers (Sec. 7). Random and locality balancing fail at high load; least-loaded is needed (Sec. 1). All schedulers reach about 3,818 to 3,834 RPS max, so overhead is equal (Sec. 6.6).

## Limitations stated
Simulator ignores container start-up; no real CPU/IO mix; cold starts keep p99 slowdown at 20 to 30.

## Relevance
Shows load-aware rules matter most with high size variance and high load; models equal-overhead checks for fair baselines.

## Gap
Equal-speed workers, processor sharing, no latency-weighted rule.
