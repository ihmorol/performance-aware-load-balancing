# References

Full details for every paper considered for the term paper, with the claim each one supports in our work. PDFs live in [pdf/](pdf/). A reference that supports no claim gets cut, per the conventions in [README.md](README.md).

Every bibliographic entry below was checked against the publisher record (USENIX, Crossref, OpenAlex, or the journal page) on 2026-11-12, not taken from memory. Where a PDF is a preprint or a company technical report rather than the publisher copy, that is stated in the entry.

## Tier 1: core papers

These three papers are the ones we start from. Prequal defines performance-aware routing, Join-Idle-Queue defines the dispatcher-worker information problem, and The Tail at Scale defines the metrics and the slow-worker problem. The ranking rationale is in [research-notes.md](research-notes.md).

### 1. Load is not what you should balance: Introducing Prequal

- Bartek Wydrowski, Robert Kleinberg, Stephen M. Rumble, Aaron Archer (Google)
- NSDI '24: 21st USENIX Symposium on Networked Systems Design and Implementation, pages 1285-1299, 2024
- https://www.usenix.org/conference/nsdi24/presentation/wydrowski, arXiv:2312.10172
- PDF: [pdf/prequal-nsdi24-wydrowski.pdf](pdf/prequal-nsdi24-wydrowski.pdf) (USENIX open access)

Claims it supports:

- Requests differ in the work they need, and server speed varies, so a dispatcher that balances request counts alone leaves workers underused while queues grow elsewhere. This is the motivation behind our whole comparison.
- Google routes by estimated finish time per worker, built from requests in flight and each worker's recent speed. Our feedback rule, `(unfinished + 1) x recent average processing time`, is a small-scale version of that idea.
- "Load" as a single number is the wrong target. The paper argues latency is the target, which is why we measure response time percentiles rather than only queue depth.
- We cite it as related work that motivates our rule. We do not implement Prequal; our scope is a controlled local comparison of four simpler rules.

### 2. Join-Idle-Queue: A novel load balancing algorithm for dynamically scalable web services

- Yi Lu, Qiaomin Xie, Gabriel Kliot, Alan Geller, James R. Larus, Albert Greenberg
- Performance Evaluation, volume 68, number 11, pages 1056-1071, 2011
- DOI 10.1016/j.peva.2011.07.015 (Elsevier)
- PDF: [pdf/jiq-2011-lu-msr.pdf](pdf/jiq-2011-lu-msr.pdf) (Microsoft Research report copy of the same paper)

Claims it supports:

- Separating the dispatcher from the workers, and the information each side holds, is a real architecture decision. Our testbed has the same dispatcher-plus-workers shape.
- Queue-length information held by a dispatcher is stale by the time it is used. This is the strongest published warning about the exact weakness our feedback rule tries to fix with recent timing data.
- Load balancing must be evaluated under heterogeneous job sizes and varying service rates, not only uniform work. Our three scenarios follow that prescription at small scale.
- The paper's idle-state feedback idea explains when our "least unfinished" rule should do well (a worker that is idle reports so) and when it should not.

### 3. The Tail at Scale

- Jeffrey Dean, Luiz André Barroso (Google)
- Communications of the ACM, volume 56, number 2, pages 74-80, 2013
- DOI 10.1145/2408776.2408794 (ACM)
- PDF: [pdf/tail-at-scale-cacm13-dean-barroso.pdf](pdf/tail-at-scale-cacm13-dean-barroso.pdf) (author copy from barroso.org)

Claims it supports:

- Users feel the tail, so systems report and optimize percentiles, not just the mean. This is why our metrics table puts p95 next to the mean.
- Heterogeneity and interference create long tails even when average utilization is low. This is the mechanism our third scenario probes with a slowed worker.
- Latency variance, not just latency, is what routing can influence. We report variation across repeated runs for the same reason.

## Tier 2: strong support

### 4. Distributed Join-the-Idle-Queue for Low Latency Cloud Services

- Chunpu Wang, Chen Feng, Julian Cheng (University of British Columbia Okanagan)
- IEEE/ACM Transactions on Networking, volume 26, number 5, pages 2309-2319, October 2018
- DOI 10.1109/TNET.2018.2869092, arXiv:1709.10119
- PDF: [pdf/wang-jiq-ton18-arxiv.pdf](pdf/wang-jiq-ton18-arxiv.pdf) (arXiv version of the ToN paper)

Claims it supports:

- Closed-form analysis of distributed JIQ dispatching: when idle-feedback routing reaches low mean and tail response time, and where it does not beat simpler policies. This gives us principled hypotheses for the three request rates: feedback should matter more away from the idle extreme.
- The JIQ-Pod variant and its mean-field analysis connect dispatching policies to response-time math, which we use to sanity-check what differences we can honestly expect at two workers.

