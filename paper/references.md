# References

Every paper considered for the term paper, with the claim each one supports. A reference that supports no claim in the final paper gets cut, per the conventions in [README.md](README.md). The course asks for at least 8.

There are two groups. Group A is the reference list Emon Morol compiled on 2026-11-12 and 2026-11-13. It holds the six references on frozen slide 9 and six more. Each bibliographic entry in group A was checked against the publisher record (USENIX, Crossref, OpenAlex, or the journal page) on 2026-11-12. Where a PDF is a preprint or a company technical report rather than the publisher copy, the entry says so. Group B is the 2016 to 2026 literature from the gap analysis of 2026-11-19, which `paper/revised-proposal.md` adds to the frozen six. Its full citations and access notes are in [literature/gap-analysis.md](literature/gap-analysis.md) and the files in [literature/summaries/](literature/summaries/), and they are not repeated here.

All PDFs are in [literature/papers/](literature/papers/).

The claims below follow the revised proposal. Our feedback rule is the SED-style rule (unfinished + 1) × recent average processing time. Prequal motivates the signals it uses but is not the source of the formula, and the slowed worker has a fixed CPU quota for the whole run.

## Group A: frozen slide 9 references and the 2026-11-12 list

### 1. Load is not what you should balance: Introducing Prequal (frozen)

- Bartek Wydrowski, Robert Kleinberg, Stephen M. Rumble, Aaron Archer (Google)
- NSDI '24: 21st USENIX Symposium on Networked Systems Design and Implementation, pages 1285-1299, 2024
- https://www.usenix.org/conference/nsdi24/presentation/wydrowski, arXiv:2312.10172
- PDF: [2024_Wydrowski_Prequal.pdf](literature/papers/2024_Wydrowski_Prequal.pdf) (USENIX open access)

Claims it supports:

- Requests differ in the work they need and server speed varies, so balancing request counts or CPU load alone can leave one worker with a long queue. This motivates the whole comparison.
- Requests in flight and latency are better routing signals than CPU load. Our feedback rule uses the same two kinds of signal. Prequal itself probes a few servers and picks with a hot-cold lexicographic rule (gap analysis, spot check of the PDF), so we cite it as motivation and do not claim to reproduce it.
- Section 2 describes Google's weighted round-robin with weights recomputed from recent queries per second and CPU use. Our weights are fixed per scenario, so this is one sentence of context in the paper.

### 2. Join-Idle-Queue: A novel load balancing algorithm for dynamically scalable web services (frozen)

- Yi Lu, Qiaomin Xie, Gabriel Kliot, Alan Geller, James R. Larus, Albert Greenberg
- Performance Evaluation, volume 68, number 11, pages 1056-1071, 2011
- DOI 10.1016/j.peva.2011.07.015 (Elsevier)
- PDF: [2011_Lu_JoinIdleQueue.pdf](literature/papers/2011_Lu_JoinIdleQueue.pdf) (Microsoft Research report copy of the same paper)

Claims it supports:

- Separating the dispatcher from the workers, and deciding what information each side holds, is a real design choice. Our testbed has the same dispatcher plus workers shape.
- Queue information held by a dispatcher can be stale when it is used. Our dispatcher counts unfinished requests itself, so its counts are current, but its processing time estimate is a recent average and can lag a worker's real speed.
- Load balancing should be evaluated with mixed job sizes and unequal service rates, not only uniform work. Our scenarios 2 and 3 do this at small scale.

### 3. The Tail at Scale (frozen)

- Jeffrey Dean, Luiz André Barroso (Google)
- Communications of the ACM, volume 56, number 2, pages 74-80, 2013
- DOI 10.1145/2408776.2408794 (ACM)
- PDF: [2013_Dean_TailAtScale.pdf](literature/papers/2013_Dean_TailAtScale.pdf) (author copy from barroso.org)

Claims it supports:

- Users feel the tail, so we report p95 next to the mean.
- Unequal components and interference create long tails even at moderate load. Scenario 3, with one CPU-quota-limited worker, is a small controlled case of this.
- We report the spread across five runs for the same reason.

### 4. Sparrow: Distributed, Low Latency Scheduling (frozen)

- Kay Ousterhout, Patrick Wendell, Matei Zaharia, Ion Stoica (UC Berkeley)
- SOSP '13: 24th ACM Symposium on Operating Systems Principles, pages 69-84, 2013
- DOI 10.1145/2517349.2522716 (ACM)
- PDF: [2013_Ousterhout_Sparrow.pdf](literature/papers/2013_Ousterhout_Sparrow.pdf)

Claims it supports:

- At millisecond scales, delay in spreading scheduler state matters, and stale state hurts placement. Background for the feedback rule's estimate, which is always somewhat old.
- Sampling-based placement (batch sampling, late binding) sits between blind and fully informed routing. Background section only.

