# Faridah and Suranegara 2026, load balancing on homogeneous and heterogeneous servers

## Citation
Tsabitah Avia Aulia Faridah and Galura Muhammad Suranegara. "Performance of Load Balancing Algorithms on Homogeneous and Heterogeneous Servers in On-Premise Environments." Journal of Applied Informatics and Computing (JAIC), vol. 10, no. 1, pp. 900-909, 2026. DOI: 10.30871/jaic.v10i1.11614 (CC BY-SA 4.0). Paper body is in Indonesian.

## Source
https://jurnal.polibatam.ac.id/index.php/JAIC/article/download/11614/3417. Local file: papers/2026_Faridah_HomogeneousHeterogeneousLB.pdf

## Problem
Which Nginx rules suit equal versus unequal on-premise servers.

## Method and testbed
Proxmox VMs, Ubuntu 22.04, 2 vCPU each. Three equal backends (2 GiB RAM) and three unequal ones (2, 4, 6 GiB RAM). Nginx and Nginx Plus, JMeter at low, medium, high load, Netdata for CPU and memory (Table I).

## Algorithms compared
Homogeneous: round-robin, IP hash, random. Heterogeneous: least response time, least connection, weighted least connection.

## Metrics and runs
Throughput, average latency, error rate, load distribution, CPU, memory. Five repetitions per scenario, means reported (Tables III and IV). No percentiles, no variance.

## Key findings
Throughput was about the same for every rule at each load (6.78 to 6.86, 64.50 to 65.49, 190.72 to 194.76 kb/sec). Weighted least connection gave the lowest latency at high load in the heterogeneous set.

## Limitations
Stated: small scale, six VMs. Observed: static rules were tested only on equal servers and dynamic rules only on unequal ones, so the comparison is confounded; heterogeneity is RAM only while CPU stays equal; national journal.

## Relevance
Same VM scale and rule families as ours.

## Gap our project could touch
Run every rule in every scenario, slow CPU not RAM, add p95.
