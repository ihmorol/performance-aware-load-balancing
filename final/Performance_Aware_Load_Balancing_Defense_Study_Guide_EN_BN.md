# Performance-Aware Load Balancing
## Detailed Proposal Defense and Presentation Study Guide
### Simple English + বাংলা

> **Purpose:** Understand the project, explain the slides confidently, present your assigned part, and answer proposal-defense questions honestly.
>
> **Project status:** This is a proposal and preparation guide. Statements about implementation and experiments describe planned work unless explicitly identified otherwise. No experimental results are claimed here.
>
> **বাংলায়:** এই guide-এর উদ্দেশ্য হলো project বুঝে বলা, নিজের presentation-এর অংশ ভালোভাবে উপস্থাপন করা এবং defense-এর প্রশ্নের সঠিক উত্তর দেওয়া। এখানে পরিকল্পনাকে completed result হিসেবে দেখানো হয়নি।

---

## Contents

1. [How to use this guide](#how-to-use)
2. [The whole project in 30 seconds](#project-summary)
3. [Understand the idea with a simple example](#simple-example)
4. [Essential terms: English and Bangla](#essential-terms)
5. [What the system will contain](#system-architecture)
6. [Slide-by-slide explanation and speaking notes](#slide-guide)
   - [Slide 1 — Title: Mahim](#slide-1)
   - [Slide 2 — Motivation: Mahim](#slide-2)
   - [Slide 3 — Research problem: Mahim](#slide-3)
   - [Slide 4 — Objectives: Ikramul](#slide-4)
   - [Slide 5 — Four rules: Ikramul](#slide-5)
   - [Slide 6 — Request flow: Ikramul](#slide-6)
   - [Slide 7 — Test plan: Omlan](#slide-7)
   - [Slide 8 — Expected contributions: Omlan](#slide-8)
   - [Slide 9 — References: backup](#slide-9)
   - [Slide 10 — Thank you: Omlan](#slide-10)
7. [Understand the four algorithms deeply](#four-algorithms)
8. [Follow one request from start to finish](#request-lifecycle)
9. [Understand the experiment plan](#experiment-plan)
10. [Understand the measurements, especially p95](#measurements)
11. [Fairness, repeatability, and limitations](#fairness)
12. [Proposal-defense questions and model answers](#defense-questions)
13. [Corrections and safer wording for the speech](#speech-corrections)
14. [Details that still need to be finalized](#open-decisions)
15. [Presentation timing and rehearsal](#rehearsal)
16. [Optional self-practice](#self-practice)
17. [Last-minute revision sheet](#revision-sheet)
18. [Source documents and scope of this guide](#sources)

---

<a id="how-to-use"></a>
## 1. How to use this guide

### Your learning order

1. Read the project summary and simple example.
2. Understand the dispatcher, workers, and request flow.
3. Understand the four routing rules, especially the feedback formula.
4. Study your own slides and speaking notes.
5. Learn the measurements and fairness controls.
6. Practice the defense answers in your own words.
7. Rehearse with the actual slide deck and a timer.

**বাংলায়:** প্রথমে পুরো project-এর ধারণা নিন। তারপর system কীভাবে কাজ করবে এবং চারটি নিয়ম কী করে, সেটি বুঝুন। এরপর নিজের slide ও speech practice করুন। সবকিছু একবারে মুখস্থ করার চেষ্টা করবেন না।

### Speaker assignments

This guide follows the latest speech supplied by the team, not the older member allocation in the presentation guide.

| Member | Slides | Main responsibility |
|---|---|---|
| Mahim | 1–3 | Explain the project, motivation, and research question. |
| Ikramul | 4–6 | Explain the objectives, algorithms, and system architecture. |
| Omlan | 7, 8, and 10 | Explain the experiments, contributions, and closing message. |
| All members | Q&A | Understand the entire project and support one another. |

### Important slide-order correction

The actual deck has:

- **Slide 9: References — backup only.**
- **Slide 10: Thank you / questions.**

The presentation guide describes those two in the opposite order. Use the actual deck when rehearsing. During the main talk, go from slide 8 to slide 10 without presenting the references slide. Practice that navigation beforehand.

There are **nine talk slides**: slides 1–8 and slide 10. Slide 9 is the additional backup slide.

**বাংলায়:** আসল deck-এ ৯ নম্বর slide references এবং ১০ নম্বর slide ending। তাই ৮ নম্বর slide-এর পরে মূল বক্তব্যে ১০ নম্বর slide-এ যাবেন। References শুধু প্রয়োজন হলে দেখাবেন।

### How to read the bilingual sections

- **Simple English:** Learn the idea in short sentences.
- **বাংলায়:** Understand the meaning naturally; do not memorize a word-for-word translation.
- **Suggested speech:** Presentation-ready wording you can adapt.
- **Defense note:** A detail that may matter when an examiner asks a question.

You do not need to speak both languages during the presentation unless your course permits or requires it. The Bangla explanations are primarily for understanding and preparation.

---

<a id="project-summary"></a>
## 2. The whole project in 30 seconds

### The central idea

> **Different requests need different amounts of work. We will compare four ways of choosing a worker and measure which works better under controlled conditions.**

**বাংলায়:** সব request করতে সমান সময় লাগে না। তাই কোন worker-কে request দিলে ভালো ফল পাওয়া যায়, সেটি চারটি নিয়ম ব্যবহার করে পরীক্ষা করব।

### A short English answer

> We will compare four load-balancing rules using two image-processing workers and one dispatcher on local virtual machines. The rules use turns, fixed shares, unfinished-request counts, or recent processing-time feedback. We will test similar images, mixed images, and mixed images with one slowed worker. We will measure response time, throughput, failures, and resource use. Our contribution is a fair, reproducible comparison, not a claim that we invented a new algorithm or that feedback always wins.

### বাংলায় একই বক্তব্য

> আমরা local virtual machine-এ দুটি image-processing worker এবং একটি dispatcher ব্যবহার করে চারটি load-balancing নিয়ম তুলনা করব। কোনো নিয়ম পালা করে request পাঠায়, কোনোটি নির্দিষ্ট অনুপাতে, কোনোটি অসমাপ্ত request গুনে, আর কোনোটি আগের processing time-ও বিবেচনা করে। একই ধরনের ছবি, ছোট-বড় ছবি এবং একটি ধীর worker দিয়ে পরীক্ষা করব। Response time, throughput, failure এবং resource use মাপব। আমাদের contribution হলো fair ও repeatable comparison। নতুন algorithm আবিষ্কার করা বা feedback সবসময় জিতবে, এমন দাবি করছি না।

### The research question in one sentence

> **When does knowing each worker's recent processing speed improve routing enough to justify the extra monitoring work?**

**বাংলায়:** Worker সম্প্রতি কত দ্রুত কাজ করছে, সেটি জানার জন্য যে অতিরিক্ত হিসাব রাখতে হবে, তার তুলনায় কখন যথেষ্ট সুবিধা পাওয়া যায়?

### What this project is not

- It is not a new public-cloud platform.
- It is not an AI or machine-learning project.
- It is not a complete implementation or reproduction of Prequal.
- It is not a guarantee that the feedback rule will win.
- It is not a claim about all clouds, all workloads, or all hardware.
- It does not claim measured money or energy savings.

---

<a id="simple-example"></a>
## 3. Understand the idea with a simple example

### A photo-processing shop

Imagine a shop with:

- One receptionist.
- Two people processing photos.
- Customers bringing different images.

The receptionist decides who receives each photo.

Some images are easy to process. Others take much longer. One person may also process photos more slowly than the other.

The shop wants customers to wait less.

| Shop example | Project equivalent |
|---|---|
| Customer asking for photo processing | A request |
| Receptionist choosing where the work goes | Dispatcher |
| Two photo processors | Two worker VMs |
| Rule used by the receptionist | Routing rule / load-balancing algorithm |
| Work waiting or currently being processed | Unfinished requests |
| Time spent editing a photo | Processing time |
| Customer's total wait for the result | Response time |

### বাংলায় উদাহরণ

ধরুন, একটি দোকানে দুইজন ছবি process করেন। একজন receptionist ঠিক করেন কোন ছবিটি কার কাছে যাবে।

সব ছবির কাজ সমান নয়। কোনো ছবির কাজ দ্রুত শেষ হয়। কোনো ছবির কাজ করতে বেশি সময় লাগে। আবার একজন অন্যজনের চেয়ে ধীরে কাজ করতে পারেন।

Receptionist যদি শুধু পালা করে ছবি দেন, তাহলে request-এর সংখ্যা সমান হতে পারে। কিন্তু কাজের পরিমাণ সমান নাও হতে পারে।

আপনাদের dispatcher-এর কাজও একই: নতুন request কোন worker-কে দেওয়া ভালো, সেটি ঠিক করা।

### Where the example stops being exact

The two worker VMs share one physical computer. They are not completely independent physical machines. Their performance can be affected by shared CPU, RAM, storage, and host activity.

**বাংলায়:** বাস্তব দোকানের দুইজন মানুষের মতো worker দুটি পুরোপুরি independent নয়। VM দুটি একই physical computer-এর resource ব্যবহার করে। এই সীমাবদ্ধতা report-এ বলতে হবে।

### Equal requests are not equal work

The following numbers are **illustrative only**, not project results.

| Worker | Requests received | Time per request | Total processing work |
|---|---:|---:|---:|
| A | 3 small images | 1 second | 3 seconds |
| B | 3 large images | 5 seconds | 15 seconds |

Both received three requests. Worker B received much more work.

> **Equal counts can hide unequal processing demand.**

**বাংলায়:** দুই worker-ই তিনটি request পেয়েছে। কিন্তু একটি worker-এর মোট কাজ তিন সেকেন্ডের, অন্যটির পনেরো সেকেন্ডের। তাই শুধু request গুনে কাজের পরিমাণ বোঝা যায় না।

---

<a id="essential-terms"></a>
## 4. Essential terms: English and Bangla

| Term | Simple English meaning | বাংলা অর্থ |
|---|---|---|
| Load balancing | Distributing incoming work between workers. | Worker-দের মধ্যে আসা কাজ ভাগ করা। |
| Routing rule | The rule used to choose a worker. | কোন worker-কে request দেওয়া হবে, তার নিয়ম। |
| Dispatcher | The service that selects a worker and forwards the request. | Worker বেছে নিয়ে request পাঠায় যে service। |
| Worker | A service that performs the image-processing task. | যে service ছবির আসল কাজটি করে। |
| Request | A message asking the service to do work. | কাজ করার জন্য service-কে পাঠানো অনুরোধ। |
| Response | The result or error returned for a request. | Request-এর উত্তর বা error। |
| Host | The physical computer running the experiment. | যে মূল computer-এ পরীক্ষা চলবে। |
| Virtual machine / VM | A software-created computer with its own operating system. | মূল computer-এর ভিতরে আলাদা operating system-সহ computer-এর মতো environment। |
| Virtualization | Running virtual computing environments on physical hardware. | Physical hardware-এর উপর virtual environment চালানো। |
| vCPU | CPU capacity presented to a VM; not automatically a dedicated physical core. | VM-কে দেওয়া virtual CPU; এটি সবসময় আলাদা physical core নয়। |
| Queue | Requests waiting for processing. | কাজ শুরু হওয়ার অপেক্ষায় থাকা request-এর লাইন। |
| Unfinished requests | Assigned requests that have not finished, including active and waiting ones. | যে request-এর কাজ চলছে বা অপেক্ষায় আছে, কিন্তু শেষ হয়নি। |
| In-flight request | A request that has been sent or assigned and has not completed, according to the defined measurement boundary. | পাঠানো বা assign করা হয়েছে, কিন্তু এখনো শেষ হয়নি এমন request। |
| Processing time | Time spent performing the image-processing operation. | ছবির কাজ করতে যে সময় লাগে। |
| Latency / response time | Time from sending a request to receiving its response. | Request পাঠানো থেকে উত্তর পাওয়া পর্যন্ত সময়। |
| Mean | Arithmetic average. | সাধারণ গড়। |
| p95 | A percentile describing a threshold met by about 95% of measured responses. | এমন একটি সময়সীমা, যার মধ্যে প্রায় ৯৫% measured response শেষ হয়। |
| Throughput | Completed requests per unit of time, usually per second. | প্রতি সেকেন্ডে শেষ হওয়া request-এর সংখ্যা। |
| Request rate | How quickly the load generator tries to send requests. | প্রতি সেকেন্ডে কত request পাঠানোর চেষ্টা করা হচ্ছে। |
| Overhead | Extra work needed to manage, monitor, or coordinate the system. | System পরিচালনা ও পর্যবেক্ষণের অতিরিক্ত কাজ। |
| Bottleneck | A component that limits the overall system's performance. | যে অংশের সীমাবদ্ধতায় পুরো system আটকে যায়। |
| Pilot | A small preliminary test before the main experiments. | মূল পরীক্ষার আগে ছোট আকারের পরীক্ষামূলক চালনা। |
| Calibration | Preliminary measurement used to choose settings, such as fixed weights. | আগে পরীক্ষা করে weight-এর মতো settings ঠিক করা। |
| CPU quota | A limit on CPU time available to a process or service. | কোনো process বা service কত CPU time পাবে, তার সীমা। |
| Timeout | A limit on how long the system waits for a request. | একটি request-এর জন্য সর্বোচ্চ অপেক্ষার সময়। |
| Health check | A check of whether a service is available and responsive. | Service সচল আছে কি না দেখার পরীক্ষা। |
| Probe | A small request used to obtain fresh information about a worker. | Worker-এর নতুন অবস্থা জানতে পাঠানো ছোট পরীক্ষামূলক request। |
| Cache | A stored result reused instead of repeating work. | আগের result রেখে পরে আবার ব্যবহার করা। |
| Reproducible | Documented well enough for others to repeat the experiment. | অন্যরা instructions মেনে পরীক্ষাটি আবার করতে পারবেন। |
| Baseline | A reference method used for comparison. | তুলনার জন্য নেওয়া মূল বা সহজ পদ্ধতি। |

### Three distinctions to remember

1. **Three VMs are not three workers:** there are two workers and one dispatcher.
2. **Processing time is not total response time:** queueing and communication add delay.
3. **Request rate is not throughput:** incoming work and completed work can differ.

---

<a id="system-architecture"></a>
## 5. What the system will contain

### 5.1 Logical architecture

```text
Physical computer / host
│
├── Load generator
│   └── Sends images according to a controlled request schedule
│
├── Dispatcher VM
│   ├── Receives each request
│   ├── Uses the currently active routing rule
│   ├── Forwards the request to one selected worker
│   └── Tracks request state and timing information
│
├── Worker VM A
│   └── Resizes and recompresses images
│
└── Worker VM B
    └── Runs the same image-processing code

Logs and resource measurements → analysis → tables and plots
```

One request is assigned to **one selected worker**. The proposal does not describe sending every request to both workers or splitting each image between them.

**বাংলায়:** একটি request-এর জন্য A অথবা B বেছে নেওয়া হবে। একই request সবসময় দুই worker-কে পাঠানো হবে না। একটি ছবিকে ভাগ করে দুই worker দিয়ে process করার পরিকল্পনাও এখানে নেই।

### 5.2 Planned starting resources

| Component | Planned starting allocation | Purpose |
|---|---|---|
| Worker VM A | 2 GB RAM, 1 vCPU | Process images. |
| Worker VM B | 2 GB RAM, 1 vCPU | Process images using the same code. |
| Dispatcher VM | 1 GB RAM, 1 vCPU | Select workers and forward requests. |
| Host | Runs the load generator and supports the VMs. | Provides shared physical resources. |

The documents report a checked device with **13.9 GB RAM and 12 logical processors**. These are source-document specifications, not a new hardware check performed for this study guide.

The starting VM memory allocations total 5 GB. That does not mean the complete experiment uses only 5 GB: the host operating system, VirtualBox, load generator, and other processes also need memory. Free RAM and disk space still need to be checked during the pilot.

**বাংলায়:** VM-এর জন্য মোট ৫ GB RAM বরাদ্দের পরিকল্পনা আছে। কিন্তু পুরো computer-এর ব্যবহার শুধু ৫ GB হবে না। Host operating system এবং অন্যান্য software-এরও RAM লাগবে।

### 5.3 Why one processing slot per worker?

Each worker will initially process one image at a time. Other accepted requests can wait within a bounded queue.

This makes the system easier to reason about. It also makes the simple delay formula more understandable, because work is processed approximately one job after another.

**বাংলায়:** এক worker এক সময়ে একটি ছবির কাজ করবে। এতে experiment-এর আচরণ বোঝা সহজ হবে। তবে one slot রাখলেই সব fairness নিশ্চিত হয় না; অন্য settings-ও consistent রাখতে হবে।

### 5.4 Technology roles

| Technology | Role | Simple explanation |
|---|---|---|
| VirtualBox base package | Virtualization | Runs the VMs on the host. |
| Ubuntu Server | Guest operating system | Provides the operating system inside each VM. |
| FastAPI | API application framework | Defines how requests are accepted and responses are returned. |
| Uvicorn | Application server | Runs the FastAPI application. |
| Pillow | Image-processing library | Resizes and recompresses images. |
| Python asyncio | Concurrent I/O coordination | Manages many waiting network operations without treating each wait as separate image-processing capacity. |
| HTTPX | HTTP client | Sends requests from the client or dispatcher. |
| CSV | Log format | Stores measurements in rows and columns. |
| time.perf_counter | Elapsed-time measurement | Measures durations on a local machine. |
| psutil | Resource monitoring | Measures CPU and memory use. |
| pytest | Automated testing | Checks behavior such as routing, timeouts, and output properties. |
| pandas | Data analysis | Reads and summarizes experiment data. |
| matplotlib | Plotting | Creates graphs from the measurements. |

**বাংলায়:** সব tool-এর বিস্তারিত মুখস্থ দরকার নেই। শুধু কোন tool কী কাজ করছে, সেটি বোঝা দরকার। FastAPI request নেওয়ার interface তৈরি করে, Pillow ছবির কাজ করে, HTTPX request পাঠায়, pandas data বিশ্লেষণ করে এবং matplotlib graph তৈরি করে।

### 5.5 Host-only networking

The plan uses a private VirtualBox host-only network so the host and VMs can communicate locally. The experiment does not require public internet exposure.

**বাংলায়:** Host এবং VM-গুলো private local network-এ যোগাযোগ করবে। Experiment চালানোর জন্য service-কে public internet-এ খুলে দেওয়ার প্রয়োজন নেই।

---

<a id="slide-guide"></a>
## 6. Slide-by-slide explanation and speaking notes

The scripts below are corrected, presentation-ready suggestions. They are not experimental claims. Use the English script for delivery and the Bangla explanation to understand what you are saying.

<a id="slide-1"></a>
### Slide 1 — Title

**Presenter:** Mahim  
**Purpose:** Introduce the team, project, and scope.  
**Memory cue:** Two workers + one dispatcher + four rules.

#### What the slide means

The project compares ways of distributing requests. It does not build a large cloud. It uses a small local environment to study one focused problem.

“Performance-aware” means using information about how workers have recently performed. It does not mean that every one of the four rules uses performance feedback.

#### বাংলায় বুঝুন

এই project-এ request ভাগ করার চারটি নিয়ম তুলনা করা হবে। বড় cloud platform বানানো হবে না। ছোট local setup-এ নির্দিষ্ট একটি সমস্যা পরীক্ষা করা হবে।

চারটি নিয়মের মধ্যে feedback rule worker-এর আগের performance ব্যবহার করে। Round-robin-এর মতো নিয়ম সেটি ব্যবহার করে না।

#### Suggested English speech

> Good morning. I am Mahim, and my teammates are Ikramul and Omlan. Our project is Performance-Aware Load Balancing. We will compare four ways of sharing image-processing requests between two workers. We will use three Ubuntu virtual machines on our own computer: two workers and one dispatcher. The project has a two-month scope and does not require paid cloud services.

#### বাংলা অর্থ

> সুপ্রভাত। আমি মাহিম। আমার teammates ইকরামুল এবং অম্লান। আমাদের project হলো Performance-Aware Load Balancing। Image-processing request দুটি worker-এর মধ্যে ভাগ করার চারটি নিয়ম আমরা তুলনা করব। নিজের computer-এ তিনটি Ubuntu VM ব্যবহার করব: দুটি worker এবং একটি dispatcher। Project-এর সময় দুই মাস এবং paid cloud service প্রয়োজন হবে না।

#### Presentation action

Point at the two worker boxes, then the dispatcher box. Do not call all three VMs workers.

#### Defense note

“No paid services” is safer than “there is no cost.” Existing hardware, electricity, and setup connectivity still have costs.

---

<a id="slide-2"></a>
### Slide 2 — Motivation

**Presenter:** Mahim  
**Purpose:** Explain why equal request distribution may not give equal work.  
**Memory cue:** Same count does not mean same work.

#### What the slide means

The left diagram shows similar-sized jobs. If workers have similar speed, taking turns can work reasonably well.

The right diagram shows uneven work. A long job can hold up one worker while another finishes its assigned work earlier.

A large image often requires more processing work, but compressed file size alone does not determine the exact cost. Dimensions, format, and processing settings also matter.

#### বাংলায় বুঝুন

বাম পাশে কাজগুলো প্রায় একই রকম। Worker-এর গতিও কাছাকাছি হলে পালা করে request দেওয়া ভালো কাজ করতে পারে।

ডান পাশে একটি বড় কাজ worker-কে বেশি সময় ব্যস্ত রাখছে। সেই worker-এর পরের request-গুলো অপেক্ষা করছে। অন্য worker-এর কাজ আগেই শেষ হতে পারে।

তাই শুধু কয়টি request দেওয়া হয়েছে, সেটি দেখলে যথেষ্ট নয়। Request করতে কত কাজ লাগছে, সেটিও গুরুত্বপূর্ণ।

#### Suggested English speech

> Web services often share requests between several servers. A simple rule is round-robin: each worker takes a turn. This can work well when jobs and worker speeds are similar. But our requests involve image processing, and different images can need different amounts of work. One long request can hold up a worker while another finishes early. So the main point is simple: the same number of requests does not mean the same amount of work.

#### বাংলা অর্থ

> Web service সাধারণত একাধিক server-এর মধ্যে request ভাগ করে। সহজ একটি নিয়ম হলো round-robin, যেখানে প্রতিটি worker পালা করে request পায়। কাজ ও worker-এর গতি প্রায় একই হলে এটি ভালো কাজ করতে পারে। কিন্তু image processing-এ ভিন্ন ছবির জন্য ভিন্ন পরিমাণ কাজ লাগে। একটি দীর্ঘ request একটি worker-কে আটকে রাখতে পারে, যখন অন্যটি আগেই কাজ শেষ করে। তাই request-এর সংখ্যা সমান হলেও কাজের পরিমাণ সমান নাও হতে পারে।

#### Optional example to explain aloud

> Suppose both workers receive three images. If one receives small images and the other receives large images, their request counts match but their processing work may not.

Label this as an example, not a measured result.

#### Presentation action

Point to the left diagram first, then the right. Pause before the takeaway sentence.

#### Defense note

Do not say “round-robin is always bad.” It is a useful baseline and may be sufficient in some conditions.

---

<a id="slide-3"></a>
### Slide 3 — Research problem

**Presenter:** Mahim  
**Purpose:** State the research question and honest research position.  
**Memory cue:** Recent speed may help, but monitoring has a cost.

#### What the slide means

The dispatcher must choose a worker. It can use simple rules, or it can also consider recent processing time.

The project asks whether the additional information improves response time enough to justify collecting and maintaining it.

#### বাংলায় বুঝুন

Dispatcher-কে ঠিক করতে হবে নতুন request কোথায় যাবে। সিদ্ধান্ত নেওয়ার সময় শুধু request count দেখা যায়, অথবা worker-এর আগের processing time-ও দেখা যায়।

কিন্তু এই তথ্য রাখতে অতিরিক্ত কাজ লাগে। সেই অতিরিক্ত কাজের তুলনায় সুবিধা পাওয়া যায় কি না, সেটিই research question।

#### Suggested English speech

> Our research question is: which routing rule keeps response time low when request sizes differ and worker capacity is unequal? We will test whether recent processing-time information helps the dispatcher make better choices. Keeping that information also requires extra work, so we will measure the trade-off. Similar routing ideas already exist in research, including Prequal from NSDI 2024. Our contribution is a small, fair, reproducible comparison on our own hardware, not a new algorithm. Now Ikramul will explain what we will build.

#### বাংলা অর্থ

> আমাদের প্রশ্ন হলো: request-এর কাজের পরিমাণ এবং worker-এর ক্ষমতা ভিন্ন হলে কোন routing rule response time কম রাখতে পারে? Worker-এর আগের processing time জানলে dispatcher ভালো সিদ্ধান্ত নিতে পারে কি না, আমরা পরীক্ষা করব। এই তথ্য রাখার অতিরিক্ত কাজও মাপব। Prequal-এর মতো গবেষণায় এই ধরনের ধারণা আগে থেকেই আছে। আমাদের contribution হলো নিজের hardware-এ ছোট, fair এবং repeatable comparison। এখন ইকরামুল system-এর পরিকল্পনা ব্যাখ্যা করবেন।

#### Why this wording is careful

The deck mentions worker speed changes. The specified third scenario establishes an unequal-capacity condition using a CPU quota. A sudden mid-run change and recovery experiment is not fully specified. Do not promise adaptation-time measurements unless that experiment is added and defined.

#### Presentation action

State the question, point at the dispatcher choosing between workers, then make the handoff clearly.

---

<a id="slide-4"></a>
### Slide 4 — Objectives

**Presenter:** Ikramul  
**Purpose:** Explain what the team will complete.  
**Memory cue:** Build → implement → test → analyze.

#### What the slide means

The four objectives are:

1. Build the VM testbed.
2. Implement four routing rules in one dispatcher.
3. Run repeatable experiments.
4. Analyze measurements and report the findings.

The pilot comes first because feasibility and suitable settings should be checked before the full experiment matrix.

#### বাংলায় বুঝুন

প্রথমে পরীক্ষা করার system তৈরি করব। তারপর dispatcher-এ চারটি নিয়ম implement করব। এরপর একই condition কয়েকবার চালিয়ে data সংগ্রহ করব। সবশেষে data বিশ্লেষণ করে report তৈরি করব।

Pilot হলো মূল পরীক্ষার আগে ছোট করে চালানো। এতে system চলে কি না এবং কী settings ব্যবহার করা উচিত, সেটি বোঝা যাবে।

#### Suggested English speech

> Thank you, Mahim. We have four objectives. First, build a working testbed with three Ubuntu VMs on VirtualBox. Second, implement all four routing rules in one dispatcher. Third, run repeatable experiments, with at least five runs for each test condition. Fourth, compare latency, throughput, failures, and resource use. Our schedule is eight weeks: a pilot first, then implementation, experiments, analysis, and finally the report and demonstration.

#### বাংলা অর্থ

> ধন্যবাদ মাহিম। আমাদের চারটি objective আছে। প্রথমে VirtualBox-এ তিনটি Ubuntu VM দিয়ে testbed তৈরি করব। এরপর একই dispatcher-এ চারটি routing rule implement করব। প্রতিটি test condition অন্তত পাঁচবার চালাব। তারপর latency, throughput, failure এবং resource use তুলনা করব। আট সপ্তাহের schedule-এ pilot, implementation, experiment, analysis এবং report ও demo থাকবে।

#### Schedule to remember

| Time | Planned work |
|---|---|
| Week 1 | Proposal refinement and pilot. |
| Weeks 2–3 | Implementation and correctness checks. |
| Weeks 4–5 | Main experiments. |
| Week 6 | Analysis. |
| Weeks 7–8 | Paper, setup guide, and recorded demo. |

#### Defense note

Do not promise a large production system. The scope is deliberately small to fit the time and hardware limits.

---

<a id="slide-5"></a>
### Slide 5 — The four routing rules

**Presenter:** Ikramul  
**Purpose:** Explain how the dispatcher chooses workers.  
**Memory cue:** Turns → fixed shares → unfinished count → estimated delay.

#### What the slide means

| Rule | Information used | Simple decision |
|---|---|---|
| Round-robin | Position in a rotation | Give each worker a turn. |
| Weighted round-robin | Fixed calibrated weights | Give a known faster worker a larger fixed share. |
| Least unfinished requests | Current unfinished count | Choose fewer unfinished requests. |
| Feedback rule | Unfinished count and recent average processing time | Choose the smaller estimated delay. |

Only one routing rule is active in a main experimental run. The same forwarding path handles requests regardless of the active rule.

#### বাংলায় বুঝুন

চারটি নিয়মই একই system-এর মধ্যে থাকবে। কিন্তু একবারের experiment-এ একটি নিয়ম চালু থাকবে।

Round-robin পালা দেখে। Weighted round-robin আগে নির্ধারিত অনুপাত দেখে। Least unfinished request-এর সংখ্যা দেখে। Feedback rule request-এর সংখ্যা এবং আগের কাজের সময়—দুটিই দেখে।

#### Suggested English speech

> These are the four rules. Round-robin sends requests in turn. Weighted round-robin gives a known faster worker a larger fixed share, using weights chosen during calibration. Least unfinished requests chooses the worker with fewer assigned requests that have not finished. This includes both running and waiting work. The feedback rule also uses the worker's recent average processing time. Its estimate is unfinished requests plus one, multiplied by recent average processing time. We choose the smaller estimate. All four rules use the same forwarding code, and we do not assume that feedback will win.

#### বাংলা অর্থ

> Round-robin পালা করে request পাঠায়। Weighted round-robin calibration-এ ঠিক করা অনুপাত অনুযায়ী বেশি সক্ষম worker-কে বেশি request দেয়। Least unfinished requests যে worker-এর অসমাপ্ত request কম, তাকে বেছে নেয়। এখানে চলমান ও অপেক্ষায় থাকা—দুটিই count করা হয়। Feedback rule-এর ক্ষেত্রে worker-এর আগের গড় processing time-ও দেখা হয়। অসমাপ্ত request-এর সঙ্গে এক যোগ করে সেই গড় সময় দিয়ে গুণ করা হয়। যার estimate কম, তাকে বেছে নেওয়া হয়। তবে feedback জিতবেই, এমন ধারণা নিয়ে পরীক্ষা করব না।

#### Presentation action

Point at each rule once. When explaining the formula, say “plus one is the new request.” Do not try to derive every detail during the main talk.

#### Defense note

The formula is a rough estimate, not an exact prediction. See [the worked examples](#four-algorithms) before presenting.

---

<a id="slide-6"></a>
### Slide 6 — How one request flows

**Presenter:** Ikramul  
**Purpose:** Walk through the system from input to result.  
**Memory cue:** Send → select → process → return → record → compare.

#### What the slide means

A controlled client sends an image. The dispatcher selects one worker. The worker processes the image and returns its processing time. The system records measurements. After the experiments, the team analyzes the logs.

The feedback information is used for later selections. It does not change how an already-finished request was routed.

#### বাংলায় বুঝুন

প্রথমে test client একটি ছবি পাঠায়। Dispatcher A অথবা B বেছে নেয়। Worker ছবির কাজ করে result ও processing time ফেরত দেয়। System সেই তথ্য record করে। পরে log থেকে analysis করা হয়।

আগের request-এর সময় পরের request-এর সিদ্ধান্তে সাহায্য করতে পারে। এটি ভবিষ্যতের সিদ্ধান্তের feedback।

#### Suggested English speech

> This is how one request flows. The load generator sends an image from a fixed test set. The dispatcher selects one worker using the active rule. That worker resizes and recompresses the image, then returns the result and its processing time. We record request details, timings, errors, and resource measurements. The feedback rule uses recent timing information for later routing decisions. After repeated runs, we analyze the logs with pandas and create plots with matplotlib. Everything runs on one physical computer, with one processing slot per worker. That is the testbed. Now Omlan will explain the test plan and expected outputs.

#### বাংলা অর্থ

> Load generator আগে নির্ধারিত test set থেকে ছবি পাঠাবে। Dispatcher চালু থাকা নিয়ম অনুযায়ী একটি worker বেছে নেবে। Worker ছবির size বদলাবে এবং recompress করবে। তারপর result ও processing time ফেরত দেবে। Request-এর তথ্য, সময়, error এবং resource measurements record করা হবে। Feedback rule পরের সিদ্ধান্তে আগের সময় ব্যবহার করবে। কয়েকবার experiment চালানোর পর pandas ও matplotlib দিয়ে analysis এবং graph তৈরি করব। সবকিছু একটি physical computer-এ চলবে, এবং প্রতিটি worker এক সময়ে একটি ছবির কাজ করবে। এখন অম্লান test plan ও output ব্যাখ্যা করবেন।

#### Presentation action

Trace the arrows in order. Do not jump between tool names before explaining the flow.

#### Defense notes

- “Fixed images” means a controlled dataset, not necessarily the same image for every request.
- Logging CPU/RAM requires monitoring the relevant components, not only reading worker replies.
- The same processing-time metadata can be collected under every rule; only the feedback rule needs to use it for its selection decision.
- Async request handling does not mean each worker processes unlimited images simultaneously.

---

<a id="slide-7"></a>
### Slide 7 — Test plan

**Presenter:** Omlan  
**Purpose:** Show that the comparison will be controlled and measurable.  
**Memory cue:** Three scenarios → three rates → five repeats → several metrics.

#### What the slide means

Every rule will be tested under three scenarios and three request rates. Each condition will be repeated at least five times.

The three scenarios are:

1. Uniform or similar images.
2. Mixed image sizes.
3. Mixed image sizes with one worker slowed using a Linux CPU quota.

#### বাংলায় বুঝুন

প্রতিটি নিয়ম একই ধরনের ছবি, ছোট-বড় মিশ্র ছবি এবং একটি ধীর worker-সহ মিশ্র ছবির condition-এ চালানো হবে। প্রতিটি condition-এ তিনটি rate থাকবে এবং অন্তত পাঁচবার পরীক্ষা করা হবে।

একটি algorithm-এর জন্য সহজ input এবং অন্যটির জন্য কঠিন input দেওয়া যাবে না। তুলনার শর্ত একই রাখতে হবে।

#### Suggested English speech

> Thank you, Ikramul. We will use three scenarios: uniform images, mixed sizes, and mixed sizes with one slowed worker. Every rule will run at three request rates, with at least five repetitions for each condition. We will choose the rates during the pilot and keep them fixed across methods. We will disable output caching, reset state between runs, and vary the run order. We will measure mean response time, p95, throughput, failures, and CPU and RAM use. p95 describes the time within which about 95 percent of measured replies finish. It helps us understand slower responses that the average alone may hide. We will also check that the host, client, and dispatcher are not the bottleneck.

#### বাংলা অর্থ

> ধন্যবাদ ইকরামুল। আমরা তিনটি scenario ব্যবহার করব: একই ধরনের ছবি, ছোট-বড় মিশ্র ছবি এবং একটি ধীর worker-সহ মিশ্র ছবি। প্রতিটি নিয়ম তিনটি request rate-এ চলবে এবং প্রতিটি condition অন্তত পাঁচবার repeat হবে। Pilot-এ rate ঠিক করে তুলনার সময় একই রাখা হবে। Output caching বন্ধ থাকবে, run-এর মাঝে state reset করা হবে এবং run order বদলানো হবে। Mean response time, p95, throughput, failure এবং CPU/RAM মাপব। p95 হলো এমন সময়, যার মধ্যে measured reply-এর প্রায় ৯৫ শতাংশ শেষ হয়। Host, client বা dispatcher bottleneck হচ্ছে কি না, সেটিও দেখব।

#### The experiment count

```text
4 rules × 3 scenarios × 3 rates × 5 repetitions = 180 main runs
```

A run contains many requests. It is not one request. Pilot runs and extra validation runs are additional.

#### Presentation action

Point to one row and one column of the grid to explain its structure. You do not need to list all 180 combinations aloud.

#### Critical p95 correction

Do not say “one very slow reply cannot hide.” p95 can miss an isolated extreme delay. See [the measurement section](#measurements).

---

<a id="slide-8"></a>
### Slide 8 — Expected contributions

**Presenter:** Omlan  
**Purpose:** Explain what the project will deliver and what it will not claim.  
**Memory cue:** Reproducible outputs + measured guidance + clear limits.

#### What the slide means

The main contribution is not a promised performance improvement. It is a working experimental system and a defensible comparison.

The deliverables are code, logs, plots, setup instructions, a paper, and a demo.

#### বাংলায় বুঝুন

আমাদের contribution শুধু “দ্রুত algorithm বানালাম” নয়। এমন একটি system এবং পরীক্ষার ফল তৈরি করব, যা অন্যরা বুঝতে এবং repeat করতে পারবেন।

Feedback ভালো না করলেও পরীক্ষাটি অর্থপূর্ণ হতে পারে। তখন কোন condition-এ বাড়তি সুবিধা পাওয়া যায়নি, সেটি জানাব।

#### Suggested English speech

> At the end, we will deliver the source code, a reproducible testbed, raw logs, plots, and a setup guide. We will also prepare a ten-to-fifteen-page paper and a recorded demonstration. Our findings will describe when feedback helps, or does not help, in our tested conditions. We are not claiming a new algorithm or results that apply to all clouds. If the simple rules perform just as well within the variation we observe, we will report that honestly too.

#### বাংলা অর্থ

> শেষে source code, repeat করা যায় এমন testbed, raw log, graph এবং setup guide দেব। সঙ্গে ১০–১৫ পাতার paper এবং recorded demo থাকবে। আমাদের পরীক্ষার condition-এ feedback কখন সাহায্য করেছে বা করেনি, সেটি জানাব। নতুন algorithm বা সব cloud-এর জন্য সত্য ফলাফল দাবি করব না। সাধারণ নিয়মও যদি পরীক্ষার variation-এর মধ্যে একই রকম ভালো করে, সেটিও সৎভাবে জানাব।

#### Defense note

“No clear difference in our experiments” does not automatically prove that the methods are equivalent everywhere. Your conclusion must stay within the tested conditions and the measurement uncertainty.

---

<a id="slide-9"></a>
### Slide 9 — References, backup only

**Presenter:** Not part of the main talk.  
**Purpose:** Support source-related questions during Q&A.

The actual slide contains six preliminary references. Their broad relevance is:

| Reference | Why it is relevant to this proposal |
|---|---|
| Prequal, NSDI 2024 | Related work on performance-aware request routing. |
| The Tail at Scale, 2013 | Motivation for examining slow responses, not just averages. |
| Join-Idle-Queue, 2011 | Background on worker availability and dispatching. |
| Sparrow, SOSP 2013 | Background on scheduling and low-latency work distribution. |
| Maglev, NSDI 2016 | Context for software load balancing at larger scale. |
| VM and Linux container performance comparison, ISPASS 2015 | Background on virtualization and performance reporting. |

This guide uses their relevance as described in the supplied materials. It does not independently verify or reproduce the papers' methods or results.

#### If asked about your research basis

> We cite Prequal as related work on performance-aware routing. Our implementation is a simpler local comparison, not a full reproduction of that system. We also cite work on tail latency, scheduling, and virtualization.

**বাংলায়:** Prequal-কে related work হিসেবে ব্যবহার করছি। কিন্তু পুরো Prequal system reproduce করার দাবি করছি না। Tail latency, scheduling এবং virtualization-এর গবেষণাও background হিসেবে আছে।

#### Reference-count note

The backup slide has six preliminary sources. The proposal specifies **at least eight reliable references for the final paper**. Those are different stages of the project.

---

<a id="slide-10"></a>
### Slide 10 — Thank you and questions

**Presenter:** Omlan  
**Purpose:** Finish with the research question and invite discussion.  
**Memory cue:** When does knowing worker speed pay off?

#### Suggested English speech

> Our main question is simple: when does knowing each worker's recent speed help us route requests better? We will answer it through a controlled comparison and report both the benefits and the limitations. Thank you. We are happy to take your questions.

#### বাংলা অর্থ

> আমাদের মূল প্রশ্ন হলো: worker সম্প্রতি কত দ্রুত কাজ করছে, সেটি জানলে কখন ভালোভাবে request পাঠানো যায়? Controlled comparison দিয়ে সেই প্রশ্নের উত্তর খুঁজব এবং সুবিধা ও সীমাবদ্ধতা দুটিই জানাব। ধন্যবাদ। এখন আমরা প্রশ্নের উত্তর দেব।

#### Presentation action

Stop after the invitation. Do not add a new algorithm explanation or read the references unless asked.

---

<a id="four-algorithms"></a>
## 7. Understand the four algorithms deeply

> All numerical examples in this section are teaching examples. They are not measured project results.

### 7.1 Round-robin

#### Rule

Give each worker a turn.

```text
Request 1 → A
Request 2 → B
Request 3 → A
Request 4 → B
Request 5 → A
Request 6 → B
```

#### What it knows

It mainly needs to remember whose turn comes next. It does not use recent processing speed or current unfinished-request counts to choose between available workers.

#### Strength

It is simple and has little selection overhead. It may work well when jobs and worker speeds are similar.

#### Limitation

It can keep assigning work to a slow worker just because that worker's turn has arrived.

**বাংলায়:** এই নিয়ম সহজ। শুধু পরের পালা কার, সেটি মনে রাখতে হয়। কিন্তু ধীর worker-ও পালা অনুযায়ী request পেতে থাকে।

#### Defense sentence

> Round-robin is our simple baseline, not an algorithm we assume is always bad.

### 7.2 Weighted round-robin

#### Rule

Use a fixed proportion chosen through calibration.

For an illustrative weight ratio of A:B = 2:1, one possible sequence is:

```text
A → A → B → A → A → B
```

Different weighted-round-robin implementations can produce different orderings while targeting the same proportions. The chosen variant should be documented.

#### What it knows

It knows the preselected weights. It does not continuously change them using recent timing feedback.

#### Strength

It can represent a stable, known capacity difference.

#### Limitation

A previously good fixed ratio may become less suitable if capacity or workload characteristics change.

**বাংলায়:** আগে থেকে জানা capacity অনুযায়ী request ভাগ করা যায়। কিন্তু পরে worker-এর গতি বদলালে weight নিজে থেকে বদলাবে না।

#### Calibration fairness

Choose and document when calibration happens. Do not secretly retune weights based on the main test outcomes. For a comparison with fixed unequal worker capacity, explain whether calibration sees that condition. This detail is not fully finalized in the proposal.

### 7.3 Least unfinished requests

#### Rule

Choose the worker with the smaller number of assigned requests that have not completed.

```text
Worker A: 4 unfinished requests
Worker B: 1 unfinished request

Decision: choose B
```

#### What counts as unfinished?

If A has one image being processed and three waiting images, A has four unfinished requests.

```text
Unfinished = currently processing + waiting after assignment
```

The precise assignment and completion boundaries must be implemented consistently. This is not the same as blindly using TCP connection counts.

#### Strength

It reacts to current outstanding work. A slow worker may naturally accumulate more unfinished requests, causing the rule to send work elsewhere.

#### Limitation

One long request and one short request both count as one. A smaller request count is not always a smaller amount of processing work.

**বাংলায়:** এই নিয়ম worker-এর বর্তমান অসমাপ্ত request দেখে। ধীর worker-এর request জমে গেলে সেটিকে কম কাজ দিতে পারে। কিন্তু প্রতিটি request কত বড় কাজ, তা সরাসরি বোঝে না।

### 7.4 Feedback-based routing

#### Rule

For each available worker, calculate:

```text
estimated_delay = (unfinished_requests + 1) × recent_average_processing_time
```

Choose the smaller estimate.

#### Explain every part

| Part | Meaning | বাংলা |
|---|---|---|
| `unfinished_requests` | Work already assigned but not finished. | আগে দেওয়া কিন্তু শেষ না হওয়া কাজ। |
| `+ 1` | The new request being considered. | নতুন request-এর জন্য এক যোগ। |
| `recent_average_processing_time` | Recent typical time spent processing requests on that worker. | Worker সম্প্রতি একটি request করতে গড়ে যত সময় নিয়েছে। |
| Multiplication | A rough estimate of how long that amount of work may take. | ওই পরিমাণ কাজ শেষ হতে আনুমানিক সময়। |
| Choose smaller | Prefer the lower predicted delay. | কম আনুমানিক সময়ের worker বেছে নেওয়া। |

#### Why the units make sense

A request count has no time unit. The recent average might be in milliseconds per request. Multiplying the count by that average produces an estimate in milliseconds.

**বাংলায়:** কয়টি কাজ আছে, সেটিকে প্রতি কাজের গড় সময় দিয়ে গুণ করলে মোট আনুমানিক সময় পাওয়া যায়।

#### Example A: a busy fast worker versus an idle slow worker

| Worker | Unfinished | Recent average | Estimate |
|---|---:|---:|---:|
| A | 2 | 100 ms | `(2 + 1) × 100 = 300 ms` |
| B | 0 | 500 ms | `(0 + 1) × 500 = 500 ms` |

- Least unfinished chooses **B**.
- Feedback chooses **A**.

Why? A has work, but its recent processing time is much smaller.

**বাংলায়:** A ব্যস্ত হলেও দ্রুত। B খালি হলেও ধীর। তাই feedback-এর আনুমানিক হিসাবে A ভালো হতে পারে।

#### Example B: a fast worker can still be too busy

| Worker | Unfinished | Recent average | Estimate |
|---|---:|---:|---:|
| A | 9 | 100 ms | `(9 + 1) × 100 = 1,000 ms` |
| B | 0 | 500 ms | `(0 + 1) × 500 = 500 ms` |

Feedback chooses **B** this time.

> The feedback rule does not always choose the fastest worker. It combines speed with outstanding work.

**বাংলায়:** Feedback সবসময় দ্রুততম worker-কে বেছে নেয় না। কাজের চাপ বেশি হলে ধীর কিন্তু খালি worker-কে বেছে নিতে পারে।

#### Example C: equal processing-time estimates

If both workers have the same recent average processing time, the formula ranks them by unfinished count. In that moment, it behaves like least unfinished requests, apart from tie handling and shared availability rules.

**বাংলায়:** দুই worker-এর average time সমান হলে যার unfinished request কম, তার estimate কম হবে। তখন feedback-এর সিদ্ধান্ত least unfinished-এর মতো হতে পারে।

### 7.5 What “recent average” does not yet specify

The proposal does not finalize whether the implementation uses a rolling window, an exponentially weighted average, or another clearly defined recent average.

Do not claim a particular window size or smoothing factor during the defense unless the team has selected and documented it.

A safe answer is:

> We will define the averaging method before the main experiments and keep it consistent. The proposal currently specifies the information used, not the final smoothing parameter.

**বাংলায়:** Average কীভাবে হিসাব হবে, সেটি মূল পরীক্ষার আগে নির্ধারণ করব। Proposal-এ এখন কোন তথ্য ব্যবহার হবে, সেটি বলা আছে; exact smoothing parameter final করা হয়নি।

### 7.6 Why the estimate is imperfect

The formula does not fully account for:

- The exact processing demand of each queued image.
- How much of the currently running image is already finished.
- Sudden changes in worker capacity.
- Network and dispatcher overhead.
- Variation in image dimensions, format, or content.
- Bias caused by different workers receiving different mixtures of jobs.

Recent average processing time is a useful signal to test. It is not a pure, workload-independent measurement of hardware speed.

**বাংলায়:** Worker বড় ছবি বেশি পেলে তার average time বাড়তে পারে, যদিও hardware ধীর হয়নি। তাই average time-কে worker-এর স্থায়ী speed ধরে নেওয়া যাবে না। এই সীমাবদ্ধতাই পরীক্ষা করে দেখতে হবে।

### 7.7 Startup, ties, and stale information

The proposal includes:

- Pilot calls to initialize worker timing estimates.
- Alternating tie decisions to avoid always favoring one worker.
- Periodic probes of idle workers to refresh stale information.

Health checks and performance probes have different purposes:

- A health check asks whether the service is available.
- A performance probe helps refresh information about how it is performing.

Probe traffic is extra work. The experiment should account for it rather than hiding it.

**বাংলায়:** শুরুতে worker-এর সময় জানা থাকবে না, তাই কিছু pilot call লাগবে। কোনো worker অনেকক্ষণ request না পেলে তার পুরোনো তথ্য ভুল হতে পারে। Probe দিয়ে সেটি নতুন করা যায়। তবে probe-এর অতিরিক্ত কাজও হিসাব করতে হবে।

---

<a id="request-lifecycle"></a>
## 8. Follow one request from start to finish

### Step 1 — Plan the request

The load generator has a controlled image set and request schedule. It selects the next image and plans when to send it.

**বাংলা:** কোন ছবি কখন পাঠানো হবে, সেটি আগে থেকে নির্ধারিত থাকবে।

### Step 2 — Send the request

The client records timing information and sends the image to the dispatcher.

**বাংলা:** Client সময় record করে dispatcher-কে request পাঠাবে।

### Step 3 — Choose an available worker

The active rule selects A or B. The dispatcher must update unfinished-request tracking consistently with assignment.

**বাংলা:** চালু থাকা নিয়মে A অথবা B বেছে নেওয়া হবে। Request assign হলে count ঠিকভাবে বাড়াতে হবে।

### Step 4 — Wait if needed

If the selected worker is already processing an image, an accepted request may wait. The worker queue is bounded. What happens when it is full must be defined consistently.

**বাংলা:** Worker ব্যস্ত থাকলে request অপেক্ষা করবে। Queue পূর্ণ হলে কী হবে, সেটি আগে থেকে নির্ধারণ করতে হবে।

### Step 5 — Process the image

The worker performs the chosen resize and recompression operation. It measures the operation's processing time.

**বাংলা:** Worker ছবির কাজ করবে এবং সেই কাজের সময় মাপবে।

### Step 6 — Return the result

The worker returns the processed image and timing information through the dispatcher to the client.

**বাংলা:** Result এবং timing information dispatcher হয়ে client-এর কাছে যাবে।

### Step 7 — Complete accounting

The system records the outcome and updates request state. Errors, cancellations, and timeouts require careful accounting too.

A client timeout does not automatically prove that worker-side processing has stopped. The implementation must define how this situation affects unfinished counts and logging.

**বাংলা:** Client timeout দেখালেও worker-এর কাজ সঙ্গে সঙ্গে বন্ধ হয়েছে, এমন নয়। এই অবস্থায় count ও log কীভাবে ঠিক রাখা হবে, সেটি implementation-এ স্পষ্ট করতে হবে।

### Step 8 — Update estimates where applicable

The feedback rule can use the completed request's processing time to update its estimate. Other rules can collect the same timing data without using it for selection.

**বাংলা:** Feedback rule এই সময় পরের সিদ্ধান্তে ব্যবহার করতে পারে। অন্য নিয়মেও data record হবে, কিন্তু সিদ্ধান্তে ব্যবহার নাও হবে।

### Step 9 — Analyze after the run

Combine request logs, configuration, and resource measurements. Compare repeated runs rather than selecting one attractive result.

**বাংলা:** Run শেষে request log, settings এবং resource data একসঙ্গে বিশ্লেষণ করতে হবে। শুধু সবচেয়ে সুন্দর ফলাফলটি বেছে দেখানো যাবে না।

### Timing boundaries

```text
Client sends request
    ↓
Communication and dispatcher work
    ↓
Waiting for the worker's processing slot
    ↓
Image processing
    ↓
Return path
    ↓
Client receives response
```

```text
End-to-end response time includes the whole path.
Worker processing time measures only the defined processing operation.
```

For reliable elapsed times, measure durations on the same machine with a monotonic clock. Do not subtract unrelated host and VM wall-clock timestamps as if the clocks were perfectly synchronized.

**বাংলায়:** Client নিজের request-এর মোট সময় নিজে মাপবে। Worker নিজের processing duration নিজে মাপবে। আলাদা machine-এর clock পুরোপুরি synchronized ধরে একটির timestamp থেকে অন্যটি বিয়োগ করা ঠিক নয়।

---

<a id="experiment-plan"></a>
## 9. Understand the experiment plan

### 9.1 The experiment matrix

| Dimension | Planned choices |
|---|---|
| Routing method | Round-robin, weighted round-robin, least unfinished, feedback. |
| Scenario | Uniform images; mixed images; mixed images with one slowed worker. |
| Request rate | Three rates selected during the pilot. |
| Repetitions | At least five per condition. |

```text
Distinct conditions = 4 × 3 × 3 = 36
Minimum main runs = 36 × 5 = 180
```

The minimum count excludes pilot runs, correctness checks, and any additional repetitions.

**বাংলায়:** মোট condition ৩৬টি। প্রতিটি condition পাঁচবার চালালে মূল run হবে ১৮০টি। Pilot ও অন্য check এর বাইরে।

### 9.2 What one condition means

An example condition is:

```text
Method: feedback
Scenario: mixed images with one slowed worker
Request rate: the middle pilot-selected rate
Repetition: run 3 of at least 5
```

Every run contains many requests. Run duration and request count still need to be finalized.

### 9.3 Why these scenarios?

#### Uniform images

Tests the simpler case where job costs are more similar. Simple rules may already work well.

**বাংলা:** কাজ প্রায় একই হলে সাধারণ নিয়ম যথেষ্ট কি না দেখা যাবে।

#### Mixed images

Tests the effect of unequal job demand without deliberately changing one worker's CPU capacity.

**বাংলা:** ছোট-বড় কাজ মিশলে request count-এর সীমাবদ্ধতা বোঝা যাবে।

#### Mixed images with one slowed worker

Tests unequal work together with unequal worker capacity.

**বাংলা:** কাজের আকার এবং worker-এর ক্ষমতা—দুই ধরনের পার্থক্য একসঙ্গে পরীক্ষা করা হবে।

### 9.4 Why three request rates?

Routing differences may be hard to see when the system is almost idle. Under heavier load, queueing can matter more. At excessive load, failures and growing queues can dominate.

The pilot should help choose meaningful rates. The exact numerical values are not provided in the proposal.

For a fair comparison, each method must receive the same offered rate and schedule for the same scenario/rate condition.

**বাংলায়:** Request খুব কম হলে সব algorithm-ই ভালো মনে হতে পারে। Request বাড়লে queue তৈরি হয় এবং পার্থক্য দেখা যেতে পারে। আবার অতিরিক্ত request দিলে সব method-ই সমস্যায় পড়তে পারে। তাই pilot করে rate ঠিক করা দরকার।

### 9.5 Planned rate versus achieved rate

Suppose the client is configured to send a certain number of requests per second but cannot keep up. Then the actual test load is lower or more irregular than planned.

Record both the planned schedule and the achieved sending rate. Otherwise, a method might appear better simply because it received less load.

**বাংলায়:** Client যত request পাঠানোর কথা, বাস্তবে তত পাঠাতে পারছে কি না দেখতে হবে। কম request গেলে result ভুলভাবে ভালো দেখাতে পারে।

### 9.6 Why repeat at least five times?

Repeated runs reveal variation caused by scheduling, background activity, resource contention, and other noise.

Five runs is a minimum plan, not a universal statistical guarantee. If the variation is large or conclusions are unclear, additional repetitions or more cautious conclusions may be needed.

**বাংলায়:** পাঁচবার পরীক্ষা করলেই result অবশ্যই নিশ্চিত হয়ে যায় না। Variation বেশি হলে আরও run লাগতে পারে বা conclusion সাবধানে বলতে হবে।

### 9.7 Why vary run order?

If one algorithm always runs first and another always runs last, order-related effects can become confused with algorithm effects.

Changing the order reduces systematic favoritism. Record the actual run order so the procedure can be repeated and inspected.

**বাংলায়:** সবসময় একই algorithm আগে চললে computer-এর তখনকার অবস্থার সুবিধা পেতে পারে। তাই order বদলানো এবং record করা দরকার।

### 9.8 Why disable output caching?

The same input may be replayed many times. If a cached output is returned, the service may skip the image-processing work you intended to measure.

“Output caching disabled” does not mean every CPU, operating-system, and filesystem cache is completely eliminated. Use a consistent warm-up and reset procedure and document its boundaries.

**বাংলায়:** আগের processed image ফেরত দিলে নতুন করে কাজ হবে না। তাই application-এর output cache বন্ধ রাখতে হবে। তবে computer-এর সব ধরনের cache বন্ধ হয়েছে, এমন দাবি করা যাবে না।

### 9.9 What reset should mean

The exact reset procedure should be documented. It may include draining or clearing outstanding work, resetting counters and routing estimates, restoring scenario settings, and starting separate logs.

Do not say “we reset everything” without defining what that means. A reset does not necessarily require rebooting every VM.

---

<a id="measurements"></a>
## 10. Understand the measurements, especially p95

### 10.1 Response time / latency

Response time is the elapsed time from the client sending a request to receiving its response, according to the chosen measurement boundary.

Conceptually:

```text
Response time
≈ request communication
+ dispatcher work
+ waiting
+ image processing
+ response communication
```

**বাংলায়:** User-এর দৃষ্টিতে মোট কত সময় লাগল, সেটি response time। শুধু worker-এর কাজের সময় নয়।

### 10.2 Processing time

Processing time describes the worker's actual image-processing operation under the defined timing boundary.

It should not silently include some workers' queueing delay while excluding others'. Define the measurement consistently.

**বাংলায়:** Processing time হলো ছবির কাজ করার সময়। Worker-ভেদে কখনো queue-এর সময় যোগ করা আর কখনো বাদ দেওয়া যাবে না।

### 10.3 Mean response time

```text
Mean response time = sum of measured response times / number of measured responses
```

The mean is useful, but it does not describe the complete distribution.

**বাংলায়:** Average একটি দরকারি সংখ্যা। কিন্তু সব user একই সময় অপেক্ষা করেছেন, এমন বোঝায় না।

### 10.4 p95 response time

A simple speaking definition is:

> p95 is a response-time threshold at or below which about 95 percent of measured replies finish.

If p95 is 500 ms, about 95% of measured replies finish within that time. Some replies can take much longer.

For finite datasets, percentile calculation methods can differ slightly. Use one documented method consistently across all runs.

**বাংলায়:** p95 যদি 500 ms হয়, measured reply-এর প্রায় ৯৫ শতাংশ ওই সময়ের মধ্যে শেষ হয়েছে। বাকি reply আরও দেরিতে আসতে পারে। Data analysis-এ একই percentile calculation method ব্যবহার করতে হবে।

### 10.5 Why the original “one very slow reply” sentence is wrong

Consider this illustrative dataset:

- 999 replies take 100 ms each.
- 1 reply takes 10,000 ms, or 10 seconds.

```text
Mean = (999 × 100 + 1 × 10,000) / 1,000
     = 109.9 ms

p95 = 100 ms
Maximum = 10,000 ms
```

The single extreme delay does not appear in p95. Therefore, p95 is not the maximum and does not guarantee that every slow reply is visible.

**বাংলায়:** এখানে একটি reply দশ সেকেন্ড নিয়েছে। কিন্তু p95 মাত্র 100 ms। তাই “একটি খুব ধীর reply লুকাতে পারবে না” বলা ভুল।

Use this sentence instead:

> We measure p95 to understand slower responses that the average alone may hide.

For deeper investigation, higher percentiles, maximum values, distributions, and individual logs can help. These are possible supplementary analyses, not all mandatory metrics already promised in the proposal.

### 10.6 Throughput

Throughput describes completed work per unit of time.

```text
Throughput = completed requests / measurement duration
```

The reporting convention must say whether “completed” means successful image-processing requests only or all terminal responses. Successful-request throughput plus separately reported failures is a clear approach, but the team must finalize the definition.

**বাংলায়:** প্রতি সেকেন্ডে কত request সফলভাবে শেষ হয়েছে, সেটি আলাদা করে দেখালে বোঝা সহজ হয়। Error response-কে throughput-এ কীভাবে ধরা হবে, সেটি স্পষ্ট করতে হবে।

### 10.7 Request rate versus throughput

Illustrative example:

```text
Client tries to send: 20 requests/second
System successfully completes: 15 requests/second
```

The difference may contribute to queued work or failures, depending on the run and queue limits.

These are not the proposal's selected rates.

**বাংলায়:** আসা কাজ আর শেষ হওয়া কাজ এক নয়। পাঠানোর rate বেশি কিন্তু শেষ করার rate কম হলে queue বাড়তে পারে বা request fail হতে পারে।

### 10.8 Failures and timeouts

A method can look fast if difficult requests fail and only easy successful ones remain in the latency sample.

Always report the latency sample definition together with failures, timeouts, and throughput. A missing response should not disappear from the report simply because it has no successful completion time.

**বাংলায়:** কঠিন request fail হয়ে গেলে শুধু সহজ request-এর latency দেখে method ভালো বলা যাবে না। Failure এবং timeout-ও দেখাতে হবে।

### 10.9 CPU and RAM

Measure relevant components separately where practical:

- Dispatcher VM or dispatcher process.
- Each worker.
- Load generator.
- Host resource pressure.

These observations help explain overhead and bottlenecks. CPU percentages must be interpreted with their measurement scope, sampling interval, and allocated capacity in mind.

**বাংলায়:** শুধু একটি মোট CPU number দেখে সব বোঝা যাবে না। কোন component কত resource ব্যবহার করছে, সেটি আলাদা করে বুঝতে হবে।

### 10.10 How to compare results responsibly

Recommended analysis practices, to be finalized before the main runs:

1. Compute the same metrics for every run.
2. Keep failed requests visible in the outcome summary.
3. Show variation across repetitions, not only a single best run.
4. Document whether a plotted percentile is per-run, pooled, or a summary of per-run percentiles.
5. Do not describe a tiny difference as a clear improvement without considering variability.
6. Keep latency, throughput, failures, and overhead together when deciding whether a method helps.

**বাংলায়:** শুধু সবচেয়ে ভালো graph নয়, repeated run-এর variation দেখাতে হবে। ছোট পার্থক্য noise-এর কারণে হয়েছে কি না বিবেচনা করতে হবে।

---

<a id="fairness"></a>
## 11. Fairness, repeatability, and limitations

### 11.1 What stays the same?

Within a matched scenario/rate comparison, keep these consistent:

- Worker application code.
- Image-processing operation and settings.
- Input image set and request schedule.
- Request rate.
- VM and scenario resource settings.
- Queue limits and processing-slot limits.
- Timeout and error-handling policies.
- Logging definitions and measurement boundaries.
- Health-check behavior, unless a documented method-specific component is being evaluated.

Only the routing policy and its necessary state handling should differ. Any method-specific probing or monitoring cost must be counted.

**বাংলায়:** Routing rule-এর প্রভাব জানতে অন্য বিষয়গুলো একই রাখতে হবে। Feedback-এর জন্য অতিরিক্ত probe লাগলে সেই খরচ লুকানো যাবে না।

### 11.2 Why the same dispatcher matters

Comparing four different server implementations could mix routing effects with differences in network code, logging, retries, or resource use.

One common forwarding path reduces those confounding differences. It does not eliminate every source of bias automatically.

**বাংলায়:** চারটি আলাদা system তুলনা করলে algorithm ছাড়াও code-এর পার্থক্যের প্রভাব আসতে পারে। একই forwarding path রাখলে সেই সমস্যা কমে।

### 11.3 Why no hidden retries?

A retry creates extra work and can change response time, throughput, and failure rates. If retries happen silently, the experiment no longer measures the workload the reader thinks it does.

**বাংলায়:** একটি request fail হলে চুপচাপ আবার পাঠানো হলে মোট কাজ বেড়ে যায়। তাই retry policy স্পষ্ট রাখতে হবে এবং proposal অনুযায়ী hidden retry থাকবে না।

### 11.4 Why local VMs are useful but limited

They provide a manageable environment for learning and comparison. However:

- Workers share physical resources.
- The virtual network differs from a real distributed network.
- Only two workers are tested.
- The dispatcher is a single central component.
- Image processing is one workload family.
- Results depend on the selected rates, images, quotas, and implementation.

**বাংলায়:** এই setup থেকে সব cloud, সব workload বা অনেক server-এর system সম্পর্কে সিদ্ধান্ত দেওয়া যাবে না। পরীক্ষার সীমা পরিষ্কার বলতে হবে।

### 11.5 Reproducible does not mean identical numbers everywhere

Another person should be able to repeat the procedure using the documented code, inputs, settings, and analysis steps.

Different hardware or software versions may produce different exact values. The goal is a transparent method and inspectable evidence, not identical numbers on every computer.

**বাংলায়:** Reproducible মানে অন্যরা একই পদ্ধতিতে পরীক্ষা করতে পারবেন। সব computer-এ একদম একই সংখ্যা আসবে, এমন নয়।

### 11.6 What to save

- Source code and version information.
- VM settings and software versions.
- Input image metadata and processing settings.
- Request schedules and repetition identifiers.
- Chosen rates, weights, quotas, and averaging settings.
- Probe, queue, and timeout policies.
- Raw request logs and resource measurements.
- Actual run order and reset procedure.
- Analysis scripts, plots, and known limitations.

This list expands the proposal's reproducibility goal into a practical checklist. It does not claim these artifacts already exist.

---

<a id="defense-questions"></a>
## 12. Proposal-defense questions and model answers

Use the English answers as short speaking models. Understand the Bangla meaning and adapt the answer to what the team has actually completed.

### Q1. What is your project about?

**English:** We will compare four ways of assigning image-processing requests to two workers. We want to find when recent processing-time feedback helps enough to justify its extra work.

**বাংলা:** দুটি worker-এর মধ্যে image-processing request ভাগ করার চারটি নিয়ম তুলনা করব। আগের processing time ব্যবহার করলে কখন যথেষ্ট সুবিধা পাওয়া যায়, সেটি জানতে চাই।

### Q2. Why is this a cloud-computing project if it runs locally?

**English:** It studies virtualization and load balancing, which are important cloud-computing concepts. Local VMs provide a controlled testbed, but they do not reproduce a full public cloud.

**বাংলা:** Virtualization এবং load balancing cloud computing-এর গুরুত্বপূর্ণ বিষয়। Local VM দিয়ে এগুলো পরীক্ষা করছি, পূর্ণ public cloud বানাচ্ছি না।

### Q3. Why not use AWS, Azure, or another public cloud?

**English:** We want to avoid paid services and keep the environment manageable within the project scope. Local VMs give us control over settings, and we will clearly state the limits of that choice.

**বাংলা:** Paid service এড়াতে এবং project-এর scope ছোট রাখতে local VM ব্যবহার করছি। Settings নিয়ন্ত্রণ করা সহজ হবে, তবে এই সিদ্ধান্তের সীমাবদ্ধতা report-এ বলব।

### Q4. What is new about the project?

**English:** We are not claiming a new algorithm. Our contribution is a reproducible implementation, a controlled comparison, and evidence about the conditions we test.

**বাংলা:** নতুন algorithm দাবি করছি না। একই setup-এ চারটি নিয়মের fair comparison এবং repeat করা যায় এমন evidence তৈরি করব।

### Q5. Are you implementing Prequal?

**English:** Not as a full reproduction. We cite Prequal as related work on performance-aware routing. Our proposal evaluates a simpler local rule and several baselines.

**বাংলা:** পুরো Prequal implement করছি না। Related work হিসেবে ব্যবহার করছি এবং ছোট local setup-এ সহজ feedback rule ও baseline তুলনা করছি।

### Q6. Why image processing?

**English:** It gives us real CPU work with controllable inputs. Image dimensions and processing settings can create different amounts of work, and the same inputs can be replayed.

**বাংলা:** Image processing-এ বাস্তব CPU কাজ হয়। Input ও settings নিয়ন্ত্রণ করে ছোট-বড় কাজ তৈরি করা যায় এবং একই input আবার চালানো যায়।

### Q7. Does a larger file always take longer to process?

**English:** Not always. Dimensions, format, content, and processing settings matter too. We will use a controlled dataset and measure actual processing times rather than assuming file bytes perfectly predict cost.

**বাংলা:** সবসময় নয়। Dimensions, format এবং settings-ও গুরুত্বপূর্ণ। তাই শুধু file size দেখে নিশ্চিত সময় বলব না; processing time মাপব।

### Q8. Why only two workers?

**English:** Two workers are enough for an initial comparison between routing choices, while keeping the project feasible in two months. The results will not establish large-scale scalability.

**বাংলা:** Routing choice তুলনা শুরু করার জন্য দুই worker যথেষ্ট। এতে সময় ও hardware-এর মধ্যে কাজ শেষ করা সম্ভব হবে। তবে বড় scale-এর দাবি করব না।

### Q9. Three VMs means three workers, correct?

**English:** No. There are two worker VMs and one dispatcher VM. The load generator runs on the physical host.

**বাংলা:** না। দুটি worker VM এবং একটি dispatcher VM। Load generator মূল host computer-এ চলবে।

### Q10. Are VMs on one computer a fair comparison?

**English:** They can support a limited controlled comparison if we keep conditions consistent and monitor shared-resource interference. They do not behave like fully independent physical servers.

**বাংলা:** শর্ত একই রেখে এবং shared resource-এর প্রভাব দেখে সীমিত comparison করা যায়। কিন্তু আলাদা physical server-এর পুরো আচরণ এতে পাওয়া যাবে না।

### Q11. Why build a dispatcher instead of configuring Nginx or HAProxy?

**English:** A small custom dispatcher lets us keep forwarding, logging, and request accounting consistent across all four rules. This helps isolate worker selection. We are not claiming it is better than production load balancers.

**বাংলা:** নিজের ছোট dispatcher-এ forwarding ও measurement একই রাখা যায়। এতে selection rule-এর প্রভাব বোঝা সহজ হয়। Production load balancer-এর চেয়ে ভালো দাবি করছি না।

### Q12. What is the difference between weighted round-robin and feedback?

**English:** Weighted round-robin uses fixed shares selected during calibration. Feedback uses recent timing and unfinished counts to make new decisions. Its decisions can change as those measurements change.

**বাংলা:** Weighted round-robin-এর অনুপাত আগে ঠিক করা থাকে। Feedback নতুন timing ও count অনুযায়ী সিদ্ধান্ত বদলাতে পারে।

### Q13. Why is queue length alone not enough?

**English:** Queue or unfinished-request counts treat a short job and a long job as one request each. They do not directly measure the amount of processing work remaining.

**বাংলা:** ছোট ও বড় request দুটিই count-এ এক। তাই সংখ্যা কম হলেই মোট কাজ কম, এমন নয়।

### Q14. What exactly does the feedback formula calculate?

**English:** It estimates delay as unfinished requests plus one, multiplied by recent average processing time. We select the available worker with the smaller estimate.

**বাংলা:** Unfinished request-এর সঙ্গে এক যোগ করে worker-এর recent average processing time দিয়ে গুণ করি। যার estimate কম, তাকে বেছে নিই।

### Q15. Why add one?

**English:** The new request is also work that must be processed. The plus one includes it in the estimate.

**বাংলা:** নতুন request-টিও কাজের তালিকায় যোগ হবে। তাই এক যোগ করা হচ্ছে।

### Q16. Is that estimate always correct?

**English:** No. It is a simple approximation. Job sizes vary, current work may be partly complete, and recent averages may become stale. Testing whether the estimate is useful is part of the project.

**বাংলা:** না। এটি আনুমানিক হিসাব। Job size, আংশিক শেষ হওয়া কাজ এবং পুরোনো average-এর কারণে ভুল হতে পারে। সেই estimate বাস্তবে সাহায্য করে কি না পরীক্ষা করব।

### Q17. Is the feedback rule AI or machine learning?

**English:** No. It uses counters, timing measurements, and arithmetic. There is no trained model in this proposal.

**বাংলা:** না। Count, সময় এবং সহজ হিসাব ব্যবহার করা হচ্ছে। কোনো trained AI model নেই।

### Q18. How will the rule start without previous timing data?

**English:** The proposal includes pilot calls to initialize each worker's timing estimate. We will define the initialization procedure before the main experiments.

**বাংলা:** শুরুতে pilot call দিয়ে worker-এর সময় সম্পর্কে ধারণা নেওয়া হবে। Exact procedure মূল পরীক্ষার আগে নির্ধারণ করব।

### Q19. What if a worker stays idle and its timing information becomes old?

**English:** We plan to probe idle workers periodically. The probe policy and its overhead will need to be documented and measured.

**বাংলা:** Idle worker-কে মাঝে মাঝে probe দিয়ে নতুন তথ্য নেওয়া হবে। Probe-এর নিয়ম এবং অতিরিক্ত কাজও document করতে হবে।

### Q20. How will you slow one worker?

**English:** We plan to use a Linux CPU quota to restrict CPU time available to its worker service. The exact quota and application procedure will be selected and recorded before the main runs.

**বাংলা:** Linux CPU quota দিয়ে worker service-এর CPU time সীমিত করব। Exact quota এবং সেটি কীভাবে দেওয়া হবে, তা আগে ঠিক করে record করব।

### Q21. Does that prove adaptation to sudden speed changes?

**English:** Not by itself. A fixed slowed-worker scenario tests unequal capacity. To measure adaptation to a sudden slowdown or recovery, we would need a defined change-over-time experiment.

**বাংলা:** শুধু fixed slow worker দিয়ে sudden change-এর adaptation প্রমাণ হয় না। Run-এর মাঝে slowdown বা recovery দিয়ে আলাদা test করতে হবে।

### Q22. How many tests will you run?

**English:** The minimum main matrix is four rules, three scenarios, three rates, and five repetitions: 180 runs. Each run contains many requests, and pilot runs are additional.

**বাংলা:** মূল matrix-এ কমপক্ষে ১৮০টি run হবে। প্রতিটি run-এ অনেক request থাকবে। Pilot আলাদা।

### Q23. Why five repetitions?

**English:** Repetitions let us observe run-to-run variation. Five is our planned minimum, not a guarantee of statistical certainty. We may need more if the variation is large.

**বাংলা:** Run-এর variation দেখতে repeat করা হবে। পাঁচটি minimum plan; variation বেশি হলে আরও লাগতে পারে।

### Q24. What are the exact request rates?

**English:** They are not finalized in the proposal. We will use the pilot to choose meaningful rates and then apply the same rates across methods for each matched condition.

**বাংলা:** এখনো final করা হয়নি। Pilot-এ rate ঠিক করে একই condition-এ সব method-এর জন্য একই রাখা হবে।

### Q25. What is p95, and why use it?

**English:** It is a threshold at or below which about 95 percent of measured replies finish. It helps describe slower responses beyond what the mean alone shows. It is not the worst response time.

**বাংলা:** প্রায় ৯৫ শতাংশ reply যে সময়ের মধ্যে শেষ হয়, সেটি বোঝায়। Average-এর বাইরে ধীর response বোঝাতে সাহায্য করে। এটি সবচেয়ে বেশি সময় নয়।

### Q26. What is the difference between latency and throughput?

**English:** Latency is how long a request waits for its response. Throughput is how many requests finish per second. A system can have high throughput while some requests still wait a long time.

**বাংলা:** Latency হলো একটি request-এর সময়। Throughput হলো প্রতি সেকেন্ডে কত request শেষ হয়। Throughput বেশি হলেও কিছু request-এর delay বেশি হতে পারে।

### Q27. What happens if a worker fails?

**English:** The design includes health checks and timeouts. Unavailable workers should not receive new requests, and failed or timed-out work will be logged without hidden retries. Detailed cancellation and accounting behavior must be tested.

**বাংলা:** Health check ও timeout থাকবে। অচল worker-কে নতুন request দেওয়া হবে না। Failure log হবে, লুকানো retry হবে না। Timeout-এর পরে count ঠিক থাকে কি না, সেটিও test করতে হবে।

### Q28. How do you keep the experiments fair?

**English:** We keep code, inputs, rates, resource settings, timeouts, and measurement definitions consistent. We disable output caching, reset state, vary run order, and repeat runs.

**বাংলা:** Code, input, rate, resource, timeout এবং measurement একই রাখব। Cache বন্ধ, state reset, run order পরিবর্তন এবং repeated run থাকবে।

### Q29. What if the dispatcher or client is the bottleneck?

**English:** The pilot will check those components, and we will monitor resource use and planned versus achieved sending rates. If the experiment is limited by the wrong component, we must address or disclose it before interpreting routing differences.

**বাংলা:** Pilot-এ client ও dispatcher check করব। অন্য component bottleneck হলে routing algorithm-কে দায়ী করা যাবে না। সমস্যা সমাধান করতে হবে বা স্পষ্টভাবে জানাতে হবে।

### Q30. What if feedback performs worse?

**English:** That is a valid finding. Its estimate may be inaccurate or its overhead may not be worthwhile. We will report where it helps and where it does not.

**বাংলা:** এটিও valid result। Estimate ভুল বা overhead বেশি হতে পারে। ভালো ও খারাপ—দুই অবস্থাই জানাব।

### Q31. What if all four methods look the same?

**English:** We will examine variation, offered load, and bottlenecks before concluding. If no clear difference remains, we will say that we did not observe a clear advantage under those conditions, not that all methods are universally equivalent.

**বাংলা:** আগে variation, load এবং bottleneck দেখব। তারপর বলব আমাদের condition-এ স্পষ্ট সুবিধা পাওয়া যায়নি। সব জায়গায় একই, এমন দাবি করব না।

### Q32. How will you judge whether feedback is worthwhile?

**English:** We will consider response time together with throughput, failures, and resource overhead. A latency improvement is less useful if it comes from dropped work or excessive overhead.

**বাংলা:** শুধু latency নয়, throughput, failure এবং resource cost-ও দেখব। কাজ বাদ দিয়ে দ্রুত result দেখালে সেটি ভালো নয়।

### Q33. What makes the work reproducible?

**English:** We will provide code, inputs or input-generation details, settings, schedules, raw logs, and analysis steps. Others should be able to repeat the procedure and inspect how conclusions were reached.

**বাংলা:** Code, input details, settings, schedule, log ও analysis দিলে অন্যরা পরীক্ষা repeat করতে এবং conclusion যাচাই করতে পারবেন।

### Q34. Are you claiming cost savings or energy savings?

**English:** No. We are avoiding paid cloud services, but we are not measuring or claiming total cost or energy savings. The experiment uses existing hardware and electricity.

**বাংলা:** না। Paid cloud ব্যবহার করছি না, কিন্তু মোট খরচ বা energy saving মেপে দাবি করছি না।

### Q35. What if you are asked for a setting you have not finalized?

**English:** That parameter is not finalized in the proposal. We will define it before the main experiments, use the pilot where appropriate, and keep the comparison consistent.

**বাংলা:** Parameter এখনো final করা হয়নি। মূল পরীক্ষার আগে ঠিক করব এবং তুলনার সময় consistent রাখব।

### Q36. What is the biggest limitation?

**English:** All components share one physical host, and we test only two workers with one workload family. Our results therefore describe this small setup, not general public-cloud performance.

**বাংলা:** সব component একই host-এ এবং মাত্র দুই worker নিয়ে একটি workload family পরীক্ষা করছি। তাই ফলাফল এই ছোট setup-এর মধ্যে সীমিত।

---

<a id="speech-corrections"></a>
## 13. Corrections and safer wording for the speech

| Original or tempting wording | Why it needs care | Safer wording |
|---|---|---|
| “p95 means one very slow reply cannot hide.” | p95 can miss a single extreme delay. | “p95 helps describe slower responses that the average alone may hide.” |
| “We have three workers.” | The third VM is the dispatcher. | “We have two workers and one dispatcher.” |
| “Least unfinished picks the smaller queue.” | This can be misunderstood as waiting requests only. | “It picks fewer unfinished requests, including running and waiting work.” |
| “Every request uses a fixed image.” | Could imply that all requests are identical. | “Requests use a fixed, controlled image set and schedule.” |
| “Feedback knows the worker's true speed.” | Processing time also depends on the jobs the worker receives. | “Feedback uses recent average processing time as an imperfect signal.” |
| “The formula predicts the exact completion time.” | It ignores several details of queued and running jobs. | “The formula gives a rough delay estimate.” |
| “We check every worker's speed before every request.” | Could imply a fresh synchronous probe for every routing decision. | “We use recent measurements and refresh information according to a defined probe policy.” |
| “One slot per worker makes the test fair.” | Other controls are necessary too. | “One slot simplifies comparison; we also keep inputs, settings, and measurement policies consistent.” |
| “Feedback will be the best.” | No results exist yet. | “We will test whether feedback helps and under which conditions.” |
| “The project has no cost.” | Hardware and electricity still have costs. | “The project does not require paid cloud services or paid APIs.” |
| “Our findings apply to cloud systems.” | Too broad for one host and two workers. | “Our findings apply to the tested local setup and conditions.” |
| “We implement Prequal.” | The proposal describes a simpler rule, not a full reproduction. | “Prequal is related work motivating our comparison.” |
| “A slowed worker proves dynamic adaptation.” | A fixed quota does not establish recovery or adaptation time. | “It tests unequal capacity; dynamic adaptation needs a separately defined experiment.” |
| “Five runs prove the result.” | Repetitions do not automatically ensure certainty. | “Repeated runs help us quantify variation and avoid relying on one result.” |
| “No difference means the methods are equal.” | A limited test may fail to reveal a real difference. | “We did not observe a clear advantage under the tested conditions.” |

### Proposal tense

Prefer:

- We will build.
- We plan to measure.
- We will compare.
- The pilot will help us select.
- We will report the results.

Avoid unless supported by completed work:

- We proved.
- Our experiment showed.
- Our algorithm reduced latency.
- The feedback rule is faster.

**বাংলায়:** Proposal-এ future plan বোঝাতে “করব” বলবেন। Experiment না করে “প্রমাণ করেছি” বা “ফলাফলে দেখা গেছে” বলবেন না।

---

<a id="open-decisions"></a>
## 14. Details that still need to be finalized

The proposal defines a direction, not every implementation parameter. The following items should not be invented during Q&A.

| Item | What the documents establish | What still needs a precise decision |
|---|---|---|
| Request rates | Three rates, selected in the pilot. | Exact values and how they are selected for each scenario. |
| Run duration | Repeated experimental runs. | Measurement duration, warm-up duration, and drain policy. |
| Image set | Controlled uniform and mixed workloads. | Dimensions, formats, counts, mixture proportions, and exact processing settings. |
| Weighted round-robin | Fixed weights after calibration. | Calibration condition, ratio selection, and exact scheduling variant. |
| Recent average | Recent average processing time. | Averaging method, window or smoothing parameter, and sample inclusion rules. |
| Slow worker | Linux CPU quota. | Exact quota, application procedure, and whether it changes during a run. |
| Worker queue | A limited queue and one processing slot. | Queue capacity, rejection behavior, and accounting boundaries. |
| Probes | Periodic checks of idle workers. | Probe content, frequency, cost accounting, and interaction with health checks. |
| Timeouts | Defined timeouts and no hidden retries. | Values, cancellation behavior, and treatment of worker work that continues after timeout. |
| Latency reporting | Mean and p95. | Which outcomes enter each sample and the percentile calculation method. |
| Throughput | Completed requests per second. | Success-only versus all-terminal-response reporting and the measurement interval. |
| Resource monitoring | CPU and RAM use. | Sampling frequency, process/VM/host scope, and overhead measurement. |
| Reset | Reset between runs. | Exactly what state is reset and how outstanding work is handled. |
| Analysis | Compare repeated measurements. | Variation summaries, uncertainty reporting, and decision criteria for a meaningful benefit. |

### A strong answer when a detail is not final

> That detail is not finalized in the proposal. We will specify it before the main experiments and apply it consistently. We will not choose it afterward just to make one method look better.

**বাংলায়:** এই বিষয়টি এখনো final হয়নি। মূল পরীক্ষার আগে ঠিক করব এবং consistent রাখব। ফলাফল দেখার পরে কোনো method-কে ভালো দেখানোর জন্য settings বদলাব না।

### What not to do

Do not give a made-up request rate, quota percentage, moving-average window, or latency improvement simply to sound confident. Being precise about what is planned and what is unknown is part of a good defense.

---

<a id="rehearsal"></a>
## 15. Presentation timing and rehearsal

### 15.1 Suggested 10-minute allocation

This is a rehearsal target based on the supplied guide, updated to the latest member assignments. It is not a measurement of how long the scripts above take to read.

| Slide | Presenter | Suggested time |
|---|---|---:|
| 1 — Title | Mahim | 30 seconds |
| 2 — Motivation | Mahim | 90 seconds |
| 3 — Research problem | Mahim | 90 seconds |
| 4 — Objectives | Ikramul | 60 seconds |
| 5 — Four rules | Ikramul | 60 seconds |
| 6 — Request flow | Ikramul | 90 seconds |
| 7 — Test plan | Omlan | 90 seconds |
| 8 — Contributions | Omlan | 60 seconds |
| 9 — References | Backup | No main-talk time |
| 10 — Ending | Omlan | 30 seconds |
| **Total** | **All presenters** | **600 seconds / 10 minutes** |

The presentation guide specifies a further **3 minutes of Q&A**.

The suggested scripts are intentionally concise. Use diagram explanations and one relevant example to fill the target time naturally. Do not stretch a short paragraph by speaking unnaturally slowly.

**বাংলায়:** Speech ছোট রাখা হয়েছে যাতে বুঝে বলা যায়। প্রয়োজন হলে diagram ব্যাখ্যা এবং একটি example যোগ করুন। শুধু সময় পূরণ করতে একই কথা বারবার বলবেন না।

### 15.2 Each person's job

#### Mahim: explain why the project matters

```text
Slide 1 → What are we building?
Slide 2 → Why can simple turn-taking be insufficient?
Slide 3 → What question will our experiment answer?
```

Priority knowledge:

- Two workers, one dispatcher.
- Equal count versus equal work.
- Research question and overhead.
- No new-algorithm claim.

#### Ikramul: explain how the system works

```text
Slide 4 → What will we complete?
Slide 5 → How do the four rules choose a worker?
Slide 6 → What happens to one request?
```

Priority knowledge:

- The feedback formula and the plus one.
- Fixed weights versus recent feedback.
- Running plus waiting requests.
- Processing time versus total response time.
- One request goes to one selected worker.

#### Omlan: explain how the team will evaluate it

```text
Slide 7 → How will we test fairly?
Slide 8 → What will we deliver and claim?
Slide 10 → What is the one-line takeaway?
```

Priority knowledge:

- 4 × 3 × 3 × 5 = 180 minimum main runs.
- p95, throughput, failures, and resource use.
- Fairness controls and shared-host limitations.
- No guaranteed winner.
- Slide 9 is backup.

### 15.3 A useful speaking structure for every slide

1. State the main idea.
2. Explain the diagram or a small example.
3. Say the takeaway.
4. Move to the next slide or presenter.

Example for slide 2:

> Equal request counts do not mean equal work. Three large images can need more processing than three small images. So we need to compare how different rules handle unequal work.

**বাংলায়:** প্রথমে মূল কথা, তারপর example, তারপর conclusion। এভাবে বললে বাক্য ভুলে গেলেও বক্তব্যের flow থাকবে।

### 15.4 Practice the handoffs

Mahim to Ikramul:

> Now Ikramul will explain what we will build.

Ikramul to Omlan:

> That is how the system works. Now Omlan will explain the test plan and expected outputs.

Omlan to Q&A:

> Thank you. We are happy to take your questions.

Pause after a handoff. Do not continue speaking over the next person.

### 15.5 Two complete rehearsals

#### Rehearsal 1 — Understanding and flow

- Use the actual deck.
- Explain each slide without reading the guide word for word.
- Note where explanations become confusing.
- Check the slide 8 → slide 10 navigation.
- Practice the feedback example and p95 definition separately.

#### Rehearsal 2 — Timing and delivery

- Use a timer.
- Include handoffs and slide changes.
- Aim for the required total time.
- Remove repeated sentences if the talk is too long.
- Add a useful example if it is too short.
- Test visibility on the actual display or projector if possible.

### 15.6 How to answer a defense question

Use this three-part pattern:

1. **Direct answer:** Answer the question first.
2. **Reason:** Give one clear explanation.
3. **Boundary:** State the limitation or what still needs testing.

Example:

> No, we are not claiming a new algorithm. Our contribution is a controlled comparison of known ideas. The results will be limited to our tested local setup.

**বাংলায়:** আগে সরাসরি উত্তর দিন। তারপর কারণ দিন। শেষে প্রয়োজন হলে সীমাবদ্ধতা বলুন। প্রশ্নের উত্তর না দিয়ে অনেক tool-এর নাম বলা ঠিক নয়।

### 15.7 If you do not know

Use one of these honest responses:

> We have not measured that yet. We will test it rather than assume the result.

> That parameter is not finalized. We will define it before the main experiments.

> That would require a separate experiment, so we cannot claim it from the current plan.

**বাংলায়:** না জানা মানেই defense খারাপ নয়। কী জানা আছে, কী এখনো মাপা হয়নি এবং কীভাবে পরীক্ষা করবেন, সেটি পরিষ্কার বলতে পারা গুরুত্বপূর্ণ।

---

<a id="self-practice"></a>
## 16. Optional self-practice

Use this only when you are ready to practice. Cover the answer key and answer aloud in your own words.

### Practice prompts

1. Explain the whole project without using more than five technical terms.
2. Why are there three VMs but only two workers?
3. Give an example where equal request counts mean unequal work.
4. Explain the difference between weighted round-robin and feedback.
5. What does “unfinished” include?
6. Why does the feedback formula add one?
7. Worker A has two unfinished requests and a 100 ms recent average. Worker B has none and a 500 ms recent average. Which worker does feedback choose, and why?
8. If A instead has nine unfinished requests, what changes?
9. Can p95 miss one extremely slow request?
10. What is the difference between request rate and throughput?
11. Why do we need repeated runs and varied run order?
12. What will you say if feedback does not win?
13. What is one limitation of running both workers on the same host?
14. What should you say if asked for an exact rate or quota that is not finalized?
15. What is the project contribution if no new algorithm is invented?

### Answer key

1. Compare ways of distributing photo-processing work and measure which works better under defined conditions.
2. Two VMs process images; the third chooses where requests go.
3. Three short jobs versus three long jobs: equal count, different total work.
4. Fixed calibrated shares versus decisions using recent timing and unfinished counts.
5. Assigned work that is running or waiting and has not finished.
6. The incoming request adds one more job.
7. A: 300 ms estimated delay versus B: 500 ms.
8. A becomes 1,000 ms, so feedback chooses B at 500 ms.
9. Yes. p95 is not the maximum response time.
10. Incoming work per second versus completed work per second.
11. To observe variation and reduce systematic order effects.
12. Report it honestly and examine the conditions, estimates, overhead, and uncertainty.
13. Shared CPU, memory, network, or host activity can influence both workers.
14. Explain that the parameter will be defined before the main experiments, with the pilot where appropriate.
15. A working reproducible testbed, fair comparison, raw evidence, and measured guidance.

### বাংলা practice tip

প্রথমে বাংলায় নিজের ভাষায় উত্তর দিন। তারপর একই ধারণা দুই বা তিনটি ছোট English sentence-এ বলুন। বাংলা থেকে প্রতিটি শব্দ সরাসরি translate করার দরকার নেই। মূল অর্থ ঠিক থাকাই গুরুত্বপূর্ণ।

---

<a id="revision-sheet"></a>
## 17. Last-minute revision sheet

### The project

> Compare four routing rules for two image-processing workers on a local VM testbed.

**বাংলা:** Local VM setup-এ দুটি worker-এর জন্য চারটি request ভাগ করার নিয়ম তুলনা।

### The problem

> Equal request counts do not mean equal work.

**বাংলা:** Request-এর সংখ্যা সমান মানেই কাজ সমান নয়।

### The architecture

```text
Host load generator → dispatcher VM → worker A or worker B → response
                                             ↓
                                  logs and resource data
                                             ↓
                                      analysis and plots
```

### The four rules

| Rule | Remember |
|---|---|
| Round-robin | Take turns. |
| Weighted round-robin | Use fixed shares. |
| Least unfinished | Choose fewer unfinished requests. |
| Feedback | Combine unfinished count and recent processing time. |

### The formula

```text
(unfinished + 1) × recent average processing time
```

- Plus one means the new request.
- Choose the smaller estimate.
- It is an estimate, not a guarantee.
- It does not directly predict the exact cost of the new image.

### The experiment

```text
4 rules × 3 scenarios × 3 rates × 5 repetitions = 180 minimum main runs
```

### The metrics

- Mean response time.
- p95 response time.
- Throughput.
- Failures and timeouts.
- CPU and RAM.

### The fairness controls

- Same code and inputs.
- Same matched rates and resource conditions.
- Same measurement and timeout policies.
- Output caching disabled.
- State reset between runs.
- Varied run order.
- Repeated runs.
- Bottleneck checks.

### The limits

- One physical host.
- Two workers.
- One workload family.
- No claim about all public clouds.
- No new-algorithm claim.
- No guaranteed feedback victory.
- No measured cost or energy savings.

### The three most important corrections

1. **Two workers and one dispatcher, not three workers.**
2. **p95 is not the worst response time and can miss an isolated extreme delay.**
3. **Use proposal language: “we will test,” not “we proved.”**

### Final takeaway

> **We are not trying to prove that a complicated rule must win. We are trying to find out when additional performance information is useful.**

**বাংলায়:** জটিল নিয়মকে জেতানো আমাদের উদ্দেশ্য নয়। অতিরিক্ত performance information কখন সত্যিই কাজে লাগে, সেটি খুঁজে বের করাই উদ্দেশ্য।

---

<a id="sources"></a>
## 18. Source documents and scope of this guide

### Primary materials

1. [Cloud Load Balancing Proposal](./Cloud_Load_Balancing_Proposal.pdf)
   - Page 1: project purpose, four methods, objectives, and research position.
   - Page 2: starting resources, software roles, feedback formula, startup behavior, and boundaries.
   - Page 3: scenarios, experiment matrix, fairness controls, schedule, and deliverables.
2. [Cloud Load Balancing Presentation Guide](./Cloud_Load_Balancing_Presentation_Guide.pdf)
   - Pages 1–3: suggested slide structure and timing.
   - Pages 4–5: defense questions, limitations, rehearsal guidance, and preliminary references.
3. [Performance-Aware Load Balancing — actual slide deck](./Performance-Aware%20Load%20Balancing.pptx)
   - Ten slides, with references on slide 9 and the ending on slide 10.
4. The team's latest supplied speech, which assigns slides 1–3 to Mahim, slides 4–6 to Ikramul, and slides 7, 8, and 10 to Omlan.

### How conflicting details were handled

- The **actual deck** determines the slide order.
- The **latest supplied speech** determines speaker assignments.
- The **proposal** supplies the technical plan and its limits.
- Teaching examples and recommended implementation checks are labeled as such; they are not presented as measured results or completed code.
- The explanation corrects the original p95 wording and distinguishes a fixed slowed-worker scenario from an unfinalized dynamic-adaptation experiment.

### What was not done for this guide

- No experiments were run.
- No implementation was audited or verified.
- Hardware capacity was not remeasured.
- Referenced research papers were not independently reviewed here.
- The original PDF, slide deck, and speech files were not modified.

This Markdown file is a study and rehearsal companion to the supplied proposal materials.
