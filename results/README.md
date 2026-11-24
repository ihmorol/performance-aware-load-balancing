# Results

Measurements from the three scenarios land here, one folder per scenario:

- `scenario-1-uniform/`
- `scenario-2-mixed/`
- `scenario-3-degraded-worker/`

Each folder holds the raw output (CSV or logs, exactly as produced) and a short summary (mean, p95, throughput, failures, resource use). The summary states how each number was computed. If a run is thrown out, say why in that folder's notes. Keep failed runs; they are data too.

Per `implementation/spec.md`, main runs go one folder per run inside these scenario folders. Pilot, calibration, and dry-run data get their own folders next to them, and the run ledger is one CSV in this folder.

No measurements exist yet. The code for the pilot and the main runs is built (issues #2 to #7); the pilot on the cloud VMs comes next. Laptop runs go to `implementation/local/results`, never here.
