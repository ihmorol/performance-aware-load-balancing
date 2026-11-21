# Implementation workspace

The planned system, per the proposal: one dispatcher VM (1 GB RAM, 1 vCPU) and two worker VMs (2 GB RAM, 1 vCPU each), all Ubuntu Server, running locally. Workers process image resize and recompression jobs. The dispatcher picks a worker by one of four rules: round-robin, weighted round-robin, least unfinished requests (least connections counted in requests), or recent processing time feedback.

The build follows [spec.md](spec.md) and the order in [ORCHESTRATION.md](ORCHESTRATION.md).

## Layout

- `plb/`: the shared package. Config loading and checks (`plb.config`), the header names and outcome values every part uses (`plb.protocol`), the column names of the worker, dispatcher, and generator logs (`plb.rows`), the seeded image set generator (`plb.images`), and the per-run summary (`plb.summary`).
- `worker/`: the image processing service. Built.
- `dispatcher/`: routing rules and the forwarding path. Not built yet.
- `experiments/`: the load generator is built. The orchestrator and pilot tools are not built yet. The per-run summary lives in `plb.summary`.
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

The run folder gets three files from the generator. `schedule.csv` (`request_id, planned_offset_s, image_id, size_class`) is written before sending, and the same seed always gives the same bytes. `generator.csv` has one row per request with the columns in `plb.rows.GENERATOR_LOG_COLUMNS`. Chosen worker, processing time, and output size come from the reply headers and stay empty when the reply has none. `loadgen.json` holds the run parameters: run id, rule, scenario, rate, round, target, run length, dropped window, tolerance, and the schedule seed.

`plb.summary` reads only `generator.csv` and `loadgen.json` and writes `summary.json`. The measured window is every request planned at or after `run.dropped_window_s` (W), and its length is the run length minus W.

- `measured` and `successes` count requests in the measured window.
- `mean_ms` and `p95_ms` cover successful requests only. p95 is the nearest rank: sort, then take the value at position ceil(0.95 × n).
- `p95_by_class_ms` gives p95 for small, medium, and large in scenarios 2 and 3, and is null in scenario 1.
- `throughput` is successes divided by the window length, shown next to `offered_rate`, the run's `--rate`.
- `failures` counts rejected, expired, timeout, and error.
- `planned_rate` counts requests planned in the window and `achieved_rate` counts requests actually sent in the window, both divided by its length. `rate_flag` is true when the two differ by more than `run.achieved_rate_tolerance` of the planned rate. Comparing with the schedule instead of the offered rate means the random spread of a Poisson schedule never sets the flag. The flag is also true when nothing was planned in the window.
- `max_send_lag_ms` is the largest send lag in the window.

A value that can't be computed, such as p95 with no successes, is null.

## Before running experiments

Work through [notes/open-questions.md](../notes/open-questions.md) first. It lists every parameter the proposal left open, with the method already settled and the value the pilot still has to fix: request rates, run length, image classes, weights, EWMA weight, CPU quota, queue capacity, timeouts. Record each value in `notes/decisions.md` and in the config before the main runs. Do not tune settings after seeing results.
