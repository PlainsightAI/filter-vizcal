---
title: Visual Calibration Environment Calibration Filter
sidebar_label: Overview
sidebar_position: 1
---

import Admonition from '@theme/Admonition';

# Visual Calibration Environment Calibration Filter

The Visual Calibration filter is a lightweight video analysis tool designed for computer vision applications. It provides crucial insights about your hardware setup and environment, including camera stability analysis, movement detection, and video quality assessment. **Supports multi-topic processing** - analyze multiple video streams independently with separate analysis states for each topic.

## How It Works

The Visual Calibration filter uses a multi-stage analysis pipeline with **per-topic processing**:

1. **Multi-Topic Input Processing**: Reads video frames from various sources (files, RTSP streams, etc.) with different topics
2. **Per-Topic Camera Stability Analysis**: Detects camera shake and movement patterns independently for each topic
3. **Per-Topic Video Properties Calculation**: Analyzes frame properties, quality metrics, and technical specifications for each topic
4. **Per-Topic Movement Detection**: Optional movement tracking and analysis (when enabled) with independent state
5. **Multi-Stream Real-time Visualization**: Provides live analysis overlays via Webvis for multiple streams
6. **Upstream Data Forwarding**: Passes through data from upstream filters while preserving topic structure
7. **Non-Image Frame Support**: Forwards non-image frames as-is without processing

## Features

### **Multi-Topic Processing**
- **Independent Analysis**: Each topic processed with separate analysis state
- **Per-Topic State Management**: Camera stability, movement tracking, and video properties tracked independently
- **Topic Preservation**: Output data maintains same topic structure as input
- **Cross-Contamination Prevention**: No interference between different topic analyses
- **Scalable Processing**: Handle any number of topics simultaneously

### **Camera Stability Analysis (Per-Topic)**
- **Shake Detection**: Identifies camera shake and vibration patterns for each topic
- **Movement Tracking**: Monitors camera movement and stability per topic
- **Stability Categorization**: Classifies video stability levels per topic
- **Threshold-based Detection**: Configurable sensitivity settings per topic

### **Video Properties Analysis (Per-Topic)**
- **Frame Analysis**: Calculates frame dimensions, quality metrics per topic
- **Technical Specifications**: Analyzes video encoding, bitrate, etc. per topic
- **Quality Assessment**: Evaluates video clarity and consistency per topic
- **Performance Metrics**: Tracks processing performance per topic

### **Movement Detection (Per-Topic, Optional)**
- **Optical Flow Analysis**: Tracks movement patterns using computer vision per topic
- **Movement Thresholds**: Configurable sensitivity for movement detection per topic
- **ROI-based Analysis**: Focuses analysis on specific regions of interest per topic
- **Real-time Tracking**: Continuous movement monitoring per topic

### **Flexible Configuration**
- **Environment Variable Driven**: No command-line arguments needed
- **Dynamic Output Naming**: Automatically generates descriptive output filenames
- **Multiple Input Sources**: Supports files, RTSP streams, and web URLs
- **Customizable Thresholds**: Adjustable sensitivity for all detection algorithms
- **Upstream Data Forwarding**: Configurable forwarding of data from upstream filters

### **Real-time Visualization**
- **Live Analysis Overlays**: Real-time stability and movement indicators per topic
- **Webvis Integration**: Browser-based visualization interface with multi-stream support
- **Interactive Controls**: Adjustable visualization parameters
- **Multi-Stream Support**: Handle multiple video sources simultaneously with independent analysis
- **Topic-based URLs**: Access different analysis streams via separate URLs

## Configuration Options

### Core Analysis Settings

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `FILTER_CALCULATE_CAMERA_STABILITY` | boolean | `true` | Enable camera stability analysis |
| `FILTER_CALCULATE_VIDEO_PROPERTIES` | boolean | `true` | Enable video properties calculation |
| `FILTER_CALCULATE_MOVEMENT` | boolean | `true` | Enable movement detection |
| `FILTER_SHAKE_THRESHOLD` | integer | `5` | Camera shake detection threshold (lower = more sensitive) |
| `FILTER_MOVEMENT_THRESHOLD` | float | `1.0` | Movement detection threshold (lower = more sensitive) |
| `FILTER_ROI` | list | `[]` | Region of interest for analysis `[x, y, width, height]` |

### Output and Visualization Settings

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `FILTER_FORWARD_UPSTREAM_DATA` | boolean | `true` | Forward data from upstream filters |
| `FILTER_SHOW_TEXT_OVERLAYS` | boolean | `true` | Show analysis overlays on video |
| `FILTER_LOG_INTERVAL` | integer | `3` | Log analysis results every N frames |

### Input/Output Settings

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `VIDEO_INPUT` | string | `./data/sample-video.mp4` | Input video file path |
| `OUTPUT_VIDEO_PATH` | string | `./output/{input_name}_vizcal_output.mp4` | Output video file path |
| `OUTPUT_FPS` | integer | `30` | Output video frames per second |
| `WEBVIS_PORT` | integer | `8002` | Port for Webvis visualization |

## Usage Examples

### Basic Multi-Topic Analysis
```bash
# Analyze a video file with multi-topic processing (same video, different analysis)
python scripts/filter_usage.py
```

### High Sensitivity Analysis
```bash
# Detect more subtle camera movements across all topics
FILTER_SHAKE_THRESHOLD=2 FILTER_MOVEMENT_THRESHOLD=0.5 python scripts/filter_usage.py
```

