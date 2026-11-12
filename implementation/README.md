# Implementation workspace

The planned system, per the proposal: one dispatcher VM (1 GB RAM, 1 vCPU) and two worker VMs (2 GB RAM, 1 vCPU each), all Ubuntu Server, running locally. Workers process image resize and recompression jobs. The dispatcher picks a worker by one of four rules: round-robin, weighted round-robin, least connections, or recent processing time feedback.

## Planned layout

- `dispatcher/`: routing rules and the request queue
- `worker/`: the image processing service
- `experiments/`: the three scenarios, uniform, mixed, and mixed with one slowed worker
- `setup/`: VM creation steps, network config, and the reset procedure

Nothing here is built yet. Files appear as work starts.

## Before running experiments

Work through [notes/open-questions.md](../notes/open-questions.md) first. It lists every parameter the proposal left open: request rates, run duration, image set, weights, averaging window, CPU quota, queue limits, timeouts. Decide each one before the main runs and record the choice in `notes/decisions.md`. Do not tune settings after seeing results.
