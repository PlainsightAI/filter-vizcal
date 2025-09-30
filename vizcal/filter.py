import logging, sys, os, json, cv2
import numpy as np
from openfilter.filter_runtime.filter import FilterConfig, Filter, Frame
from vizcal.vizcal_utils.video_properties import calc_video_properties, detect_camera_shake, text_on_image, flag_stability, KEYS_TO_INCLUDE
from vizcal.vizcal_utils.utils import convert_dict_to_serializable

# Expose VizcalConfig and Vizcal to external modules
__all__ = ['VizcalConfig', 'Vizcal']

logger = logging.getLogger(__name__)

class VizcalConfig(FilterConfig):
    """Configuration class for Vizcal - lightweight video metrics calculator"""
    # Metrics to calculate
    calculate_camera_stability: bool = True
    calculate_video_properties: bool = True
    calculate_movement:         bool = True
    
    # Camera stability settings
    shake_threshold:            int = 5
    
    # Movement detection settings  
    movement_threshold:         float = 1.0
    
    # ROI for analysis (optional)
    roi:                        list[int] = []
    
    # Data forwarding
    forward_upstream_data:      bool = True  # Forward data from upstream filters
    
    # Visual overlays
    show_text_overlays:         bool = True  # Show text overlays on video frames
    
    # Output settings
    log_interval:               int = 3  # Log every N frames
    

