# A general "power-of-d" dispatching framework for heterogeneous systems

## Full citation
Jazeem Abdul Jaleel, Sherwin Doroudi, Kristen Gardner, Alexander Wickeham. "A general 'power-of-d' dispatching framework for heterogeneous systems." Queueing Systems 102(3-4):431-480, 2022. https://doi.org/10.1007/s11134-022-09736-z

## Free PDF
Published version on co-author's Amherst College page: https://kgardner.people.amherst.edu/papers/gardner_questa_22a.pdf. Local file: papers/2022_AbdulJaleel_GeneralPowerOfD.pdf

## Problem
How a dispatcher that samples d servers should use server speed information when servers are heterogeneous.

## Model and method
Many servers in speed classes, exponential job sizes, mean field analysis. A policy is split into a querying rule (which d servers to ask) and an assignment rule (which of them gets the job). Tractable analysis covers assignment rules that use only idle/busy status; SED-style rules are tested by simulation (Sect. 1, 6, 7).

## Key results
- Speed-unaware JSQ-d can perform quite poorly with heterogeneous servers (Sect. 1, citing earlier work).
- SED-d and Balanced Routing beat JSQ-d, but leave room for improvement (Sect. 1).
- Heuristic policies that pair SED-like assignment with an optimized querying rule do well in simulation (Sect. 7).
- At light load the querying choice matters most; at heavy load the assignment choice matters most (Sect. 1).

## Assumptions and limitations
Large-system limit, exponential sizes in the main text, known speeds, fresh state at query time.

## Relevance to our project
Supports comparing speed-aware (weighted round-robin, feedback) against speed-unaware rules (round-robin, least unfinished). Prediction: speed awareness should matter more as load rises, in the assignment step.

## Gap our project could touch
Two servers only, measured rather than known speeds, real overhead.
