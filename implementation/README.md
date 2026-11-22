# Implementation workspace

The planned system, per the proposal: one dispatcher VM (1 GB RAM, 1 vCPU) and two worker VMs (2 GB RAM, 1 vCPU each), all Ubuntu Server, running locally. Workers process image resize and recompression jobs. The dispatcher picks a worker by one of four rules: round-robin, weighted round-robin, least unfinished requests (least connections counted in requests), or recent processing time feedback.

The build follows [spec.md](spec.md) and the order in [ORCHESTRATION.md](ORCHESTRATION.md).

## Layout

- `plb/`: the shared package. Config loading and checks (`plb.config`), the header names and outcome values every part uses (`plb.protocol`), the column names of the worker, dispatcher, and generator logs (`plb.rows`), the seeded image set generator (`plb.images`), and the per-run summary (`plb.summary`).
- `worker/`: the image processing service. Built.
- `dispatcher/`: routing rules and the forwarding path. Built.
- `experiments/`: the load generator, the sampler, and the orchestrator with its local backend are built. The SSH backend and the pilot tools are not built yet. The per-run summary lives in `plb.summary`.
- `setup/`: VM setup guide, systemd units, and scripts. Not built yet.
- `config/dev.toml`: development values for localhost. They are not pilot results.
- `tests/`: the test suite.

## Setting up

Use Python 3.12, the version Ubuntu 24.04 ships. From this folder:

```bash
python3.12 -m venv .venv
. .venv/bin/activate          # Windows (Git Bash): . .venv/Scripts/activate
pip install -r requirements.txt
pip install -e . --no-deps
python -m pytest
```

Every package in `requirements.txt` is pinned with `==`, so the host and every VM get the same versions.

## Config

One TOML file holds every tunable value. `plb.config.load_config` reads it and refuses keys it doesn't know. A key missing from the file loads as `None`, which the `pilot` stage allows. With `stage = "main"`, loading fails if any key is still unset, if the config file itself is not committed, or if tracked files in the git working tree have uncommitted changes. Other untracked files, such as run outputs, are ignored. `config_hash` gives the SHA-256 of the file bytes and `git_commit` gives the commit id; both go into each run's metadata.

TOML files are checked out with LF line endings on every OS (see `.gitattributes`), so the same commit gives the same config hash on Windows and Linux.

## Image set

```bash
python -m plb.images --config config/dev.toml --out local/images
```

This writes `per_class` synthetic JPEGs for each size class: `local/images/<class>/<class>-<NN>.jpg`. The file name without `.jpg` is the image id. Each image is a colour gradient with random shapes and blended noise. The seed comes from `seeds.image_set` (or `--seed`). The same seed and the same Pillow version give byte-identical files. `local/` is ignored by git. The dispatcher and load generator can skip the files: `plb.images.generate_image` and `generate_image_set` give the same bytes in memory.

## Worker

```bash
python -m worker --config config/dev.toml --port 8101
```

Add `--host 0.0.0.0` on a VM. The queue capacity comes from `worker.queue_capacity`.

- `POST /process` takes JPEG bytes. The worker decodes the image, resizes it to half width and height with LANCZOS, and encodes it as JPEG quality 80. Only that work is timed. The reply is 200 with the JPEG and the headers `X-Outcome: done`, `X-Processing-Ms`, and `X-Output-Bytes`.
- One request is processed at a time, and up to `queue_capacity` more wait in the queue. When the queue is full, the reply is 503 with `X-Outcome: rejected` at once.
- `X-Budget-Ms` is the time budget from arrival. If it has passed by the time a queued request would start, the reply is 504 with `X-Outcome: expired` and no image work is done. A request without the header never expires. A header that isn't a number gets 400 with `X-Outcome: error`.
- A body Pillow can't decode gets 500 with `X-Outcome: error`. The worker keeps serving other requests.
- `GET /health` does no image work.
- `POST /admin/flush` with `{"path": "<csv file>"}` writes the per-request log (`request_id, arrival_unix_s, queue_wait_ms, processing_ms, outcome`). The worker also writes it to `--log` (default `local/worker-<port>.csv`) when it shuts down cleanly.

Nothing is cached, so two identical requests cost the same work.

## Dispatcher

```bash
python -m dispatcher --config config/dev.toml --rule rr --scenario 1 --rate 2 --run-id manual --port 8100
```

`--rule` is `rr`, `wrr`, `lur` (least unfinished requests), or `feedback`. Add `--host 0.0.0.0` on a VM. The workers in `addresses.workers` are called w1 and w2, in that order.

