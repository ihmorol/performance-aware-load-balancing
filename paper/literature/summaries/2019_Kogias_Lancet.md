# 2019 Kogias Lancet (foundational, older)

## Citation
M. Kogias, S. Mallon, E. Bugnion. "Lancet: A self-correcting Latency Measuring Tool." 2019 USENIX Annual Technical Conference (ATC 19), Renton, WA, July 2019. Proceedings page: https://www.usenix.org/conference/atc19/presentation/kogias-lancet

## Free PDF
https://www.usenix.org/system/files/atc19-kogias-lancet.pdf. Local: papers/2019_Kogias_Lancet.pdf

## Problem
Tail latency is easy to mismeasure because of the workload setup, the client machines, or the server itself.

## Method
A tool that runs statistical checks during the run and refuses to report a tail value it cannot trust.

## Key findings
- Background section: open-loop clients send at a set rate and inter-arrival distribution (for example Poisson). Closed-loop clients cap the number of outstanding requests, so their tail is bounded by that cap.
- Figure 1: with 144 connections, Mutilate acted closed-loop and could not reach the target rate.
- Methodology: first check the target load is reached; check sent gaps match the planned distribution (Anderson-Darling); check samples are independent (Spearman autocorrelation); check stationarity (Augmented Dickey-Fuller), adding 10,000 samples if not.
- Confidence intervals on non-independent samples underestimate their size.
- Evaluation: above 70% load, the 99th percentile CI target could not be met.

## Limitations
Built for microsecond RPCs with special NICs. Our requests are much slower.

## Implications for us
Use an open-loop schedule, log planned vs actual send times and achieved rate, discard warmup, and check that samples close in time are not strongly correlated before computing CIs.

## Gap
No checks for a Python generator on a busy desktop host.
