"""Headless Prometheus metrics exporter for cubestat."""

import time

from cubestat.metrics_registry import get_metrics
from cubestat.prometheus_server import PrometheusServer


class PrometheusExporter:
    """Headless exporter that collects metrics for Prometheus scraping."""

    def __init__(self, args):
        """Initialize the exporter with metrics configuration.

        Args:
            args: Parsed command-line arguments
        """
        self.metrics = get_metrics(args)
        self.collection_count = 0
        self.start_time = time.time()
        self.refresh_ms = args.refresh_ms

    def do_read(self, context) -> None:
        """Callback for platform loop - run collectors to update Prometheus gauges.

        Args:
            context: Platform-specific context (plist dict on macOS, None on Linux)
        """
        for group, metric in self.metrics.items():
            metric.collector.collect(context)
        self.collection_count += 1

        # Print periodic stats every 10 collections
        if self.collection_count % 10 == 0:
            elapsed = time.time() - self.start_time
            print(f"[{elapsed:.1f}s] Collections: {self.collection_count}", flush=True)


def prometheus_export(platform, args):
    """Run cubestat in headless mode - collect metrics for Prometheus only.

    Args:
        platform: Platform instance (MacOSPlatform or LinuxPlatform)
        args: Parsed command-line arguments
    """
    server = PrometheusServer(args.prometheus_port)
    server.start()

    exporter = PrometheusExporter(args)

    print(f"Prometheus metrics: http://localhost:{args.prometheus_port}/metrics")
    print(f"Refresh interval: {args.refresh_ms}ms")
    print("Press Ctrl+C to stop\n")

    try:
        platform.loop(exporter.do_read)
    except KeyboardInterrupt:
        print(f"\nStopping... Total collections: {exporter.collection_count}")
        server.stop()