### 5. Maglev: A Fast and Reliable Software Network Load Balancer (frozen)

- Daniel E. Eisenbud, Cheng Yi, Carlo Contavalli, Cody Smith, Roman Kononov, Eric Mann-Hielscher, Ardas Cilingiroglu, Bin Ye, Yaojun Cai, Andrew Shakhayev (Google)
- NSDI '16: 13th USENIX Symposium on Networked Systems Design and Implementation, 2016
- https://www.usenix.org/conference/nsdi16/technical-sessions/presentation/eisenbud
- PDF: [2016_Eisenbud_Maglev.pdf](literature/papers/2016_Eisenbud_Maglev.pdf) (USENIX/Google copy)

Claims it supports:

- Production load balancers spread packets and connections at the network level before any application-level rule sees a request. Used in the background section to place dispatcher-level routing.

### 6. An Updated Performance Comparison of Virtual Machines and Linux Containers (frozen)

- Wesley Felter, Alexandre Ferreira, Ram Rajamony, Juan Rubio (IBM Research)
- ISPASS 2015: IEEE International Symposium on Performance Analysis of Systems and Software, pages 171-172, 2015
- DOI 10.1109/ISPASS.2015.7095802 (IEEE)
- PDF: [2015_Felter_VMsVsContainers.pdf](literature/papers/2015_Felter_VMsVsContainers.pdf) (IBM research report copy hosted by Harvard)

Claims it supports:

- VM overhead over native performance is real but usually small for CPU-bound work. Per the revised proposal, this reference stays only if the paper discusses virtualization overhead, for example in the limitations section.

### 7. Distributed Join-the-Idle-Queue for Low Latency Cloud Services

- Chunpu Wang, Chen Feng, Julian Cheng (University of British Columbia Okanagan)
- IEEE/ACM Transactions on Networking, volume 26, number 5, pages 2309-2319, October 2018
- DOI 10.1109/TNET.2018.2869092, arXiv:1709.10119
- PDF: [2018_Wang_DistributedJIQ.pdf](literature/papers/2018_Wang_DistributedJIQ.pdf) (arXiv version of the ToN paper)

Claims it may support:

- Differences between dispatching policies concentrate away from the light-load end. A possible citation for H3 (no clear difference at the lightest rate), which the revised proposal states without a source.

### 8. The power of two choices in randomized load balancing

- Michael D. Mitzenmacher
- IEEE Transactions on Parallel and Distributed Systems, volume 12, number 10, pages 1094-1104, 2001
- DOI 10.1109/71.963420 (IEEE)
- PDF: [2001_Mitzenmacher_PowerOfTwoChoices.pdf](literature/papers/2001_Mitzenmacher_PowerOfTwoChoices.pdf) (author copy, Harvard)

Claims it may support:

- Picking the less loaded of a small sample cuts queueing delay sharply compared with blind choice. With two workers, least unfinished requests looks at both, so it is the full version of this idea. Background for rule 3.

### 9. Critical Limitations of the Least Outstanding Request Load Balancing Policy in Service Meshes for Large-Scale Microservice Applications