- `POST /process` reads the whole body, picks a worker, and forwards the request with `X-Budget-Ms` set to the dispatcher timeout D. The reply carries the worker's body and `X-Outcome`, `X-Chosen-Worker`, and `X-Processing-Ms`.
- Outcomes: a worker 200 is `success`, a worker 503 is passed back as `rejected`, and a worker 504 `expired` as `expired`. No reply within D gives 504 `timeout`, and a connection error or any other reply gives 502 `error`. Nothing is retried.
- `GET /health` answers 503 until warm-up has succeeded, then 200.
- `GET /admin/cpu` returns the dispatcher's process CPU time in seconds.
- `POST /admin/flush` with `{"path": "<csv file>"}` writes the log, one row per request, warm-up request, and probe, with the columns in `plb.rows.DISPATCHER_LOG_COLUMNS`. The dispatcher also writes it to `--log` (default `local/dispatcher-<port>.csv`) when it shuts down cleanly.

The rules, the EWMA estimate, warm-up, and probes follow the "Dispatcher" section of [spec.md](spec.md). On a tie, every rule picks the worker it did not pick last time, and the first tie goes to w1.

Under the feedback rule, probes start only after the first client request has reached `/process`. Warm-up requests don't count. So idle workers are not probed, and their estimates don't move, while a run is still being set up.

## Load generator and summary

```bash
python -m experiments.loadgen --config config/dev.toml --target http://127.0.0.1:8101/process \
    --scenario 2 --rate 2 --round 1 --rule rr --run-id manual --out local/run-manual
python -m plb.summary --run-dir local/run-manual
```

The target takes the same POST as the worker's `/process`, so a worker can stand in for the dispatcher during manual checks.

- The schedule is Poisson arrivals (exponential gaps) at `--rate` over `run.length_s`, with an image per request. Scenario 1 uses only medium images; scenarios 2 and 3 pick the class from `images.mix`. The seed is a string made from `seeds.schedule`, the scenario, the rate, and the round. The rule is not part of it, so every rule in one round, scenario, and rate gets the same schedule.
- Sending is open loop. Each request has its own asyncio task that sends at the planned time whether or not earlier replies have come back, and the HTTPX client has no connection limit. With `generator.spin_wait` on, a task sleeps until 20 ms before its planned time and then busy-waits.
- Each request carries `X-Request-Id`, `X-Image-Id`, and `X-Size-Class`, with the image bytes as the body. The images are drawn in memory from `seeds.image_set`.
- A request with no reply within `generator.timeout_ms` is a timeout. The run ends when every request has an outcome. A 200 is success, 503 is rejected, 504 with `X-Outcome: expired` is expired, any other 504 is timeout, and any other status or a connection error is error.
- Response time is the time the reply arrived (or the timeout fired) minus the planned send time. Send lag is the actual send time minus the planned one.
- `--rate` must be above 0.
- `--run-length <s>` replaces `run.length_s` for a short pilot or development run, and W shrinks by the same share. With `config/dev.toml` (30 s, W 5 s), `--run-length 5` gives W ≈ 0.833 s. A `main` stage config refuses the flag.

The run folder gets three files from the generator. `schedule.csv` (`request_id, planned_offset_s, image_id, size_class`) is written before sending, and the same seed always gives the same bytes. `generator.csv` has one row per request with the columns in `plb.rows.GENERATOR_LOG_COLUMNS`. Chosen worker, processing time, and output size come from the reply headers and stay empty when the reply has none. `loadgen.json` holds the run parameters: run id, rule, scenario, rate, round, target, the run length and dropped window actually used, tolerance, and the schedule seed.

`plb.summary` reads `generator.csv` and `loadgen.json`, plus `dispatcher.csv` and `metadata.json` when the run folder has them, and writes `summary.json`. The measured window is every request planned at or after the dropped window W from `loadgen.json`, and its length is the run length minus W. A W as long as the run or longer is an error.

- `measured` and `successes` count requests in the measured window.
- `mean_ms` and `p95_ms` cover successful requests only. p95 is the nearest rank: sort, then take the value at position ceil(0.95 × n).
- `p95_by_class_ms` gives p95 for small, medium, and large in scenarios 2 and 3, and is null in scenario 1.
- `throughput` is successes divided by the window length, shown next to `offered_rate`, the run's `--rate`.
- `failures` counts rejected, expired, timeout, and error.
- `planned_rate` counts requests planned in the window and `achieved_rate` counts requests actually sent in the window, both divided by its length. `rate_flag` is true when the two differ by more than `run.achieved_rate_tolerance` of the planned rate. Comparing with the schedule instead of the offered rate means the random spread of a Poisson schedule never sets the flag. The flag is also true when nothing was planned in the window.
- `max_send_lag_ms` is the largest send lag in the window.
- `mean_select_ns` is the mean `select_ns` over the dispatcher rows of measured requests, without warm-up requests and probes.
- `probe_count` counts the probe rows in the dispatcher log.
- `dispatcher_cpu_s` is the dispatcher CPU time at the end of the run minus the time at the start, from `metadata.json`.
- `throttling` gives, for each worker, the change in each cpu.stat counter (`nr_periods`, `nr_throttled`, `throttled_usec`). It is null when `cpu_stat` in `metadata.json` is `"unsupported"`, as on the local backend.

