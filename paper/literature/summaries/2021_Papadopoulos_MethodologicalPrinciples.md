# 2021 Papadopoulos methodological principles

## Citation
A. V. Papadopoulos, L. Versluis, A. Bauer, N. Herbst, J. von Kistowski, A. Ali-Eldin, C. L. Abad, J. N. Amaral, P. Tuma, A. Iosup. "Methodological Principles for Reproducible Performance Evaluation in Cloud Computing." IEEE Transactions on Software Engineering 47(8):1528-1543, 2021. DOI: 10.1109/TSE.2019.2927908 (checked on Crossref).

## Free PDF
https://www.es.mdu.se/pdf_publications/5558.pdf (Malardalen University repository, IEEE-formatted author version). Local: papers/2021_Papadopoulos_MethodologicalPrinciples.pdf

## Problem
Cloud performance results are hard to repeat, and many papers do not say how they measured.

## Method
The authors propose eight principles, apply them to a SPEC Cloud IaaS use case, and survey cloud papers from 2012 to 2017 (Section 4).

## Key findings
- P1: decide how many repetitions to run and quantify the confidence in the result. The survey found repetition counts often unjustified or not reported.
- P2: cover workload and configuration space, possibly randomized.
- P3, P4: describe the setup fully and release code, data, and scripts.
- P5: report the distribution, not only an average. Averages only make sense when data cluster around a central value.
- P6: give a statistical test when comparing approaches. P7: units. P8: cost.
- Abstract: few surveyed studies follow the principles.

## Limitations
No fixed repetition number is given. The survey covers papers up to 2017.

## Implications for us
Justify 5 runs per condition, report spread and CIs, use a nonparametric test between rules, list VM and host versions, and publish scripts and raw data.

## Gap
Principles target public clouds. A single shared host with a deliberate CPU quota is not covered.
