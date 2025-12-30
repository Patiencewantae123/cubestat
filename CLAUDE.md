# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands
- Install: `pip install -e .` or `pip install -e .[cuda]` for NVIDIA GPU support
- Install dev dependencies: `pip install -r requirements-dev.txt`
- Run tests: `python -m unittest discover`
- Run single test: `python -m unittest cubestat.tests.test_data_manager`
- Type check: `mypy cubestat`
- Lint: `ruff check cubestat`
- Format: `ruff format cubestat`
- Run TUI mode: `python -m cubestat.cubestat`
- Run headless Prometheus exporter: `python -m cubestat.cubestat --prometheus-port 9090`
- Run TUI with Prometheus: `python -m cubestat.cubestat --prometheus-port 9090 --tui`

## Code Style
- File/function/variable naming: snake_case (e.g., `data_manager.py`, `get_metrics`)
- Class naming: CamelCase for primary classes (e.g., `DataManager`), snake_case for metrics 
- Add type hints to all new code and when refactoring existing code
- Imports: standard library first, then project imports
- **Metrics Architecture**: Use collector/presenter pattern (see Architecture section below)
- **Metric Naming**: Use standardized `component.type.instance.attribute.unit` format
- Platform-specific implementations in separate modules
- Error handling: Use try/except blocks with specific exceptions and logging
- Documentation: Add docstrings in Google style format to all functions and classes
- Logging: Use the logging module instead of print statements
- Support cross-platform (macOS, Linux) when implementing features
- Main entry point is `cubestat.cubestat:main`

## Architecture

### Collector/Presenter Pattern
All metrics follow the simplified collector/presenter architecture with standardized naming:

**Collectors** (`cubestat/collectors/`):
- Responsible for data collection from system APIs
- Platform-specific implementations (e.g., `MacOSCPUCollector`, `LinuxCPUCollector`)
- **Return standardized metric names**: `component.type.instance.attribute.unit`
- Handle platform differences (psutil vs system context vs /proc files)
- **Double-write pattern**: Update both return dict and Prometheus gauges simultaneously
- Initialize Prometheus `Gauge` metrics in constructor with appropriate labels

**Presenters** (`cubestat/presenters/`):
- Handle data transformation and UI concerns: display modes, formatting, filtering
- Process standardized collector data directly into final display format
- Manage hotkeys and command-line arguments
- Platform-agnostic display logic

**Metrics** (`cubestat/metrics/`):
- Unified `Metric` class that directly composes collector and presenter
- Simple factory functions create platform-specific instances
- Configuration-driven approach via `all_metrics.py`
- No complex inheritance hierarchy or adapter patterns

### Data Flow
```
Collector → Standardized Names → Presenter → TUI Display
    ↓              ↓                  ↓
Raw System   component.type.     Process &
   Data      instance.attr.unit   Format
    ↓
Prometheus Gauges (double-write)
```

### Current Architecture Structure
```
cubestat/collectors/memory_collector.py   # Data collection → standardized names
cubestat/presenters/memory_presenter.py   # Data transformation & UI formatting
cubestat/metrics/metric.py                # Unified Metric class
cubestat/metrics/metric_factory.py        # Simple factory functions
cubestat/metrics/all_metrics.py           # Configuration-driven metric definitions
```

### Standardized Naming Examples
- `memory.system.total.used.percent`
- `cpu.performance.0.core.2.utilization.percent`
- `gpu.nvidia.0.utilization.percent`
- `power.component.cpu.consumption.watts`
- `network.total.rx.bytes_per_sec`

### Output Modes
**TUI Mode (default)**:
- Interactive terminal interface with horizon charts
- Presenters transform standardized names to display-friendly format
- Requires curses and 256-color terminal

**Prometheus Metrics Mode (`--prometheus-port PORT`)**:
- Runs headless by default - no TUI, just collects metrics for Prometheus
- Serves metrics in Prometheus format at `/metrics` endpoint
- Add `--tui` flag to show TUI charts alongside Prometheus export
- Prints periodic stats (collection count) to stdout
- Metrics include labels for multi-dimensional data (e.g., CPU core, cluster type, GPU vendor)
- **Complete collector coverage**: All system collectors export Prometheus metrics
  - **ANE**: `ane_usage_percent` - Apple Neural Engine utilization
  - **CPU**: `cpu_usage_percent` - Per-core utilization with cluster labels
  - **Disk**: `disk_read_bytes_per_second`, `disk_write_bytes_per_second` - I/O throughput
  - **GPU**: `gpu_usage_percent`, `gpu_memory_usage_percent` - Multi-vendor with labels
  - **Memory**: `memory_usage_percent`, `memory_used_bytes`, platform-specific metrics
  - **Network**: `network_receive_bytes_per_second`, `network_transmit_bytes_per_second`
  - **Power**: `power_consumption_total_watts`, `power_consumption_watts` by component
  - **Swap**: `swap_used_bytes` - Virtual memory usage

### Metric Creation
**Simplified Architecture** (current):
- Single `Metric` class composes collector and presenter directly
- Factory functions in `metric_factory.py` create platform-specific instances
- Configuration in `all_metrics.py` defines all metrics declaratively
- No inheritance hierarchy or complex adapter patterns

**Adding New Metrics**:
1. Implement collector(s) in `cubestat/collectors/`
2. Implement presenter in `cubestat/presenters/`  
3. Add metric key to appropriate list in `all_metrics.py`
4. Handle special cases (if any) with simple configuration overrides

**Example - Adding a new cross-platform metric**:
```python
# In all_metrics.py
CROSS_PLATFORM_METRICS = [
    "cpu", "network", "gpu", "disk", "swap", 
    "temperature"  # ← Just add the key here
]
```

### Platform-Specific Guidelines
- **macOS-only metrics** (power, accel): No Linux implementation to avoid confusion
- **Cross-platform metrics** (CPU, memory, network): Platform-specific collectors
- **Graceful degradation**: Clear absence better than misleading zero values