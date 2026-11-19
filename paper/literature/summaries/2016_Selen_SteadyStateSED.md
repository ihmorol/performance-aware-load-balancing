# Steady-state analysis of shortest expected delay routing (foundational, older)

## Full citation
Jori Selen, Ivo Adan, Stella Kapodistria, Johan van Leeuwaarden. "Steady-state analysis of shortest expected delay routing." Queueing Systems 84(3-4):309-354, 2016. https://doi.org/10.1007/s11134-016-9497-7

## Free PDF
Springer open access (CC BY 4.0): https://link.springer.com/content/pdf/10.1007/s11134-016-9497-7.pdf. Local file: papers/2016_Selen_SteadyStateSED.pdf

## Problem
Exact queue-length distribution for two servers with different speeds when each job joins the queue with the shortest expected delay (SED).

## Model and method
Two exponential FCFS servers, rates 1 and s, each with its own queue, Poisson arrivals. The state is a random walk in the quadrant, solved with the compensation approach as a series of product forms (abstract, Sect. 3).

## Key results
- The stationary distribution is a series of product forms that can be computed numerically (abstract, Sect. 4).
- Intro (p. 310-311): with equal rates SED is JSQ. With unequal rates JSQ is not optimal. SED is also not exactly optimal; citing earlier work, it does well at low and high load but slightly worse than other policies at medium load, and it is heavy-traffic optimal (Foschini).
- Numerically, queue lengths stay between the line of equal expected delay and the line of equal expected waiting time (Sect. 4, s = 3).

## Assumptions and limitations
Exponential service, known rates, unbounded queues, no information delay. No job-size variability.

## Relevance to our project
Closest exact model to our feedback rule with two workers. Prediction: SED should beat JSQ (least unfinished) when speeds differ, but the gap at medium load may be small.

## Gap our project could touch
Bounded queues, non-exponential image sizes, and rates estimated online rather than known.
