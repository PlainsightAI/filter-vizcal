
# Visual Calibration Environment Calibration Filter

[![PyPI version](https://img.shields.io/pypi/v/filter-vizcal.svg?style=flat-square)](https://pypi.org/project/filter-vizcal/)
[![Docker Version](https://img.shields.io/docker/v/plainsightai/openfilter-vizcal?sort=semver)](https://hub.docker.com/r/plainsightai/openfilter-vizcal)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://github.com/PlainsightAI/filter-vizcal/blob/main/LICENSE)

Visual Calibration is a lightweight video analysis filter designed for computer vision applications. It provides real-time analysis of camera stability, movement detection, and video properties to help you understand your hardware setup and environment. **Supports multi-topic processing** - analyze multiple video streams independently with separate analysis states.

## Quick Start

The easiest way to run the Visual Calibration filter is using the provided usage script:

```bash
# Basic usage with default settings (single video, multi-topic analysis)
python scripts/filter_usage.py

# Custom video input
VIDEO_INPUT="./data/your-video.mp4" python scripts/filter_usage.py

# Custom configuration
FILTER_SHAKE_THRESHOLD=10 FILTER_MOVEMENT_THRESHOLD=2.0 python scripts/filter_usage.py
```

### Environment Variables

The filter can be configured using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `VIDEO_INPUT` | `./data/sample-video.mp4` | Input video file path |
| `OUTPUT_FPS` | `30` | Output video frames per second |
| `WEBVIS_PORT` | `8002` | Port for Webvis visualization |
| `FILTER_CALCULATE_CAMERA_STABILITY` | `True` | Enable camera stability analysis |
| `FILTER_CALCULATE_VIDEO_PROPERTIES` | `True` | Enable video properties calculation |
| `FILTER_CALCULATE_MOVEMENT` | `True` | Enable movement detection |
| `FILTER_SHAKE_THRESHOLD` | `5` | Camera shake detection threshold |
| `FILTER_MOVEMENT_THRESHOLD` | `1.0` | Movement detection threshold |
| `FILTER_FORWARD_UPSTREAM_DATA` | `True` | Forward data from upstream filters |
| `FILTER_SHOW_TEXT_OVERLAYS` | `True` | Show analysis overlays on video |
| `FILTER_LOG_INTERVAL` | `3` | Log analysis results every N frames |

### Viewing Results

After running the filter, you can view the results at:
- **Webvis**: `http://localhost:8002` - Real-time video streams with analysis overlays
  - **Main stream**: `http://localhost:8002/main` - First topic analysis
  - **Stream2**: `http://localhost:8002/stream2` - Second topic analysis

## Features

- **Multi-Topic Processing**: Analyze multiple video streams independently with separate analysis states
- **Camera Stability Analysis**: Detects camera shake and movement patterns per topic
- **Video Properties Calculation**: Analyzes frame properties and quality metrics per topic
- **Movement Detection**: Optional optical flow-based movement tracking per topic
- **Per-Topic State Management**: Independent analysis states prevent cross-contamination
- **Environment Variable Configuration**: No command-line arguments needed
- **Real-time Visualization**: Live analysis overlays via Webvis for multiple streams
- **Upstream Data Forwarding**: Passes through data from upstream filters
- **Text Overlays**: Optional visual analysis information on video frames
- **Non-Image Frame Support**: Forwards non-image frames as-is

## How to Run

### Prerequisites
- Python 3.10 or higher
- OpenCV and other dependencies (see `pyproject.toml`)

### Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd filter-vizcal
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the filter:**
   ```bash
   python scripts/filter_usage.py
   ```

### Docker Support

The filter also supports Docker deployment:

1. **Build the Docker image:**
   ```bash
   docker build -t vizcal-filter .
   ```

2. **Run with Docker:**
   ```bash
   docker run -p 8002:8002 -v $(pwd)/data:/app/data -v $(pwd)/output:/app/output vizcal-filter
   ```

### Configuration Examples

**Basic Analysis:**
```bash
python scripts/filter_usage.py
```

**High Sensitivity:**
```bash
FILTER_SHAKE_THRESHOLD=2 FILTER_MOVEMENT_THRESHOLD=0.5 python scripts/filter_usage.py
```

**Disable Overlays:**
```bash
FILTER_SHOW_TEXT_OVERLAYS=false python scripts/filter_usage.py
```

**Custom Video:**
```bash
VIDEO_INPUT="./path/to/your/video.mp4" python scripts/filter_usage.py
```

## Documentation

For detailed information about configuration options, performance tuning, and advanced usage, see the [comprehensive documentation](https://github.com/PlainsightAI/filter-vizcal/blob/main/docs/overview.md).
