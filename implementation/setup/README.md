# VM setup

How to build the testbed on cloud VMs: four Linux VMs in one zone, with the orchestrator on the generator VM. The plan, provider choice, prices, and sources are in [../cloud-deployment.md](../cloud-deployment.md). This guide holds the commands the code expects.

Nobody has run these steps on real VMs yet. The hardware check in [../ORCHESTRATION.md](../ORCHESTRATION.md) is the first real run, and this guide gets fixed wherever it fails.

> [!WARNING]
> Google Cloud's free trial needs a payment card, and nobody has tested a Bangladeshi card for this project yet. Before signing up, ask the bank whether the card allows international online USD payments and recurring charges, and have cards from two members ready. If no card works, use Azure for Students. Sign up only after #6 and #7 are merged, because the 90 day trial starts at sign-up.

## The four VMs and the network

| VM | Role | Internal address in `config/cloud.toml` |
|---|---|---|
| `plb-gen` | Load generator, orchestrator, host sampler | 10.128.0.10 |
| `plb-disp` | Dispatcher, port 8100 | 10.128.0.20 |
| `plb-w1` | Worker 1, port 8101 | 10.128.0.21 |
| `plb-w2` | Worker 2, port 8102, gets the quota in scenario 3 | 10.128.0.22 |

All four sit in one zone on one private network and talk over internal addresses only. The firewall allows SSH from outside and nothing else; ports 8100 to 8102 stay internal. Every VM has 1 vCPU and runs Ubuntu Server 24.04 LTS. Both workers use the same machine type, and the orchestrator refuses a run when their CPU model or vCPU count differ.

Each VM has a user named `plb`. The code lives at `/home/plb/plb`, and run files (env files, logs, sampler CSVs) go to `/home/plb/plb-run`. The units and the sudo rule use these paths, so keep them.

## Google Cloud

Follow phases 1 to 5 of "Google Cloud setup, step by step" in [../cloud-deployment.md](../cloud-deployment.md): the trial and project, the budget alerts, the quota check, then the four t2d-standard-1 VMs with the fixed internal addresses above. Do not use Spot VMs.

The default network already has the firewall rules this setup needs: SSH from outside, and all traffic between VMs on internal addresses. Add no rule that opens 8100 to 8102 to the internet.

The `plb` user comes from the SSH key added in phase 5 (`ssh-keys="plb:KEY"`). Google gives that user full sudo as well; the limited rule below is what the orchestrator needs.

## Azure for Students

Follow "Azure for Students, if no card works" in [../cloud-deployment.md](../cloud-deployment.md). Create the four VMs with the administrator name `plb`, in one virtual network and subnet, with the fixed private addresses above. Allow SSH only from your own IP address. The network's default rules allow all traffic inside the virtual network, so the service ports need no extra rule.

The free sizes are burstable. Record each VM's "CPU Credits Remaining" metric before and after every pilot and main run, and stop when it gets low. Reading it 180 times by hand isn't practical, so after each session open the metric for that session's time range in Azure Monitor, one chart per VM, and compare it with the start and end times in `results/ledger.csv`. Mark any run during which a VM ran out of credits as thrown out, with that reason (`experiments.orchestrate throw-out`).

## VM install

On every VM, as `plb`:

```bash
sudo apt update && sudo apt -y install python3.12-venv git tmux
lscpu | grep "Model name"
```

Both workers must show the same CPU model. If they don't, delete one and create it again.

On `plb-gen`, clone the repository into `~/plb` (a GitHub token is needed if it is private) and set it up:

```bash
git clone https://github.com/ihmorol/performance-aware-load-balancing.git ~/plb
bash ~/plb/implementation/setup/provision.sh gen
```

Then send the same commit to the other three and set each one up for its role:

```bash
cd ~/plb/implementation
bash setup/deploy.sh 10.128.0.20 10.128.0.21 10.128.0.22
ssh -i ~/.ssh/plb plb@10.128.0.20 bash plb/implementation/setup/provision.sh dispatcher
ssh -i ~/.ssh/plb plb@10.128.0.21 bash plb/implementation/setup/provision.sh worker
ssh -i ~/.ssh/plb plb@10.128.0.22 bash plb/implementation/setup/provision.sh worker
```

`deploy.sh` sends only committed code, as a git bundle. Each VM gets a real clone at that commit, which the main-stage git check needs. Run it again after every new commit, and `provision.sh` again after `requirements.txt` changes. `provision.sh` is safe to run more than once.

## SSH keys

The orchestrator on `plb-gen` reaches the other VMs with one key and no password. Create it on `plb-gen`:

