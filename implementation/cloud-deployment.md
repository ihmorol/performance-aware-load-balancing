# Running the experiment on cloud VMs

Written 2026-11-23 for issue #19. The main runs no longer happen on the teammate's PC. That PC does not have enough free RAM for the three VMs (1 + 2 + 2 GB) next to its own work, so the pilot, the dry run, and the 180 main runs move to rented cloud VMs. Development and tests still run as localhost processes on any laptop, as before.

Google Cloud is the first choice. It needs a credit or debit card, which is a real problem for us (see "Payment card problem" below). Azure for Students is the fallback that needs no card. The code must work on any provider, so nothing in it may depend on one cloud.

Nothing in this file is a measurement. Prices and limits come from the provider pages listed under "Sources", read on 2026-11-23. They change, so check them again on the day you sign up.

## What stays the same

- The four rules, three scenarios, three rates per scenario, five shuffled rounds, and 180 main runs.
- One dispatcher and two workers, each with 1 vCPU, running Ubuntu Server 24.04 LTS and Python 3.12.
- The orchestrator talks to the machines with plain `ssh` and `scp` and key login, as `implementation/spec.md` already says. The local backend stays for development.
- Scenario 3 slows worker 2 with systemd CPUQuota inside its VM, checked through `cpu.max` and `cpu.stat`.
- Every run records the commit id and the config hash.

## What changes

- The machines are four cloud VMs in one zone instead of three VirtualBox VMs on one PC. The fourth VM runs the load generator and the orchestrator, which the spec placed on "the host OS of the experiment PC". In this file, "the host" means that VM.
- RAM per VM follows the provider's machine type. On Google Cloud's t2d-standard-1 every VM has 4 GB, more than the frozen 1 GB and 2 GB. RAM is not the resource under test, but the paper must state the real sizes.
- The host runs Linux, not Windows. The spin-wait switch and the send-accuracy check stay; the pilot still decides the switch.
- VirtualBox items drop out: the host-only network, the VirtualBox version in the version record, and the hardware check "on the teammate's PC".
- The setup guide from #6 becomes a cloud guide (Google Cloud first, Azure second) instead of a VirtualBox guide.
- The paper describes a public cloud testbed. Results are still claimed only for this setup, with two workers.

## The four VMs

All four sit in one zone, in one private network, and talk over internal addresses only. Traffic between VMs in the same Google Cloud zone over internal addresses is free. Ports 8100 to 8102 are never opened to the internet.

| VM | Role | Example internal address (Google Cloud default network) |
|---|---|---|
| `plb-gen` | Load generator, orchestrator, host sampler | 10.128.0.10 |
| `plb-disp` | Dispatcher, port 8100 | 10.128.0.20 |
| `plb-w1` | Worker 1, port 8101 | 10.128.0.21 |
| `plb-w2` | Worker 2, port 8102, gets the quota in scenario 3 | 10.128.0.22 |

The addresses go into the `[addresses]` section of the config. The 10.128.0.0/20 range is Google Cloud's usual default for us-central1; confirm it with `gcloud compute networks subnets list` before using these numbers.

Why four and not three: if the generator shared a VM with the dispatcher, both would compete for one vCPU and the dispatcher CPU numbers would no longer mean anything. If the quota only allows three VMs, use one 2 vCPU VM for the generator and dispatcher, pin each to its own core with systemd `CPUAffinity`, and say so in the paper. Never run the generator on a laptop over the internet: internet delay would end up inside every response time.

## Payment card problem

> [!WARNING]
> Google Cloud's free trial needs a credit card or another payment method. Google places a temporary hold of $0 to $1 to check it. Users in other countries report debit cards declined with "invalid payment method", and Google forum staff said such a card probably could not take recurring charges. Nobody has tested a Bangladeshi card for this project yet. Before signing up, ask your bank whether your Visa or Mastercard allows international online USD payments and recurring charges, and have cards from two members ready. If no card works, use Azure for Students.

## Choosing a provider