### Movement Detection Only
```bash
# Enable only movement detection, disable other analysis for all topics
FILTER_CALCULATE_CAMERA_STABILITY=false FILTER_CALCULATE_VIDEO_PROPERTIES=false python scripts/filter_usage.py
```

### Custom Output Location
```bash
# Specify custom output paths
OUTPUT_VIDEO_PATH="/output/analysis.mp4" python scripts/filter_usage.py
```

### RTSP Stream Analysis
```bash
# Analyze live RTSP stream
VIDEO_INPUT="rtsp://admin:password@192.168.1.100:554/stream" python scripts/filter_usage.py
```

### Disable Text Overlays
```bash
# Run analysis without visual overlays
FILTER_SHOW_TEXT_OVERLAYS=false python scripts/filter_usage.py
```

### Custom ROI Analysis
```bash
# Focus analysis on specific region for all topics
FILTER_ROI="[100, 100, 400, 300]" python scripts/filter_usage.py
```

### Multi-Topic Pipeline Integration
```python
# Example: Process multiple video streams with Visual Calibration
(Vizcal, {
    "id": "vizcal_multi",
    "sources": [
        "tcp://localhost:5552;main",      # Analyze main stream
        "tcp://localhost:5554;stream2",   # Analyze stream2
        "tcp://localhost:5556;stream3",   # Analyze stream3
    ],
    "outputs": "tcp://*:5580",
    "calculate_camera_stability": True,
    "calculate_video_properties": True,
    "calculate_movement": True,
    # Each topic gets independent analysis
}),
```

## Output Data Structure

The filter provides real-time analysis data through frame metadata and visual overlays with **per-topic analysis**:

### Multi-Topic Frame Metadata
Each processed frame includes analysis data in the frame's metadata, with independent analysis per topic:

```json
{
  "main": {
    "camera_stability": {
      "shake_distance": 2.3,
      "is_stable": true,
      "stability_category": "Stable"
    },
    "video_properties": {
      "frame_width": 1920,
      "frame_height": 1080,
      "fps": 30
    },
    "movement_detection": {
      "movement_detected": false,
      "movement_distance": 0.5
    },
    "analysis_timestamp": "2024-01-15T10:30:45Z"
  },
  "stream2": {
    "camera_stability": {
      "shake_distance": 1.8,
      "is_stable": true,
      "stability_category": "Stable"
    },
    "video_properties": {
      "frame_width": 1920,
      "frame_height": 1080,
      "fps": 30
    },
    "movement_detection": {
      "movement_detected": true,
      "movement_distance": 2.1
    },
    "analysis_timestamp": "2024-01-15T10:30:45Z"
  }
}
```

### Visual Overlays (Per-Topic)
When `FILTER_SHOW_TEXT_OVERLAYS=true`, the filter adds real-time analysis information directly to the video frames for each topic:
- Camera stability status per topic
- Movement detection alerts per topic
- Video properties per topic
- Analysis metrics per topic
- Independent overlays for each stream

## When to Use

### **Perfect For:**
- **Multi-Camera Security Setup**: Verify camera stability and positioning across multiple cameras
- **Surveillance System Calibration**: Ensure optimal camera placement with independent analysis
- **Video Quality Assessment**: Analyze video clarity and consistency across multiple streams
- **Research Applications**: Study camera behavior and environmental factors with per-topic analysis
- **System Integration**: Validate video input quality in production systems with multi-stream support
- **Troubleshooting**: Diagnose video quality issues across different video sources
- **A/B Testing**: Compare different video processing approaches with independent analysis
- **Pipeline Branching**: Analyze different processing paths independently

### **Consider Alternatives For:**
- **Real-time Processing**: High-latency analysis may not suit real-time applications
- **Simple Video Playback**: Overkill for basic video viewing
- **Batch Processing**: Designed for continuous analysis, not batch operations

## Performance Tuning

### Shake Detection Sensitivity
- **Lower threshold (1-3)**: More sensitive, detects subtle movements
- **Higher threshold (10-20)**: Less sensitive, only major shake events
- **Default (5)**: Balanced approach for most use cases

### Movement Detection
- **Lower threshold (0.1-0.5)**: Detects small movements and drift
- **Higher threshold (2.0-5.0)**: Only significant camera movements
- **Default (1.0)**: Good balance for typical surveillance scenarios

### Analysis Features
- **Camera Stability**: Adds shake detection overhead but provides stability analysis
- **Video Properties**: Minimal overhead, provides technical video information
- **Movement Detection**: Adds optical flow processing overhead but provides movement analysis

## Troubleshooting

### Common Issues

**High CPU Usage**
- Disable movement detection if not needed (`FILTER_CALCULATE_MOVEMENT=false`)
- Disable video properties calculation if not needed (`FILTER_CALCULATE_VIDEO_PROPERTIES=false`)
- Use lower resolution input videos
- Increase `FILTER_LOG_INTERVAL` to reduce processing frequency

**False Positive Shake Detection**
- Increase `FILTER_SHAKE_THRESHOLD` value
- Check for environmental vibrations (fans, machinery)
- Verify camera mounting stability

**Missing Analysis Data**
- Ensure the filter is properly configured with required parameters
- Check that input video is accessible and readable
- Verify Webvis port is available

**Poor Video Quality**
- Check input video resolution and bitrate
- Ensure adequate lighting conditions
- Verify camera focus and positioning

<Admonition type="tip" title="Pro Tip">
For best results, run Visual Calibration on a representative sample of your video content to establish optimal threshold values for your specific use case and environment.
</Admonition>

<Admonition type="warning" title="Important">
Ensure the input video file is accessible and the output directory has write permissions. The filter will automatically create output directories but requires proper file system access.
</Admonition>