# 2017 Abedi repeatable experiments in the cloud (foundational, older)

## Citation
A. Abedi, T. Brecht. "Conducting Repeatable Experiments in Highly Variable Cloud Computing Environments." Proceedings of the 8th ACM/SPEC International Conference on Performance Engineering (ICPE 2017), pp. 287-292. DOI: 10.1145/3030207.3030229 (checked on Crossref).

## Free PDF
https://research.spec.org/icpe_proceedings/2017/proceedings/p287.pdf (SPEC-hosted ICPE proceedings). Local: papers/2017_Abedi_RepeatableExperimentsCloud.pdf

## Problem
Common ways of running cloud experiments can show differences that are not real.

## Method
Replay Amazon EC2 CPU, memory, disk and network traces through four designs: single trial, multiple consecutive trials (MCT), multiple interleaved trials (MIT), and randomized multiple interleaved trials (RMIT).

## Key findings
- Abstract: common methods reported a 38% difference between two identical systems at 95% confidence.
- Of 38 SoCC'16 papers, single trial and MCT were the only methods seen in the 9 public cloud papers.
- MIT avoided non-overlapping CIs in most traces, but periodic changes in the environment still produced false differences (Figures 6 and 7).
- RMIT reorders the alternatives randomly in each round, a randomized block design.

## Limitations
Short paper, trace-based, sequential trials on one VM. Parallel runs on several VMs left for future work.

## Implications for us
Run the four rules in rounds and shuffle their order each round. Do not run all trials of one rule back to back. Keep the slow-worker choice fixed but record which VM it is.

## Gap
Not tested on a single desktop host with background processes.
