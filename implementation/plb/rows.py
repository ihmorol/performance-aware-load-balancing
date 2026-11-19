"""Column names of the per-request CSV logs, in file order.

The lists follow the "Worker", "Dispatcher", and "Load generator" sections of
implementation/spec.md. The worker log is written by worker/app.py; the other
two are here so the dispatcher, the load generator, and the summary agree on
one set of names.
"""

WORKER_LOG_COLUMNS = (
    "request_id",
    "arrival_unix_s",  # wall-clock time, only for lining up with other logs from the same machine
    "queue_wait_ms",
    "processing_ms",
    "outcome",
)

DISPATCHER_LOG_COLUMNS = (
    "run_id",
    "rule",
    "scenario",
    "rate",
    "request_id",
    "image_id",
    "size_class",
    "probe",
    "warmup",
    "chosen_worker",
    "unfinished_w1",
    "unfinished_w2",
    "estimate_w1_ms",
    "estimate_w2_ms",
    "select_ns",
    "worker_processing_ms",
    "worker_status",
    "outcome",
    "dispatcher_ms",
)

GENERATOR_LOG_COLUMNS = (
    "run_id",
    "request_id",
    "image_id",
    "size_class",
    "planned_offset_s",
    "actual_offset_s",
    "send_lag_ms",
    "status",
    "outcome",
    "response_ms",
    "chosen_worker",
    "processing_ms",
    "output_bytes",
)