| Provider | What is free | Card | Fit for the main runs |
|---|---|---|---|
| Google Cloud free trial | $300 credit for 90 days. No quota increases during the trial. No billing unless you upgrade; at the end the VMs are stopped and deleted after a 30 day grace period. | Required | Best. t2d-standard-1 gives 1 vCPU that is a full physical core, so the CPU does not burst or drop. |
| Azure for Students | $100 credit per year, renewable while a full-time student, verified with a university email. 750 hours each of B1s, B2pts v2, and B2ats v2 for 12 months. The subscription is disabled, not charged, when credit runs out. | Not required | Usable with care. The free sizes are burstable (see below). A forum report says student subscriptions are capped at 4 vCPUs, which would allow four 1 vCPU VMs and nothing more. |
| AWS Free plan | $100 credit at sign-up plus up to $100 more, for 6 months. Free-tier types: t3.micro, t3.small, t4g.micro, t4g.small, c7i-flex.large, m7i-flex.large. | "Not required for most new customers" | Weak. The t types are burstable; the flex types have a 40% baseline per vCPU and reach full speed "a majority of the time", which is not a guarantee. |
| Oracle Always Free | Arm A1: 2 OCPUs and 12 GB in total, at most two instances. Two AMD micro VMs with 1/8 OCPU each. Home region only, capacity errors are common, idle VMs may be reclaimed. | Not confirmed | Not enough. The A1 share covers two workers, but the micro VMs are too weak for the dispatcher. |

### Why burstable VMs are a problem

A burstable VM runs at full speed while it has saved CPU credits and drops to a baseline when they run out. If that happens during a run, a worker slows down for a reason that has nothing to do with the routing rule, and the comparison is no longer fair. Azure's B2ats v2 and B2pts v2 have a 20% base, start with 60 credits, and save at most 576. One credit is one vCPU at 100% for one minute, so a worker that keeps one core busy spends 60 credits an hour while earning 24. AWS t3.micro has a 10% baseline per vCPU and t3.small 20%.

Burstable VMs are fine for setup, smoke tests, and the class demo. For the pilot and main runs on such VMs, record each VM's credit balance before and after every run (Azure shows it as the "CPU Credits Remaining" metric), stop when it gets low, and report it in the paper.

## Fairness rules for cloud runs

- Both workers use the same machine type in the same zone, and `lscpu` must show the same CPU model on both. If not, delete one and create it again.
- All runs, pilot included, use one set of four VMs. Do not move to a new zone or type in the middle.
- Other customers share the physical machines. The sampler should record CPU steal time on every VM so this shows up in the data (see "What the code needs").
- The five shuffled rounds already follow Abedi and Brecht (ICPE 2017), who found that simple trial designs in a public cloud reported a 38% difference between two identical systems and recommend randomized interleaved rounds (`paper/literature/summaries/2017_Abedi_RepeatableExperimentsCloud.md`). Papadopoulos et al. (TSE 2021) ask for a full setup description and justified repetitions (`paper/literature/summaries/2021_Papadopoulos_MethodologicalPrinciples.md`).
- The paper's limitations section gains one line: the VMs ran on shared public cloud hardware.

## Cost and time on Google Cloud

These are estimates, not bills. The VM price comes from third-party price lists because Google's own price pages did not load during the check; confirm it in the Google Cloud pricing calculator.

| Item | Price | Source |
|---|---|---|
| t2d-standard-1 in us-central1 | about $0.0422 per hour | Holori and Economize price lists |
| External IPv4 address on a running VM | $0.005 per hour | Google network pricing page |
| Traffic between VMs in one zone over internal addresses | Free | Google network pricing page |
| 10 GB balanced disk | about $1 per month, charged while the VM is stopped too | gcloud-compute.com |

Four VMs running cost about $0.19 an hour, so the $300 credit covers roughly 1,500 hours of all four together. Run length is set in the pilot, so the real total is not known yet. As an example only: 100 hours of VM time for pilot, dry run, main runs, and debugging would cost about $20 plus about $4 a month for disks.

Time is the tighter limit. The trial lasts 90 days and cannot be paused or extended. Sign up only when #6 and #7 are merged, so the clock starts when the code is ready.

## Google Cloud setup, step by step

Run the commands in Cloud Shell, the terminal button at the top right of the Google Cloud console. It runs in the browser and already has `gcloud`, so nobody installs anything on Windows. The commands below are the planned steps; the guide from #6 (`implementation/setup/README.md`) will hold the tested version.

### Phase 0: before signing up

1. Wait until #6 and #7 are merged.
2. Check the payment cards as described in "Payment card problem".

### Phase 1: account and project

