"""Header names and outcome values shared by worker, dispatcher, and generator.

Request and reply formats are described under "Request format" in
implementation/spec.md. Header values are plain strings; times are in
milliseconds.
"""

# Generator to dispatcher, and dispatcher to worker.
REQUEST_ID = "X-Request-Id"
IMAGE_ID = "X-Image-Id"
SIZE_CLASS = "X-Size-Class"

# Dispatcher to worker only. The budget is relative (milliseconds from the
# worker's arrival time) because the machines' clocks differ.
BUDGET_MS = "X-Budget-Ms"
# "1" for a probe request, "0" otherwise.
PROBE = "X-Probe"

# Worker reply.
PROCESSING_MS = "X-Processing-Ms"
OUTPUT_BYTES = "X-Output-Bytes"
OUTCOME = "X-Outcome"

# Dispatcher reply to the generator.
CHOSEN_WORKER = "X-Chosen-Worker"

# Terminal outcomes. The worker produces the first three; the dispatcher and
# generator add the last two.
DONE = "done"
REJECTED = "rejected"
EXPIRED = "expired"
TIMEOUT = "timeout"
ERROR = "error"