class Vizcal(Filter):
    """
    Lightweight video metrics calculator that can be configured to calculate
    specific video analysis metrics like camera stability, video properties, and movement.
    """
    
    @classmethod
    def normalize_config(cls, config: VizcalConfig):
        config = VizcalConfig(super().normalize_config(config))
        
        # Convert string booleans to actual booleans
        bool_fields = ['calculate_camera_stability', 'calculate_video_properties', 'calculate_movement', 'forward_upstream_data', 'show_text_overlays']
        for field in bool_fields:
            if hasattr(config, field) and isinstance(getattr(config, field), str):
                setattr(config, field, getattr(config, field).lower() == 'true')
        
        # Convert string numbers to proper types
        if isinstance(config.shake_threshold, str):
            config.shake_threshold = int(config.shake_threshold)
        if isinstance(config.movement_threshold, str):
            config.movement_threshold = float(config.movement_threshold)
        if isinstance(config.log_interval, str):
            config.log_interval = int(config.log_interval)
        
        logger.info(f"VizCal configuration: {config}")
        return config
    
    
    def setup(self, config: VizcalConfig, **kwargs):
        """
        Initializes the metrics calculator with the specified configuration.

        Args:
            config (VizcalConfig): The configuration for Vizcal.
        """
        
        # Store configuration
        self.config = config
        self.frame_no = 0
        
        # Initialize metrics flags
        self.calculate_camera_stability = config.calculate_camera_stability
        self.calculate_video_properties = config.calculate_video_properties
        self.calculate_movement = config.calculate_movement
        
        # Set other configuration attributes
        self.shake_threshold = config.shake_threshold
        self.movement_threshold = config.movement_threshold
        self.roi = config.roi
        self.forward_upstream_data = config.forward_upstream_data
        self.show_text_overlays = config.show_text_overlays
        
        # Initialize per-topic state tracking
        self.topic_states = {}
        
        # Initialize camera stability tracking
        if self.calculate_camera_stability:
            self.prv_frame = None
        
        # Initialize movement tracking
        if self.calculate_movement:
            # Optical flow parameters for movement tracking
            self.old_gray = None
            self.p0 = None
            self.feature_params = dict(maxCorners=100, qualityLevel=0.3, minDistance=7, blockSize=7)
            self.lk_params = dict(winSize=(15, 15), maxLevel=2, criteria=(cv2.TERM_CRITERIA_EPS | cv2.TERM_CRITERIA_COUNT, 10, 0.03))
        
        # Initialize video properties
        if self.calculate_video_properties:
            self.video_properties_calculated = False
        
        # Output settings
        self.log_interval = config.log_interval

    def shutdown(self):
        """
        Shutdown function to cleanup resources and log final statistics.
        """
        logger.info("VizCal filter shutting down...")
        
        # Log final statistics
        if hasattr(self, 'frame_no'):
            logger.info(f"Processed {self.frame_no} frames total")
        
        # Log camera stability statistics if enabled
        if self.calculate_camera_stability and hasattr(self, 'prv_frame') and self.prv_frame is not None:
            logger.info("Camera stability analysis completed")
        
        # Log video properties if calculated
        if self.calculate_video_properties and hasattr(self, 'video_properties_calculated') and self.video_properties_calculated:
            logger.info("Video properties analysis completed")
        
        # Log movement analysis if enabled
        if self.calculate_movement and hasattr(self, 'old_gray') and self.old_gray is not None:
            logger.info("Movement analysis completed")
        
        # Clean up resources
        if hasattr(self, 'prv_frame'):
            self.prv_frame = None
        
        if hasattr(self, 'old_gray'):
            self.old_gray = None
        
        if hasattr(self, 'p0'):
            self.p0 = None
        
        logger.info("VizCal filter shutdown complete - all resources cleaned up")

    def calculate_camera_stability_metrics(self, frame):
        """
        Calculates camera stability metrics for the current frame.

        Args:
            frame (numpy.ndarray): The current video frame.

        Returns:
            dict: A dictionary with camera stability metrics.
        """
        if not self.calculate_camera_stability:
            return {}
            
        shaky_bool = False
        avg_distance = 0
        if self.prv_frame is not None:
            avg_distance, shaky_bool = detect_camera_shake(self.prv_frame, frame, self.shake_threshold)
        
        stability_category = "Video Unstable - Camera might be Shaking" if shaky_bool else "Video is Stable"
        self.prv_frame = frame

        metrics = {
            "Average Shake Distance": round(float(avg_distance), 2),
            "Camera Stability Category": stability_category
        }
        
        return metrics

    def calculate_video_properties_metrics(self, data):
        """
        Calculates video properties metrics.
        
        Args:
            data: Frame data containing metadata
            
        Returns:
            dict: Video properties metrics
        """
        if not self.calculate_video_properties or self.video_properties_calculated:
            return {}
            
        file_path = data['meta']['src'].replace('file://', '')
        logger.info(f"Calculating video properties for: {file_path}")
        
        self.video_properties = calc_video_properties(file_path)
        
        # Set ROI if not specified
        if not self.roi:
            self.roi = [0, 0, self.video_properties['Frame Width'], self.video_properties['Frame Height']]
        
        self.video_properties_calculated = True
        return self.video_properties

    def calculate_movement_metrics(self, frame):
        """
        Calculates movement metrics for the current frame.
        
        Args:
            frame (numpy.ndarray): The current video frame.
            
        Returns:
            dict: Movement metrics
        """
        if not self.calculate_movement:
            return {}
            
        # Convert to grayscale for optical flow
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        if self.old_gray is not None:
            # Calculate optical flow
            p1, st, err = cv2.calcOpticalFlowPyrLK(self.old_gray, gray, self.p0, None, **self.lk_params)
            
            if p1 is not None and st is not None:
                # Select good points
                good_new = p1[st == 1]
                good_old = self.p0[st == 1]
                
                if len(good_new) > 0 and len(good_old) > 0:
                    # Calculate movement distances
                    distances = np.linalg.norm(good_new - good_old, axis=1)
                    avg_movement = float(np.mean(distances))
                    
                    # Update points for next frame
                    self.p0 = good_new.reshape(-1, 1, 2)
                    
                    return {
                        "Movement Distance": round(avg_movement, 2),
                        "Movement Detected": avg_movement > self.movement_threshold
                    }
        
        # Initialize for first frame
        self.p0 = cv2.goodFeaturesToTrack(gray, mask=None, **self.feature_params)
        self.old_gray = gray.copy()
        
        return {"Movement Distance": 0.0, "Movement Detected": False}

    def calculate_camera_stability_metrics_per_topic(self, frame, topic_state):
        """
        Calculates camera stability metrics for the current frame using per-topic state.

        Args:
            frame (numpy.ndarray): The current video frame.
            topic_state (dict): Per-topic state dictionary.

        Returns:
            dict: A dictionary with camera stability metrics.
        """
        if not self.calculate_camera_stability:
            return {}
            
        shaky_bool = False
        avg_distance = 0
        if topic_state['prv_frame'] is not None:
            avg_distance, shaky_bool = detect_camera_shake(topic_state['prv_frame'], frame, self.shake_threshold)
        
        stability_category = "Video Unstable - Camera might be Shaking" if shaky_bool else "Video is Stable"
        topic_state['prv_frame'] = frame

        metrics = {
            "Average Shake Distance": round(float(avg_distance), 2),
            "Camera Stability Category": stability_category
        }
        
        return metrics

    def calculate_movement_metrics_per_topic(self, frame, topic_state):
        """
        Calculates movement metrics for the current frame using per-topic state.
        
        Args:
            frame (numpy.ndarray): The current video frame.
            topic_state (dict): Per-topic state dictionary.
            
        Returns:
            dict: Movement metrics
        """
        if not self.calculate_movement:
            return {}
            
        # Convert to grayscale for optical flow
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        if topic_state['old_gray'] is not None:
            # Calculate optical flow
            p1, st, err = cv2.calcOpticalFlowPyrLK(topic_state['old_gray'], gray, topic_state['p0'], None, **self.lk_params)
            
            if p1 is not None and st is not None:
                # Select good points
                good_new = p1[st == 1]
                good_old = topic_state['p0'][st == 1]
                
                if len(good_new) > 0 and len(good_old) > 0:
                    # Calculate movement distances
                    distances = np.linalg.norm(good_new - good_old, axis=1)
                    avg_movement = float(np.mean(distances))
                    
                    # Update points for next frame
                    topic_state['p0'] = good_new.reshape(-1, 1, 2)
                    
                    return {
                        "Movement Distance": round(avg_movement, 2),
                        "Movement Detected": avg_movement > self.movement_threshold
                    }
        
        # Initialize for first frame
        topic_state['p0'] = cv2.goodFeaturesToTrack(gray, mask=None, **self.feature_params)
        topic_state['old_gray'] = gray.copy()
        
        return {"Movement Distance": 0.0, "Movement Detected": False}

    def process(self, frames: dict[str, Frame]):
        """
        Main processing function that calculates configured metrics for video frames.
        Processes all incoming topics and forwards data in the same topic names.
        Maintains separate state for each topic to avoid cross-contamination.
        """
        output_frames = {}
        
        # Process each incoming topic
        for topic_name, frame in frames.items():
            if not frame.has_image:
                # Forward non-image frames as-is if upstream forwarding is enabled
                if self.config.forward_upstream_data:
                    output_frames[topic_name] = frame
                continue
                
            image = frame.rw.image
            data = frame.rw.data

            # Initialize topic state if not exists
            if topic_name not in self.topic_states:
                self.topic_states[topic_name] = {
                    'prv_frame': None,
                    'old_gray': None,
                    'p0': None,
                    'video_properties_calculated': False,
                    'video_properties': {},
                    'frame_count': 0
                }

            topic_state = self.topic_states[topic_name]

            # Initialize frame data
            frame_data = {
                "frame_number": topic_state['frame_count'],
                "meta": data.get('meta', {}),
            }

            # Calculate video properties (only once per topic, but include in every frame)
            if self.calculate_video_properties and not topic_state['video_properties_calculated']:
                video_props = self.calculate_video_properties_metrics(data)
                if video_props:
                    frame_data.update(video_props)
                    topic_state['video_properties'] = video_props
                    topic_state['video_properties_calculated'] = True
            elif self.calculate_video_properties and topic_state['video_properties']:
                # Include video properties in every frame after they're calculated
                frame_data.update(topic_state['video_properties'])

            # Calculate camera stability metrics (per-topic)
            stability_metrics = self.calculate_camera_stability_metrics_per_topic(image, topic_state)
            if stability_metrics:
                frame_data.update(stability_metrics)

            # Calculate movement metrics (per-topic)
            movement_metrics = self.calculate_movement_metrics_per_topic(image, topic_state)
            if movement_metrics:
                frame_data.update(movement_metrics)

            # Add visual overlays if enabled and camera stability is being calculated
            if self.config.show_text_overlays and self.calculate_camera_stability and stability_metrics:
                image = text_on_image(image, frame_data)
                image = flag_stability(image, frame_data)
            
            # Prepare output data - include all frame data, not just filtered
            data_serializable = convert_dict_to_serializable(frame_data)
            
            # Create output frame with the same topic name
            output_frames[topic_name] = Frame(image, {**data, **data_serializable}, format='BGR')
            
            # Update topic frame count
            topic_state['frame_count'] += 1
        
        self.frame_no += 1
        
        # Ensure main topic comes first in the output dictionary
        if 'main' in output_frames:
            main_frame = output_frames.pop('main')
            return {'main': main_frame, **output_frames}
        
        return output_frames

    def get_name(self):
        """Returns the name of the filter."""
        return "Vizcal"


if __name__ == '__main__':
    Vizcal.run()
