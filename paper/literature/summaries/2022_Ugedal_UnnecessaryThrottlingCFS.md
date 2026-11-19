# 2022 Ugedal unnecessary throttling in CFS bandwidth control

## Citation
O. Ugedal, R. Kumar. "Mitigating Unnecessary Throttling in Linux CFS Bandwidth Control." 2022 IEEE 34th International Symposium on Computer Architecture and High Performance Computing (SBAC-PAD), pp. 336-345. DOI: 10.1109/SBAC-PAD55451.2022.00044 (checked on Crossref and the SBC proceedings page).

## Free PDF
Not downloaded. NTNU repository record: https://hdl.handle.net/11250/3055366 (author version; the file link could not be reached by script). Read online: abstract only.

## Problem
CFS bandwidth control (the quota and period behind cgroup CPU limits) can throttle a process that should not be throttled.

## Method
Root cause study of the runtime accounting in bandwidth control, plus kernel changes.

## Key findings (abstract only)
- The runtime accounting that tracks if a group hit its limit causes the extra throttling.
- Overhead of bandwidth control can become high.
- Their changes removed nearly all unnecessary throttling, up to 12% performance gain, and cut overhead up to 24x.

## Limitations
Full text not read here, so setup, kernel version and workloads are unknown to us.

## Implications for us
A quota slows the worker in bursts, not as a smooth slower CPU. Record the quota and period values, the kernel version, and the throttling counters (nr_throttled, throttled_usec in cpu.stat) for every run.

## Gap
No data on how a fixed quota on one VM worker shapes p95 for a load balancer.
