"""Start the dispatcher.

    python -m dispatcher --config config/dev.toml --rule rr --scenario 1 --rate 2 --run-id manual --port 8100

The log is written to --log when the service stops (default
local/dispatcher-<port>.csv).
"""

import argparse
from pathlib import Path

import uvicorn

from dispatcher.app import create_app
from dispatcher.rules import RULES
from plb.config import load_config


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Run the dispatcher with one routing rule.")
    parser.add_argument("--config", required=True, help="config TOML file")
    parser.add_argument("--rule", required=True, choices=RULES)
    parser.add_argument("--scenario", required=True, type=int, choices=(1, 2, 3))
    parser.add_argument("--rate", required=True, type=float, help="request rate of the run, for the log")
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--host", default="127.0.0.1", help="use 0.0.0.0 on a VM")
    parser.add_argument("--log", help="CSV file the log is written to on shutdown")
    args = parser.parse_args(argv)

    config = load_config(args.config)
    needed = {
        "addresses.workers": config.addresses.workers,
        "dispatcher.timeout_ms": config.dispatcher.timeout_ms,
        "dispatcher.ewma_weight": config.dispatcher.ewma_weight,
        "dispatcher.probe_threshold_s": config.dispatcher.probe_threshold_s,
        "dispatcher.warmup_count": config.dispatcher.warmup_count,
        "images.resolutions.medium": config.images.resolutions.medium,
        "images.resolutions.small": config.images.resolutions.small,
        "seeds.image_set": config.seeds.image_set,
    }
    # Only weighted round-robin reads the weights. The pilot may run the
    # other rules before calibration has set them.
    if args.rule == "wrr":
        needed[f"weights.scenario{args.scenario}"] = getattr(config.weights, f"scenario{args.scenario}")
    unset = [key for key, value in needed.items() if value is None]
    if unset:
        parser.error(f"unset in the config: {', '.join(unset)}")
    if len(config.addresses.workers) != 2:
        parser.error("addresses.workers must list exactly two workers")

    log_path = Path(args.log or f"local/dispatcher-{args.port}.csv")
    app = create_app(config, args.rule, args.scenario, args.rate, args.run_id, shutdown_log_path=log_path)
    # No access log: one line per request would add work to every measurement.
    uvicorn.run(app, host=args.host, port=args.port, access_log=False)


if __name__ == "__main__":
    main()
