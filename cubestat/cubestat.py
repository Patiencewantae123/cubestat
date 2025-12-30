#!/usr/bin/env python3

import argparse
import curses
import logging

from cubestat.metrics_registry import metrics_configure_argparse
from cubestat.platforms.factory import get_platform
from cubestat.tui.app import ViewMode, start


def main():
    logging.basicConfig(filename="/tmp/cubestat.log", level=logging.INFO)
    parser = argparse.ArgumentParser("cubestat")
    parser.add_argument(
        "--refresh_ms", "-i", type=int, default=1000, help="Update frequency (milliseconds)"
    )

    parser.add_argument(
        "--buffer_size",
        type=int,
        default=500,
        help="Number of datapoints to store. Consider larger values for window resizing.",
    )

    parser.add_argument(
        "--view",
        type=ViewMode,
        default=ViewMode.one,
        choices=list(ViewMode),
        help='Display mode (legend, values, time). Hotkey: "v".',
    )

    parser.add_argument(
        "--prometheus-port", type=int, help="Enable Prometheus metrics exporter on specified port"
    )

    parser.add_argument(
        "--tui", action="store_true", help="Show TUI charts (use with --prometheus-port for both)"
    )

    metrics_configure_argparse(parser)
    args = parser.parse_args()

    platform = get_platform(args.refresh_ms)

    # Mode selection
    if args.prometheus_port:
        if args.tui:
            # TUI + Prometheus
            curses.wrapper(start, platform, args)
        else:
            # Headless Prometheus only (default when --prometheus-port given)
            from cubestat.prometheus.exporter import prometheus_export
            prometheus_export(platform, args)
    else:
        # Plain TUI (default)
        curses.wrapper(start, platform, args)


if __name__ == "__main__":
    main()
