# Results

Measurements from the three scenarios land here, one folder per scenario:

- `scenario-1-uniform/`
- `scenario-2-mixed/`
- `scenario-3-degraded-worker/`

Each folder holds the raw output (CSV or logs, exactly as produced) and a short summary (mean, p95, throughput, failures, resource use). The summary states how each number was computed. If a run is thrown out, say why in that folder's notes. Keep failed runs; they are data too.

Per `implementation/spec.md`, main runs go one folder per run inside these scenario folders. Pilot, calibration, and dry-run data get their own folders next to them, and the run ledger is one CSV in this folder.

No measurements exist yet. Only the worker is built; the dispatcher, load generator, and orchestrator are not.