Response times come only from `generator.csv`, so warm-up and probe rows never enter them. A value that can't be computed, such as p95 with no successes, is null. Without `dispatcher.csv` or `metadata.json`, as in a run sent straight to a worker, the fields that need them are null too.

The resource sampler writes one CSV row per interval:

```bash
python -m experiments.sampler --out local/sampler-host.csv --interval 1 --pid <service pid>
```

The columns are `timestamp_unix_s, cpu_total_percent, cpu_process_percent, ram_used_mb`. `cpu_process_percent` is the `--pid` process's CPU as a percent of one CPU, as psutil gives it, and stays empty without `--pid`. Every row is flushed at once, so a killed sampler keeps the rows it wrote. It runs until it is killed, or stops by itself when the `--pid` process ends.

## Orchestrator

```bash
python -m experiments.orchestrate run --backend local --config config/dev.toml \
    --scenario 2 --rule feedback --rate 2 --round 0 --results local/results
python -m experiments.orchestrate round --backend local --config config/dev.toml \
    --round 1 --run-length 5 --results local/results
python -m experiments.orchestrate throw-out --run-id r1-s2-feedback-2-a1 \
    --reason "..." --results local/results
```

`--results` defaults to `../results`, relative to this folder. Runs on a laptop should use `--results local/results`, so they never land in `results/` and can't be mistaken for measurements. `--run-length` shortens the run and is refused in the main stage. The config is loaded before any backend starts, so a main stage config with an unset value or a dirty working tree is refused before any service runs.

The local backend starts every service as a process on this machine with the ports from `config.addresses`. It has no cgroups, so the quota and cpu.stat operations return `unsupported`, and metadata.json records them that way. The backends are listed in `experiments/backends.py`.

One run follows the steps of "Orchestrator" in [spec.md](spec.md):

1. Write a `started` row to the ledger.
2. In scenario 3, apply the quota from `[quota]` to w2 and read it back. In scenarios 1 and 2, clear it.
3. Restart w1 and w2 and wait for their health checks, then restart the dispatcher with the run's rule, scenario, rate, and run id and wait for its health check, which passes only after warm-up. A failed warm-up fails the run at once.
4. Read cpu.stat on both workers and the dispatcher CPU time, then start the samplers for the host, the dispatcher, and both workers.
5. Run `python -m experiments.loadgen` against the dispatcher. A non-zero exit fails the run.
6. Read cpu.stat and the dispatcher CPU time again, stop the samplers, and have the dispatcher and both workers write their logs into the run folder.
7. Write metadata.json (commit, config hash, seeds, quota, cpu.stat, dispatcher CPU time at start and end, time of each step) and summary.json.
8. Write a `finished` row. Any error in steps 2 to 7 writes `failed` with the error text instead. The backend stops every service and sampler in either case.

The ledger is `<results>/ledger.csv`. Rows are only ever appended. Its columns are `timestamp_unix_s, stage, round, scenario, rule, rate, attempt, run_id, status, reason`, and status is `started`, `finished`, `failed`, or `thrown_out`. The run id is `r<round>-s<scenario>-<rule>-<rate>-a<attempt>`, such as `r1-s2-feedback-2-a1`. Each attempt gets its own run id, also one cut off by Ctrl+C.

A round is every scenario with its three rates from `[rates]`, times the four rules: 36 conditions. They are shuffled with the seed `"<seeds.round_order>:<round>"`, and the seed and order are saved to `round-<n>-order.json` before the first run. Conditions the ledger already marks finished in that stage and round are skipped, so a round stopped with Ctrl+C can be started again with the same command. A failed run is run once more at the end of the round, and both attempts stay in the ledger. `round` exits 0 only when all 36 conditions are finished.

Run folders:

- main stage: `<results>/<scenario folder>/<run id>/`
- pilot stage: `<results>/pilot/<scenario folder>/<run id>/`, with the round order files in `<results>/pilot/`

The scenario folders are `scenario-1-uniform`, `scenario-2-mixed`, and `scenario-3-degraded-worker`, as in [results/README.md](../results/README.md). Each run folder holds `schedule.csv`, `generator.csv`, `loadgen.json`, `dispatcher.csv`, `worker-w1.csv`, `worker-w2.csv`, `sampler-host.csv`, `sampler-dispatcher.csv`, `sampler-w1.csv`, `sampler-w2.csv`, `metadata.json`, and `summary.json`.

`throw-out` appends a `thrown_out` row with the reason for a run already in the ledger. It changes nothing else.

## Before running experiments

Work through [notes/open-questions.md](../notes/open-questions.md) first. It lists every parameter the proposal left open, with the method already settled and the value the pilot still has to fix: request rates, run length, image classes, weights, EWMA weight, CPU quota, queue capacity, timeouts. Record each value in `notes/decisions.md` and in the config before the main runs. Do not tune settings after seeing results.