- Andrea Detti, Ludovico Funari (University of Rome Tor Vergata)
- IEEE Transactions on Network and Service Management, 2025
- DOI 10.1109/TNSM.2025.3593870
- PDF: [2025_Detti_LeastOutstandingRequest.pdf](literature/papers/2025_Detti_LeastOutstandingRequest.pdf) (author-hosted accepted version, retrieved via a Wayback capture of the author's group page; a 2024 preprint also exists on TechRxiv, DOI 10.36227/techrxiv.170906303.32793543)

Claims it may support:

- The least outstanding request policy, the industry name for our least unfinished requests rule, has measured failure modes in large service meshes. Context only. Our two-worker testbed does not test those failure modes, and we do not claim the feedback rule fixes them.

### 10. Slicer: Auto-sharding for datacenter applications

- Atul Adya, Daniel Myers, Jon Howell, Jeremy Elson, Colin Meek, Vishesh Khemani, Stefan Fulger, Pan Gu, Luca Qian, Jason Wei, Hrishikesh Amur, Amit Bhayapudi, Nishant Shyamkumar, Neeraj Khadka, Stephen Connors, Peter Buhrdorf, Umar Javed (Google)
- OSDI '16: 13th USENIX Symposium on Operating Systems Design and Implementation, 2016
- https://www.usenix.org/conference/osdi16/technical-sessions/presentation/adya
- PDF: [2016_Adya_Slicer.pdf](literature/papers/2016_Adya_Slicer.pdf) (USENIX open access)

Claims it may support:

- Production systems balance load with measured performance and judge it by tail percentiles. Background only; cut it if the paper has enough production context from Prequal and Maglev.

### 11. Issues and Challenges of Load Balancing Techniques in Cloud Computing: A Survey

- Pawan Kumar, Rakesh Kumar
- ACM Computing Surveys, volume 51, number 6, article 120, February 2019
- DOI 10.1145/3281010 (ACM)
- PDF: not obtained. The paper is closed access. OpenAlex, Unpaywall, and Semantic Scholar all report no open-access copy, and no author-hosted or repository copy turned up in search. The citation stands without a local PDF; access via the university library or a request to the authors (NITTTR Chandigarh) are the legitimate routes.

Claims it may support:

- A taxonomy of cloud load balancing techniques, static versus dynamic, for the literature review. Devi et al. (2024) and Lohumi et al. (2023) in group B cover the same ground more recently, so the paper probably needs only one or two surveys.

### 12. Load balancing techniques in cloud computing environment: A review

- Dalia Abdulkareem Shafiq, N. Z. Jhanjhi, Azween Abdullah
- Journal of King Saud University - Computer and Information Sciences, volume 34, number 7, pages 3910-3933, 2022
- DOI 10.1016/j.jksuci.2021.02.007 (Elsevier, open access, CC-BY)
- PDF: not obtained. The article page (https://www.sciencedirect.com/science/article/pii/S131915782100046X) serves the PDF free of charge, but Elsevier's bot wall blocked the network it was fetched from. A team member can save it from the article page in a normal browser to `literature/papers/2022_Shafiq_CloudLBReview.pdf`.

Claims it may support:

- A recent survey of static and dynamic techniques and their evaluation settings. Same note as reference 11.

### Notes on versions

- Join-Idle-Queue also has a 2014 journal extension in IEEE/ACM Transactions on Networking ("Join-Idle-Queue: A novel load balancing algorithm for dynamically scalable web systems"). We cite the 2011 Performance Evaluation paper because it is the version the proposal deck referenced.
- The 2011 Join-Idle-Queue PDF is the Microsoft Research report copy, since the Elsevier journal page is paywalled. The content of the report matches the published paper.
- Wang, Feng, and Cheng is cited from the arXiv version (1709.10119). The citation follows the Crossref record for DOI 10.1109/TNET.2018.2869092. Some web sources attribute this paper to Scully and Harchol-Balter with different volume and page numbers; Crossref confirms the authors as Wang, Feng, and Cheng and the record as volume 26, number 5, pages 2309-2319.
- Sparrow's authors are Ousterhout, Wendell, Zaharia, and Stoica. The CSUR survey at DOI 10.1145/3281010 is by Pawan Kumar and Rakesh Kumar. The Detti and Funari paper's final venue is IEEE ToNSM 2025, not IEEE Access. These were corrected against publisher records on 2026-11-12.
- The Felter PDF is the IBM Research Report version of the ISPASS 2015 paper. Page numbers in the citation follow the IEEE record.
- Page numbers for the USENIX papers (Slicer, Maglev) are left out where they were not checked against the publisher record. Do not add them from memory.

## Group B: references added by the revised proposal

From the table in `paper/revised-proposal.md`. Numbers in the last column are the paper numbers in the gap analysis.

| Reference | Claim it supports | Gap analysis |
|---|---|---|
| Selen et al., Queueing Systems 84, 2016 | Our feedback rule is SED; SED equals join the shortest queue at equal speeds; SED is not exactly optimal (H1) | 9 |
| Gardner et al., Performance Evaluation 145, 2021 | SED-style dispatching with heterogeneous servers | 5 |
| Abdul Jaleel et al., Queueing Systems 102, 2022 | Speed-unaware rules do worse when speeds differ, most at heavy load (H2) | 6 |
| Michaelis et al., L3, Middleware 2024 | Closest recent systems use of (in-flight + 1) and latency | 1 |
| Aslanpour et al., FGCS 154, 2024 | How we set weighted round-robin weights; dynamic rules gained mainly under heavy load with unequal nodes | 11 |
| Devi et al., Artificial Intelligence Review 57, 2024 | Most load balancing studies use simulation | 14 |
| Papadopoulos et al., IEEE TSE 47(8), 2021 | Repeated runs and reporting the spread | 15 |
| Abedi and Brecht, ICPE 2017 | Shuffled run order | 17 |
| Kogias et al., Lancet, USENIX ATC 2019 | Open-loop load generation and achieved-rate checks | 16 |

The other gap analysis papers (ServiceRouter, Horus, Hermod, Tahir et al., Xie et al., Ma and Chi, Faridah and Suranegara, Lohumi et al., Ugedal and Kumar) are candidates. Each one enters the paper only with a claim it supports.

## Count

Group A gives 6 frozen references and group B adds 9, so the planned list has 15 before any cut. Felter et al. is conditional. Either way the course minimum of 8 is met.
