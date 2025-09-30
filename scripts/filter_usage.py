"""
VizCal Filter Usage Example

This script demonstrates how to use the VizCal filter for video analysis and calibration.
The filter analyzes video properties, camera stability, and movement detection.
Supports multiple video sources and topics with independent analysis per topic.

Environment Variables:
- VIDEO_INPUT: Input video file path (default: ./data/sample-video.mp4)
- OUTPUT_VIDEO_PATH: Output video file path (default: ./output/vizcal_output.mp4)
- OUTPUT_FPS: Output video frames per second (default: 30)
- WEBVIS_PORT: Port for Webvis visualization (default: 8002)
- FILTER_CALCULATE_CAMERA_STABILITY: Enable camera stability calculation (default: True)
- FILTER_CALCULATE_VIDEO_PROPERTIES: Enable video properties calculation (default: True)
- FILTER_CALCULATE_MOVEMENT: Enable movement detection (default: False)
- FILTER_SHAKE_THRESHOLD: Camera shake detection threshold (default: 5)
- FILTER_MOVEMENT_THRESHOLD: Movement detection threshold (default: 1.0)
- FILTER_FORWARD_UPSTREAM_DATA: Forward data from upstream filters (default: True)
- FILTER_SHOW_TEXT_OVERLAYS: Show text overlays on video frames (default: True)
- FILTER_LOG_INTERVAL: Log data every N frames (default: 3)
"""

import sys, os

# Adding current script directory to system path for importing custom modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import custom and filter runtime modules
from openfilter.filter_runtime import Frame, Filter
from openfilter.filter_runtime.filters.video_in import VideoIn
from openfilter.filter_runtime.filters.video_out import VideoOut
from openfilter.filter_runtime.filters.webvis import Webvis
from vizcal.filter import Vizcal, VizcalConfig  # Custom Vizcal filter

def main():
    """
    Main function to process video using a multi-filter pipeline.
    - Video is processed using VideoIn, custom Vizcal filter, and VideoOut filters.
    - Visualization is served using Webvis.
    - Demonstrates multi-topic analysis capabilities.
    """
    
    # Configuration from environment variables
    VIDEO_INPUT = os.getenv("VIDEO_INPUT", "./data/sample-video.mp4")
    FPS = int(os.getenv("OUTPUT_FPS", "30"))
    WEBVIS_PORT = int(os.getenv("WEBVIS_PORT", "8000"))
        
    # VizCal configuration from environment variables
    vizcal_config = {
        'calculate_camera_stability': os.getenv("FILTER_CALCULATE_CAMERA_STABILITY", "True").lower() == "true",
        'calculate_video_properties': os.getenv("FILTER_CALCULATE_VIDEO_PROPERTIES", "True").lower() == "true",
        'calculate_movement': os.getenv("FILTER_CALCULATE_MOVEMENT", "False").lower() == "true",
        'shake_threshold': int(os.getenv("FILTER_SHAKE_THRESHOLD", "5")),
        'movement_threshold': float(os.getenv("FILTER_MOVEMENT_THRESHOLD", "1.0")),
        'forward_upstream_data': os.getenv("FILTER_FORWARD_UPSTREAM_DATA", "True").lower() == "true",
        'show_text_overlays': os.getenv("FILTER_SHOW_TEXT_OVERLAYS", "True").lower() == "true",
        'log_interval': int(os.getenv("FILTER_LOG_INTERVAL", "3")),
    }
    
    print("VizCal Filter Configuration:")
    print(f"  Video Input: {VIDEO_INPUT}")
    print(f"  Topics: main, stream2 (same video, different analysis)")
    print(f"  Output FPS: {FPS}")
    print(f"  Webvis Port: {WEBVIS_PORT}")
    print(f"  Calculate Camera Stability: {vizcal_config['calculate_camera_stability']}")
    print(f"  Calculate Video Properties: {vizcal_config['calculate_video_properties']}")
    print(f"  Calculate Movement: {vizcal_config['calculate_movement']}")
    print(f"  Shake Threshold: {vizcal_config['shake_threshold']}")
    print(f"  Movement Threshold: {vizcal_config['movement_threshold']}")
    print(f"  Forward Upstream Data: {vizcal_config['forward_upstream_data']}")
    print(f"  Show Text Overlays: {vizcal_config['show_text_overlays']}")
    print(f"  Log Interval: {vizcal_config['log_interval']}")
    print()

    # Run the multi-filter pipeline using `Filter.run_multi`
    Filter.run_multi(
        [
            # VideoIn filter: Reads the same video with different topics
            (
                VideoIn,
                dict(
                    id="vidin",  
                    sources=[
                        f'file://{VIDEO_INPUT}!sync!loop;main',
                        f'file://{VIDEO_INPUT}!sync!loop;stream2'
                    ],
                    outputs="tcp://*:5550", 
                ),
            ),
            # Custom Vizcal filter: Processes the same video with different topics
            # Each topic gets independent analysis (camera stability, movement, etc.)
            # This demonstrates how the same video can have different analysis states
            (
                Vizcal,
                VizcalConfig(
                    id="vizcal",  
                    sources=[
                        "tcp://127.0.0.1:5550;main",
                        "tcp://127.0.0.1:5550;stream2"
                    ],
                    outputs="tcp://*:5552",  
                    calculate_camera_stability=vizcal_config['calculate_camera_stability'],
                    calculate_video_properties=vizcal_config['calculate_video_properties'],
                    calculate_movement=vizcal_config['calculate_movement'],
                    shake_threshold=vizcal_config['shake_threshold'],
                    movement_threshold=vizcal_config['movement_threshold'],
                    forward_upstream_data=vizcal_config['forward_upstream_data'],
                    show_text_overlays=vizcal_config['show_text_overlays'],
                    log_interval=vizcal_config['log_interval'],
                    mq_log='pretty',
                ),
            ),
            # Webvis filter: Displays both processed video streams
            (
                Webvis,
                dict(
                    id='webvis', 
                    sources=[
                        'tcp://127.0.0.1:5552;main>main',
                        'tcp://127.0.0.1:5552;stream2>stream2'
                    ],
                    port=WEBVIS_PORT  
                )
            )
        ]
    )
    
    print(f"\nVizCal processing complete!")
    print(f"Webvis: http://localhost:{WEBVIS_PORT}")
    print(f"  - Main stream: http://localhost:{WEBVIS_PORT}/main")
    print(f"  - Stream2: http://localhost:{WEBVIS_PORT}/stream2")
    print(f"Multi-topic analysis:")
    print(f"  - Same video processed with different topics")
    print(f"  - Each topic analyzed independently")
    print(f"  - Per-topic camera stability tracking")
    print(f"  - Per-topic movement detection")
    print(f"  - Per-topic video properties")
    print(f"Metrics calculated:")
    print(f"  - Camera Stability: {vizcal_config['calculate_camera_stability']}")
    print(f"  - Video Properties: {vizcal_config['calculate_video_properties']}")
    print(f"  - Movement Detection: {vizcal_config['calculate_movement']}")

if __name__ == "__main__":
    main()  