1. Go to https://cloud.google.com/free and start the free trial with one member's Google account. Add the card.
2. Create a project, for example `plb-experiment`.
3. Under Billing, open Budgets & alerts and add alerts at $50, $100, and $200.
4. Add the other two members: IAM & Admin, then IAM, then Grant access, with their Gmail addresses and the Editor role. They do not need their own trials.
5. Write the sign-up date in `notes/decisions.md`. The 90 days count from it.

### Phase 2: check quota before creating anything

```bash
gcloud config set project plb-experiment
gcloud config set compute/zone us-central1-a
gcloud services enable compute.googleapis.com
gcloud compute regions describe us-central1 --format="table(quotas.metric,quotas.limit)" | grep -i -E "cpus|in_use_addresses"
gcloud compute machine-types list --zones=us-central1-a --filter="name=t2d-standard-1"
```

You need at least 4 CPUs, a T2D CPU quota of at least 4 if one is listed, and 4 in-use addresses. If t2d-standard-1 is not offered in that zone, try us-central1-b or us-central1-c. If the quota is too low, stop and record it in `notes/open-questions.md`. Other 1 vCPU types where a vCPU is a whole core are c4a-standard-1 and t2a-standard-1 (both Arm). n1-standard-1 is a single hyperthread, so avoid it.

### Phase 3: create the four VMs

```bash
for pair in plb-gen:10.128.0.10 plb-disp:10.128.0.20 plb-w1:10.128.0.21 plb-w2:10.128.0.22; do
  name=${pair%%:*}; ip=${pair##*:}
  gcloud compute instances create "$name" \
    --machine-type=t2d-standard-1 \
    --image-family=ubuntu-2404-lts-amd64 --image-project=ubuntu-os-cloud \
    --boot-disk-size=10GB --boot-disk-type=pd-balanced \
    --private-network-ip="$ip"
done
gcloud compute instances list
```

Do not use Spot VMs. Google can stop them at any time, which would break runs.

### Phase 4: base setup on each VM

Open each VM with `gcloud compute ssh plb-w1` (and the same for the others), then:

```bash
sudo apt update && sudo apt -y install python3.12-venv git tmux
sudo systemctl disable --now unattended-upgrades apt-daily.timer apt-daily-upgrade.timer
python3 --version
lscpu | grep "Model name"
```

Write down the Python version and the CPU model of both workers. They must match.

### Phase 5: let the generator VM control the others

On `plb-gen`:

```bash
ssh-keygen -t ed25519 -N "" -f ~/.ssh/plb
cat ~/.ssh/plb.pub
```

In Cloud Shell, add that public key to the other three VMs. Replace `KEY` with the printed line:

```bash
for vm in plb-disp plb-w1 plb-w2; do
  gcloud compute instances add-metadata "$vm" --metadata=ssh-keys="plb:KEY"
done
```

From `plb-gen`, `ssh -i ~/.ssh/plb plb@10.128.0.21` should now log in without a password. Put the user and key path into the config's `[ssh]` section. The limited sudo rule and the systemd units come from the #6 guide.

### Phase 6: deploy and smoke test

1. Clone the repository on `plb-gen` (a GitHub token is needed if the repository is private) and deploy to the other three with the #6 deploy step.
2. From `plb-gen`, check `curl http://10.128.0.21:8101/health` for each service.
3. Run one `orchestrate run --backend ssh` per scenario and confirm that the scenario 3 run shows a rising `nr_throttled`.

### Phase 7: pilot, freeze, dry run, main runs

1. Always work inside `tmux` on `plb-gen`, so a run keeps going if the SSH connection drops. Reattach with `tmux attach`.
2. Follow the order in `implementation/ORCHESTRATION.md`: pilot, record values, freeze the config, dry run until PASS, then the main runs in one stretch.
3. Between sessions, stop the VMs: `gcloud compute instances stop plb-gen plb-disp plb-w1 plb-w2`. Start them again with `start`. A stopped VM still pays for its disk.
4. After each session, copy the results off the cloud and commit them: `gcloud compute scp --recurse plb-gen:~/plb/results ./results-backup`.

### Phase 8: clean up

When every result is committed, delete the four VMs with `gcloud compute instances delete`. Do it before day 90.

## Azure for Students, if no card works