### 5. The power of two choices in randomized load balancing

- Michael D. Mitzenmacher
- IEEE Transactions on Parallel and Distributed Systems, volume 12, number 10, pages 1094-1104, 2001
- DOI 10.1109/71.963420 (IEEE)
- PDF: [pdf/mitzenmacher-power-of-two-tpds01.pdf](pdf/mitzenmacher-power-of-two-tpds01.pdf) (author copy, Harvard)

Claims it supports:

- The classical theory behind count-based routing: picking the less loaded of a small sample dramatically reduces queueing delay versus blind selection. Our least-unfinished rule is a deterministic version of this idea.
- A count of waiting jobs is a strong signal when job sizes are similar, and much weaker when they are not. This frames exactly where we expect the feedback rule to beat least-unfinished and where we expect a tie.

### 6. Critical Limitations of the Least Outstanding Request Load Balancing Policy in Service Meshes for Large-Scale Microservice Applications

- Andrea Detti, Ludovico Funari (University of Rome Tor Vergata)
- IEEE Transactions on Network and Service Management, 2025
- DOI 10.1109/TNSM.2025.3593870
- PDF: [pdf/detti-lor-tnsm25.pdf](pdf/detti-lor-tnsm25.pdf) (author-hosted accepted version, retrieved via a Wayback capture of the author's group page; a 2024 preprint also exists on TechRxiv, DOI 10.36227/techrxiv.170906303.32793543)

Claims it supports:

- The least outstanding request policy, which is our least-unfinished rule, has published, measured failure modes in request-level routing. This is a recent, peer-reviewed source that says the simple rule needs help, which is the gap our feedback rule addresses.
- Shows that the choice of routing rule measurably changes response time in real deployments, supporting the premise that the comparison we run is worth running.

## Tier 3: scheduling and production context

### 7. Sparrow: Distributed, Low Latency Scheduling

- Kay Ousterhout, Patrick Wendell, Matei Zaharia, Ion Stoica (UC Berkeley)
- SOSP '13: 24th ACM Symposium on Operating Systems Principles, pages 69-84, 2013
- DOI 10.1145/2517349.2522716 (ACM)
- PDF: [pdf/sparrow-sosp13-ousterhout.pdf](pdf/sparrow-sosp13-ousterhout.pdf)

Claims it supports:

- At millisecond scales, scheduler state propagation delay dominates. Stale state, not wrong math, is the enemy of good placement. This supports our choice to measure what the feedback rule achieves with limited, possibly stale, information.
- Sampling-based placement (batch sampling, Late binding) as a design point between blind and fully informed routing.

### 8. Slicer: Auto-sharding for datacenter applications

- Atul Adya, Daniel Myers, Jon Howell, Jeremy Elson, Colin Meek, Vishesh Khemani, Stefan Fulger, Pan Gu, Luca Qian, Jason Wei, Hrishikesh Amur, Amit Bhayapudi, Nishant Shyamkumar, Neeraj Khadka, Stephen Connors, Peter Buhrdorf, Umar Javed (Google)
- OSDI '16: 13th USENIX Symposium on Operating Systems Design and Implementation, 2016
- https://www.usenix.org/conference/osdi16/technical-sessions/presentation/adya
- PDF: [pdf/slicer-osdi16-adya.pdf](pdf/slicer-osdi16-adya.pdf) (USENIX open access)

Claims it supports:

- Production systems balance load at request-group level with latency-awareness, and sharding decisions depend on measured slice performance. Context for why performance-aware routing is a real production concern, not a classroom exercise.
- Demonstrates that load balancing quality is measured with tail percentiles and error budgets in production settings.

### 9. Maglev: A Fast and Reliable Software Network Load Balancer

- Daniel E. Eisenbud, Cheng Yi, Carlo Contavalli, Cody Smith, Roman Kononov, Eric Mann-Hielscher, Ardas Cilingiroglu, Bin Ye, Yaojun Cai, Andrew Shakhayev (Google)
- NSDI '16: 13th USENIX Symposium on Networked Systems Design and Implementation, 2016
- https://www.usenix.org/conference/nsdi16/technical-sessions/presentation/eisenbud
- PDF: [pdf/maglev-nsdi16-eisenbud.pdf](pdf/maglev-nsdi16-eisenbud.pdf) (USENIX/Google copy)

Claims it supports:

- The background layer our project sits above: production load balancers spread packets and connections at network level before any application-level routing rule sees a request. Used in the paper's background section to position dispatcher-level routing.

## Tier 4: surveys and testbed context

### 10. An Updated Performance Comparison of Virtual Machines and Linux Containers

- Wesley Felter, Alexandre Ferreira, Ram Rajamony, Juan Rubio (IBM Research)
- ISPASS 2015: IEEE International Symposium on Performance Analysis of Systems and Software, pages 171-172, 2015
- DOI 10.1109/ISPASS.2015.7095802 (IEEE)
- PDF: [pdf/felter-vm-vs-containers-ispass15.pdf](pdf/felter-vm-vs-containers-ispass15.pdf) (IBM research report copy hosted by Harvard)

Claims it supports:

- VM overhead over native performance is real but usually small for CPU-bound work, and containers trade isolation for smaller overhead. We use it to justify our VirtualBox VM testbed and to qualify what our measurements can and cannot say.

### 11. Issues and Challenges of Load Balancing Techniques in Cloud Computing: A Survey

- Pawan Kumar, Rakesh Kumar
- ACM Computing Surveys, volume 51, number 6, article 120, February 2019
- DOI 10.1145/3281010 (ACM)
- PDF: not obtained. The paper is closed access. OpenAlex, Unpaywall, and Semantic Scholar all report no open-access copy, and no author-hosted or repository copy turned up in search. The citation stands without a local PDF; access via the university library or a request to the authors (NITTTR Chandigarh) are the legitimate routes.

Claims it supports:

- Background and literature review section: taxonomy of cloud load balancing techniques, static versus dynamic classes, and the open challenges. Anchors the literature review required by the course guidelines.

### 12. Load balancing techniques in cloud computing environment: A review

- Dalia Abdulkareem Shafiq, N. Z. Jhanjhi, Azween Abdullah
- Journal of King Saud University - Computer and Information Sciences, volume 34, number 7, pages 3910-3933, 2022
- DOI 10.1016/j.jksuci.2021.02.007 (Elsevier, open access, CC-BY)
- PDF: not obtained. The article page (https://www.sciencedirect.com/science/article/pii/S131915782100046X) serves the PDF free of charge, but Elsevier's bot wall blocks this network's address, and no scholarly index, the Wayback Machine, or mirror host holds the PDF bytes. A team member can save it from the article page in a normal browser to `pdf/shafiq-lb-survey-jksuci22.pdf`.

Claims it supports:

- Recent survey covering static and dynamic techniques and their evaluation settings. Used with reference 11 so the literature review has both the established citation and a current one.

## PDF status

| File | Paper | Status |
|---|---|---|
| prequal-nsdi24-wydrowski.pdf | Prequal | downloaded, verified |
| tail-at-scale-cacm13-dean-barroso.pdf | Tail at Scale | downloaded, verified |
| jiq-2011-lu-msr.pdf | Join-Idle-Queue | downloaded, verified (MSR report copy) |
| wang-jiq-ton18-arxiv.pdf | Wang, Feng, and Cheng | downloaded, verified (arXiv copy of the ToN paper) |
| mitzenmacher-power-of-two-tpds01.pdf | Mitzenmacher | downloaded, verified |
| sparrow-sosp13-ousterhout.pdf | Sparrow | downloaded, verified |
| slicer-osdi16-adya.pdf | Slicer | downloaded, verified |
| maglev-nsdi16-eisenbud.pdf | Maglev | downloaded, verified |
| felter-vm-vs-containers-ispass15.pdf | Felter et al. | downloaded, verified (IBM report copy) |
| detti-lor-tnsm25.pdf | Detti and Funari | downloaded, verified (author-hosted accepted version via Wayback capture; DOI on page 1 matches ToNSM record) |
| kumar-lb-survey-csur19.pdf | Kumar and Kumar | no legal free copy exists (closed access; cite from DOI) |
| shafiq-lb-survey-jksuci22.pdf | Shafiq et al. | not obtainable from this network (publisher IP block; OA at ScienceDirect, manual fetch suggested) |

## Notes on versions

- Join-Idle-Queue also has a 2014 journal extension in IEEE/ACM Transactions on Networking ("Join-Idle-Queue: A novel load balancing algorithm for dynamically scalable web systems"). We cite the 2011 Performance Evaluation paper because it is the version the proposal deck referenced, and we note the extension here.
- The 2011 Join-Idle-Queue PDF we keep is the Microsoft Research report copy, since the Elsevier journal page is paywalled. The content of the report matches the published paper.
- Wang, Feng, and Cheng is cited from the arXiv version (1709.10119); the IEEE/ACM ToN copy is paywalled and the citation above follows the Crossref record for DOI 10.1109/TNET.2018.2869092. Note: some web sources attribute this paper to Scully and Harchol-Balter with different volume and page numbers; Crossref confirms the authors as Wang, Feng, and Cheng and the record as volume 26, number 5, pages 2309-2319.
- The Felter PDF is the IBM Research Report version of the ISPASS 2015 paper, hosted publicly by Harvard. Page numbers in the citation follow the IEEE record.
- Page numbers for the USENIX papers (Slicer, Maglev) are omitted where we did not verify them against the publisher record. Do not add them from memory.
