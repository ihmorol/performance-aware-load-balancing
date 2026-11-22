"""Start the worker service.

    python -m worker --config config/dev.toml --port 8101

The queue capacity comes from worker.queue_capacity in the config. The log is
written to --log when the service stops (default local/worker-<port>.csv).
"""

import argparse
from pathlib import Path

import uvicorn

from plb.config import load_config
from worker.app import create_app


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run one image processing worker.")
    parser.add_argument("--config", required=True, help="config TOML file")
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--host", default="127.0.0.1", help="use 0.0.0.0 on a VM")
    parser.add_argument("--log", help="CSV file the log is written to on shutdown")
    args = parser.parse_args(argv)

    config = load_config(args.config)
    capacity = config.worker.queue_capacity
    if capacity is None:
        parser.error("worker.queue_capacity is unset in the config")

    log_path = Path(args.log or f"local/worker-{args.port}.csv")
    app = create_app(capacity, shutdown_log_path=log_path)
    # No access log: one line per request would add work to every measurement.
    # Longer than the HTTPX clients' 5 s idle limit, so the server never drops a connection a client is reusing.
    uvicorn.run(app, host=args.host, port=args.port, access_log=False, timeout_keep_alive=30)


if __name__ == "__main__":
    main()