1. Sign up at https://azure.microsoft.com/free/students with a university email address.
2. In the portal, open the subscription, then Usage + quotas, and check Total Regional vCPUs for your region. A forum report says the limit is 4 and that the allowed regions are listed under Policy, then Assignments. One student reported no quota at all for the B2 v2 sizes, so check before planning.
3. Create one resource group and one virtual network with one subnet in one region.
4. Create four Ubuntu Server 24.04 LTS VMs of the same size in that subnet, each with a fixed private address. The 1 vCPU free size is B1s. Give each a public IP for setup and allow SSH only from your own IP address.
5. Continue from Phase 4 of the Google Cloud steps. The commands inside the VMs are the same.
6. Before and after every pilot and main run, record each VM's "CPU Credits Remaining" metric. Stop and wait if it gets low.

The $100 credit pays for anything outside the free hours. When it runs out, the subscription is disabled rather than charged.

## What the code needs (issues #6 and #7)

The code must run on any Linux VM reachable by SSH, whatever the provider.

- No provider SDK, provider CLI, or provider-specific command in the code path. The orchestrator uses only `ssh`, `scp`, and the config. Provider steps live in the setup guide.
- `implementation/setup/README.md` covers Google Cloud and Azure for Students instead of VirtualBox: creating the VMs, the private network and fixed addresses, the firewall rule, and the payment card warning. The sections on SSH keys, the sudo rule, services, background jobs, the version record, and the reset stay.
- The version record drops VirtualBox and adds the provider, machine type, zone or region, CPU model, vCPU count, and RAM. It may read the provider's metadata service (Google: `http://metadata.google.internal` with the header `Metadata-Flavor: Google`; Azure: `http://169.254.169.254/metadata/instance` with the header `Metadata: true`) and writes "unknown" when neither answers.
- The sampler adds a CPU steal column on Linux, so time taken by other tenants shows up in the data. It stays empty on other operating systems.
- A pre-flight check compares the CPU model and vCPU count of the two workers over SSH and refuses to start if they differ.
- In #7, the host in `bottleneck` and `send-accuracy` output is the generator VM. `quota-check` and `dry-run` work over the SSH backend on cloud VMs without changes to the backend interface.

## Still unknown

- Whether a member's card is accepted by Google Cloud.
- The trial's CPU and address quota in the chosen region. Google does not publish it.
- The real cost, which depends on the run length the pilot sets.
- For Azure: the real vCPU quota and whether B1s credits last through a session of runs.

## Sources

Read on 2026-11-23.

- Google Cloud free trial and free tier: https://docs.cloud.google.com/free/docs/free-cloud-features
- Google Cloud quotas: https://docs.cloud.google.com/compute/resource-usage
- Google Cloud machine types (T2D has SMT disabled, so a vCPU is a whole core): https://docs.cloud.google.com/compute/docs/general-purpose-machines
- Ubuntu 24.04 images on Compute Engine: https://docs.cloud.google.com/compute/docs/images/os-details
- Google Cloud network pricing: https://cloud.google.com/vpc/network-pricing
- t2d-standard-1 price (third party): https://calculator.holori.com/gcp/vm/t2d-standard-1 and https://www.economize.cloud/resources/gcp/pricing/compute-engine/t2d-standard-1/
- Balanced disk price (third party): https://gcloud-compute.com/pd-balanced.html
- Card declines reported by users: https://groups.google.com/g/google-appengine/c/we_G1goAagM and https://discuss.google.dev/t/billing/88960
- Azure for Students: https://learn.microsoft.com/en-us/azure/education-hub/about-azure-for-students and https://azure.microsoft.com/en-us/free/students
- Azure student quota reports (forum): https://techcommunity.microsoft.com/discussions/microsoft-learn-for-educators/sku-quota-and-policy-restrictions-on-azure-for-students-and-free-subscriptions/4525160 and https://learn.microsoft.com/en-us/answers/questions/1440468/no-b2ats-v2-and-b2pts-v2-quota-for-azure-student
- Azure burstable sizes: https://learn.microsoft.com/en-us/azure/virtual-machines/sizes/general-purpose/basv2-series and https://learn.microsoft.com/en-us/azure/virtual-machines/sizes/b-series-cpu-credit-model
- AWS Free plan and EC2 free types: https://aws.amazon.com/free/ and https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-free-tier-usage.html
- AWS burstable and flex instances: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/burstable-performance-instances.html and https://aws.amazon.com/ec2/instance-types/m7i/
- Oracle Always Free: https://docs.oracle.com/en-us/iaas/Content/FreeTier/freetier_topic-Always_Free_Resources.htm
