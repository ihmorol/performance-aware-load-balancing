# Load balancing in compute clusters with delayed feedback

## Full citation
Anam Tahir, Bastian Alt, Amr Rizk, Heinz Koeppl. "Load balancing in compute clusters with delayed feedback." IEEE Transactions on Computers 72(6):1610-1622, 2023. https://doi.org/10.1109/TC.2022.3215907

## Free PDF
IEEE Xplore open access (CC BY 4.0): https://ieeexplore.ieee.org/stampPDF/getPDF.jsp?tp=&arnumber=9925099. Local file: papers/2023_Tahir_DelayedFeedback.pdf

## Problem
Dispatching to heterogeneous servers with finite buffers when the dispatcher only learns server state through randomly delayed job acknowledgements.

## Model and method
N parallel FIFO servers with finite buffers. The problem is a partially observable MDP. The proposed policy (POL) keeps a belief about queue states with a particle filter, plans with Monte Carlo tree search, and estimates unknown parameters at runtime (Sect. 3, 4).

## Key results
- POL beats limited-information baselines (Join-the-Most-Observations variants) and is comparable to full-information JSQ, JSQ(d) and SED in response time and job drops (abstract, Sect. 5).
- In a two-server case, POL gives priority to the faster server and sends jobs to the emptier or faster queue, close to JSQ and SED (Sect. 5, Fig. 3).
- POL has almost no job losses up to offered load 1 (Sect. 5, Fig. 8).

## Assumptions and limitations
Simulation only. Results depend on the computing resources given to the planner (Sect. 5). It may need estimates of arrival and service time densities (Sect. 4.4).

## Relevance to our project
Our dispatcher also sees worker state with delay (completion messages). Prediction: SED with delayed state should stay close to full-information SED; finite buffers make drops a key metric.

## Gap our project could touch
Real VMs, a simple estimator instead of tree search, and a CPU-quota slowdown.
