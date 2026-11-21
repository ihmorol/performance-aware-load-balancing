# Implementation workspace

The planned system, per the proposal: one dispatcher VM (1 GB RAM, 1 vCPU) and two worker VMs (2 GB RAM, 1 vCPU each), all Ubuntu Server, running locally. Workers process image resize and recompression jobs. The dispatcher picks a worker by one of four rules: round-robin, weighted round-robin, least unfinished requests (least connections counted in requests), or recent processing time feedback.

The build follows [spec.md](spec.md) and the order in [ORCHESTRATION.md](ORCHESTRATION.md).

## Layout

- `plb/`: the shared package. Config loading and checks (`plb.config`), the header names and outcome values every part uses (`plb.protocol`), the column names of the worker, dispatcher, and generator logs (`plb.rows`), and the seeded image set generator (`plb.images`).
- `worker/`: the image processing service. Built.
- `dispatcher/`: routing rules and the forwarding path. Built.
- `experiments/`: load generator, orchestrator, pilot tools, and the per-run summary. Not built yet.
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

## Before running experiments

Work through [notes/open-questions.md](../notes/open-questions.md) first. It lists every parameter the proposal left open, with the method already settled and the value the pilot still has to fix: request rates, run length, image classes, weights, EWMA weight, CPU quota, queue capacity, timeouts. Record each value in `notes/decisions.md` and in the config before the main runs. Do not tune settings after seeing results.
