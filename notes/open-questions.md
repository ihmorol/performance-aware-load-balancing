# Open questions

Parameters the proposal left open. Decide each before the main experiments and move it to `decisions.md` with the chosen value. Do not invent values during the defense; the honest answer is "not final yet, we fix it before the runs and keep it consistent". The full table is in the defense study guide, section 14.

- [ ] Request rates: exact values for each scenario, and how the pilot selects them
- [ ] Run duration: measurement window, warm-up, drain policy
- [ ] Image set: dimensions, formats, counts, mixture proportions, processing settings
- [ ] Weighted round-robin: calibration condition, weight ratio, exact variant
- [ ] Feedback rule: averaging method, window or smoothing, which samples count
- [ ] Slow worker: exact CPU quota, how it is applied, fixed during a run or not
- [ ] Worker queue: capacity, rejection behavior, accounting boundaries
- [ ] Probes: content, frequency, cost accounting, relation to health checks
- [ ] Timeouts: values, cancellation, what happens to work that finishes after timeout
- [ ] Latency reporting: which outcomes enter the sample, percentile method
- [ ] Throughput: success-only or all-terminal responses, measurement interval
- [ ] Resource monitoring: sampling frequency, scope (process, VM, host), overhead
- [ ] Reset: what state is reset between runs, handling of outstanding work
- [ ] Analysis: variation summary, uncertainty reporting, what counts as a meaningful benefit