```bash
ssh-keygen -t ed25519 -N "" -f ~/.ssh/plb
cat ~/.ssh/plb.pub
```

Add the public key for user `plb` on the other three VMs (phase 5 of the Google Cloud steps; on Azure, append it to `~/.ssh/authorized_keys`). Then `ssh -i ~/.ssh/plb plb@10.128.0.21 true` must work without a prompt. Log in to each address once by hand to accept its host key, because the orchestrator runs ssh with `BatchMode=yes` and can't answer prompts. `config/cloud.toml` names the user and key in its `[ssh]` section.

## Sudo rule

`provision.sh` installs [plb-sudoers](plb-sudoers) as `/etc/sudoers.d/plb` and checks it with `visudo`. It allows only these commands, without a password:

- `systemctl restart` and `systemctl stop` for `plb-worker.service` and `plb-dispatcher.service`
- `systemctl set-property --runtime plb-worker.service ...` for the quota

The orchestrator runs every one of them with `sudo -n`, so a missing rule fails at once instead of waiting for a password.

## Services

[plb-worker.service](plb-worker.service) runs on both worker VMs and [plb-dispatcher.service](plb-dispatcher.service) on the dispatcher VM. Each runs one Python process from `~/plb/implementation/.venv`, as `plb`.

The units take their arguments from an env file in `~/plb-run`. Before every restart, the orchestrator copies the config to the same path in the VM's clone and writes that file: the config path and port, and for the dispatcher also the run's rule, scenario, rate, and run id. So the sudo rule only needs a plain restart.

The unit files have no CPUQuota. In scenario 3 the orchestrator sets it on worker 2 at run time with `systemctl set-property --runtime plb-worker.service CPUQuota=<q>% CPUQuotaPeriodSec=<p>ms` and reads `/sys/fs/cgroup/system.slice/plb-worker.service/cpu.max` to confirm it. In scenarios 1 and 2 it clears the quota and confirms `max`. A runtime setting lasts until the next reboot, and the orchestrator sets or clears it before every run.

## Background jobs disabled

`provision.sh` turns off `unattended-upgrades` and the `apt-daily`, `apt-daily-upgrade`, and `man-db` timers, so no update or cache job wakes up during a run. Check with:

```bash
systemctl list-timers --all
```

Turn off any other timer that shows up there before the pilot.

## Version record

On each VM, after setup:

```bash
cd ~/plb/implementation && .venv/bin/python -m experiments.versions --out setup/versions-$(hostname).txt
```

It writes the provider, machine type, and zone (from the metadata service, or "unknown"), CPU model, vCPU count, RAM, Ubuntu, kernel, systemd, cgroup version, Python, and package versions. Copy the four files to `plb-gen` with `scp` and commit them, so the paper's setup section comes from these files.

## Smoke test

From `plb-gen`, inside `tmux`:

```bash
cd ~/plb/implementation
for port in 20:8100 21:8101 22:8102; do curl -s http://10.128.0.${port%%:*}:${port##*:}/health; echo; done
.venv/bin/python -m experiments.orchestrate run --backend ssh --config config/cloud.toml --scenario 3 --rule rr --rate 1 --round 0 --run-length 10
```

The health checks answer only while a service runs, so the first `orchestrate run` is the real test. The scenario 3 run's `metadata.json` must show `nr_throttled` rising on worker 2. Run one per scenario for the hardware check.

## During the main runs

From the freeze to the last main run, every run records the generator VM's commit, and the orchestrator refuses a run when a VM's clone is at another commit. So in that time:

- Commit nothing, pull nothing, and edit no tracked file on `plb-gen` or the other VMs.
- Copy results off with `scp` (or `gcloud compute scp` from Cloud Shell) and commit them from another clone, for example on a laptop.
- Work inside `tmux` on `plb-gen`, so a dropped SSH connection doesn't stop a round. `orchestrate round` resumes from the ledger after a crash.

If code must change after the freeze, the runs before and after it come from different commits. Stop, record it in `notes/decisions.md`, and redo the affected rounds.

## Reset

The reset is the orchestrator's restart step, done before every run:

1. Set the quota on worker 2 (scenario 3) or clear it (scenarios 1 and 2), and confirm it in `cpu.max`.
2. Restart both worker services. This empties their queues and their per-request logs.
3. Restart the dispatcher service with the run's rule. This clears its unfinished counts, estimates, rule state, probe timing, and log, and it warms up again before it reports healthy.

It does not reset the VMs themselves, the Linux page cache, or the CPU credits of a burstable VM.
