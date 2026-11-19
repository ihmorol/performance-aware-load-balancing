# Scalable load balancing in the presence of heterogeneous servers

## Citation
Gardner, K., Abdul Jaleel, J., Wickeham, A., Doroudi, S. 2021. Scalable load balancing in the presence of heterogeneous servers. Performance Evaluation 145, 102151. https://doi.org/10.1016/j.peva.2020.102151 (verified on Crossref). Queueing theory, not a systems paper.

## Free PDF
Author's Amherst page: https://kgardner.people.amherst.edu/papers/gardner_peva20.pdf (journal layout, volume fields still "xxx", so likely the accepted proof). Local: `2021_Gardner_ScalableLB_HeterogeneousServers.pdf`

## Problem
Power-of-d and JIQ assume equal-speed servers and can behave badly with fast and slow servers.

## Method
Defines SED-d: query d servers, send to the one with smallest expected delay, queue length scaled by speed (Sec. 1, 5). Proposes JIQ-(dF, dS) and JSQ-(dF, dS). Exact analysis as server count grows, mostly exponential service.

## Setup
Analysis plus simulation; speed ratio r of 1.1 to 10, fast fraction 0.2 to 0.8 (Fig. 5).

## Key findings
At r = 1.1, JSQ-d and SED-d perform about the same. As r grows, JSQ-d suffers and SED-d corrects it. With few fast servers, both can look unstable; at qF = 0.2 only about 40% of jobs query a fast server (Sec. 5). SED needs known speeds and is not optimal in general (Sec. 2).

## Limitations stated
Exponential service, infinite-server limit, two speed classes, speed heterogeneity only.

## Relevance
Precise peer-reviewed definition of the rule family of our feedback rule; predicts SED near least connections when speeds match and better when one worker is slow.

## Gap
Speeds known and fixed; no online speed estimate from noisy processing times; no real jobs.
