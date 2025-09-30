"""
Smoke tests for VizCal filter.
Basic end-to-end tests to ensure the filter initializes and performs core functions.
"""

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock
import numpy as np
import pytest

from vizcal.filter import Vizcal, VizcalConfig
from openfilter.filter_runtime import Frame


class TestSmokeSimple:
    """Smoke tests for basic VizCal functionality."""

    def test_filter_initialization(self):
        """Test that the filter can be initialized with valid config."""
        config_data = {
            'calculate_camera_stability': True,
            'calculate_video_properties': True,
            'calculate_movement': False,
            'shake_threshold': 10,
            'movement_threshold': 1.5,
            'roi': [100, 200, 300, 400],
            'forward_upstream_data': True,
            'show_text_overlays': True,
            'log_interval': 3
        }
        
        # Test config normalization
        config = Vizcal.normalize_config(config_data)
        assert config.calculate_camera_stability is True
        assert config.calculate_video_properties is True
        assert config.calculate_movement is False
        assert config.shake_threshold == 10
        assert config.movement_threshold == 1.5
        assert config.roi == [100, 200, 300, 400]
        assert config.forward_upstream_data is True
        assert config.show_text_overlays is True
        assert config.log_interval == 3
        
        # Test filter initialization
        filter_instance = Vizcal(config=config)
        assert filter_instance is not None

    def test_setup_and_shutdown(self, temp_workdir):
        """Test that setup() and shutdown() work correctly."""
        config_data = {
            'calculate_camera_stability': True,
            'calculate_video_properties': True,
            'calculate_movement': False,
            'shake_threshold': 15,
            'movement_threshold': 2.0,
            'roi': [50, 100, 200, 300],
            'forward_upstream_data': True,
            'show_text_overlays': True,
            'log_interval': 3
        }
        
        config = Vizcal.normalize_config(config_data)
        filter_instance = Vizcal(config=config)
        
        # Mock the download_cached_files method to avoid model download
        with patch('openfilter.filter_runtime.filter.Filter.download_cached_files'):
            # Test setup
            filter_instance.setup(config)
            assert filter_instance.config is not None
            assert filter_instance.calculate_camera_stability is True
            assert filter_instance.calculate_video_properties is True
            assert filter_instance.calculate_movement is False
            assert filter_instance.shake_threshold == 15
            assert filter_instance.movement_threshold == 2.0
            assert filter_instance.roi == [50, 100, 200, 300]
            assert filter_instance.forward_upstream_data is True
            assert filter_instance.show_text_overlays is True
            assert filter_instance.log_interval == 3
            
            # Mock the nested_config to avoid KeyError in shutdown
            filter_instance.nested_config = {
                'video_properties': {},
                'output_json_path': os.path.join(temp_workdir, 'test_output.json')
            }
            filter_instance.frames_data = []
            
            # Test shutdown
            filter_instance.shutdown()  # Should not raise any exceptions

    def test_config_validation(self):
        """Test that config validation works correctly."""
        config_data = {
            'calculate_camera_stability': 'true',  # String that should be converted
            'calculate_video_properties': 'false',  # String that should be converted
            'calculate_movement': 'true',  # String that should be converted
            'shake_threshold': '25',  # String that should be converted
            'movement_threshold': '1.8',  # String that should be converted
            'roi': '[10, 20, 30, 40]',  # String that should be converted
            'forward_upstream_data': 'false',  # String that should be converted
            'show_text_overlays': 'true',  # String that should be converted
            'log_interval': '5'  # String that should be converted
        }
        
        config = Vizcal.normalize_config(config_data)
        assert config.calculate_camera_stability is True
        assert config.calculate_video_properties is False
        assert config.calculate_movement is True
        assert config.shake_threshold == 25  # Now properly converted
        assert config.movement_threshold == 1.8  # Now properly converted
        assert config.forward_upstream_data is False
        assert config.show_text_overlays is True
        assert config.log_interval == 5

    @patch('vizcal.filter.detect_camera_shake')
    @patch('vizcal.filter.calc_video_properties')
    @patch('vizcal.filter.text_on_image')
    @patch('vizcal.filter.flag_stability')
    def test_frame_processing(self, mock_flag_stability, mock_text_on_image, 
                            mock_calc_video_properties, mock_detect_camera_shake):
        """Test basic frame processing."""
        config_data = {
            'calculate_camera_stability': True,
            'calculate_video_properties': True,
            'calculate_movement': False,
            'shake_threshold': 5,
            'movement_threshold': 1.0,
            'roi': [0, 0, 640, 480],
            'forward_upstream_data': True,
            'show_text_overlays': True,
            'log_interval': 3
        }
        
        config = Vizcal.normalize_config(config_data)
        filter_instance = Vizcal(config=config)
        
        # Mock the setup method
        with patch('openfilter.filter_runtime.filter.Filter.download_cached_files'):
            filter_instance.setup(config)
        
        # Mock the return values
        mock_calc_video_properties.return_value = {'Frame Width': 640, 'Frame Height': 480}
        mock_detect_camera_shake.return_value = (0.5, True)
        mock_text_on_image.return_value = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_flag_stability.return_value = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Create a test frame
        test_image = np.zeros((480, 640, 3), dtype=np.uint8)
        frame = Frame(image=test_image, data={'meta': {'src': 'file://test.mp4'}}, format='BGR')
        frames = {'main': frame}
        
        # Process the frame
        result = filter_instance.process(frames)
        assert isinstance(result, dict)
        assert 'main' in result
        assert isinstance(result['main'], Frame)

    def test_empty_frame_processing(self):
        """Test processing with empty frame dictionary."""
        config_data = {
            'calculate_camera_stability': True,
            'calculate_video_properties': True,
            'calculate_movement': False,
            'shake_threshold': 5,
            'movement_threshold': 1.0,
            'forward_upstream_data': True,
            'show_text_overlays': True,
            'log_interval': 3
        }
        
        config = Vizcal.normalize_config(config_data)
        filter_instance = Vizcal(config=config)
        
        # Mock the setup method
        with patch('openfilter.filter_runtime.filter.Filter.download_cached_files'):
            filter_instance.setup(config)
        
        # Test with empty frames - VizCal now handles empty frames gracefully
        empty_frames = {}
        result = filter_instance.process(empty_frames)
        
        # Should return empty result for empty input
        assert isinstance(result, dict)
        assert len(result) == 0

    def test_missing_main_frame(self):
        """Test processing when main frame is missing but other topics exist."""
        config_data = {
            'calculate_camera_stability': True,
            'calculate_video_properties': True,
            'calculate_movement': False,
            'shake_threshold': 5,
            'movement_threshold': 1.0,
            'forward_upstream_data': True,
            'show_text_overlays': True,
            'log_interval': 3
        }
        
        config = Vizcal.normalize_config(config_data)
        filter_instance = Vizcal(config=config)
        
        # Mock the setup method
        with patch('openfilter.filter_runtime.filter.Filter.download_cached_files'):
            filter_instance.setup(config)
        
        # Test with frames missing 'main' key - VizCal now processes all topics
        frame = Frame(image=np.zeros((480, 640, 3), dtype=np.uint8), data={'meta': {'src': 'file://test.mp4'}}, format='BGR')
        frames_without_main = {'other': frame}
        
        result = filter_instance.process(frames_without_main)
        
        # Should process the 'other' topic successfully
        assert isinstance(result, dict)
        assert 'other' in result
        assert isinstance(result['other'], Frame)

    def test_forward_upstream_data_disabled(self):
        """Test processing when forward_upstream_data is disabled - should not forward non-image frames."""
        config_data = {
            'calculate_camera_stability': True,
            'calculate_video_properties': True,
            'calculate_movement': True,
            'forward_upstream_data': False,  # Disable upstream data forwarding
            'show_text_overlays': True,
            'debug': True
        }
    
        config = Vizcal.normalize_config(config_data)
        filter_instance = Vizcal(config=config)
    
        filter_instance.setup(config)
    
        # Create sample frames
        sample_frame = Frame(image=np.zeros((480, 640, 3), dtype=np.uint8), data={'meta': {'src': 'file://test.mp4'}}, format='BGR')
        
        # Process frames with multiple topics
        frames = {
            "main": sample_frame,
            "stream2": sample_frame,
            "data_only": Frame({"some": "data"})  # Data-only frame
        }
        output_frames = filter_instance.process(frames)
    
        # Verify output (should process all image topics, but not forward data_only)
        assert "main" in output_frames
        assert "stream2" in output_frames  # Should be processed (image frame)
        assert "data_only" not in output_frames  # Should not be forwarded (non-image frame)
        assert len(output_frames) == 2  # Only image topics processed
        
        # Verify main topic comes first
        output_keys = list(output_frames.keys())
        assert output_keys[0] == "main"

    def test_main_topic_ordering(self):
        """Test that main topic always comes first in output dictionary."""
        config_data = {
            'calculate_camera_stability': True,
            'calculate_video_properties': True,
            'calculate_movement': True,
            'forward_upstream_data': True,
            'show_text_overlays': True,
            'debug': True
        }
    
        config = Vizcal.normalize_config(config_data)
        filter_instance = Vizcal(config=config)
    
        filter_instance.setup(config)
    
        # Create sample frames
        sample_frame = Frame(image=np.zeros((480, 640, 3), dtype=np.uint8), data={'meta': {'src': 'file://test.mp4'}}, format='BGR')
        
        # Process frames with multiple topics in different order
        frames = {
            "stream2": sample_frame,
            "main": sample_frame,
            "other": sample_frame
        }
        output_frames = filter_instance.process(frames)
    
        # Verify main topic comes first regardless of input order
        output_keys = list(output_frames.keys())
        assert output_keys[0] == "main"
        assert len(output_frames) == 3  # All topics processed

    def test_different_shake_thresholds(self):
        """Test processing with different shake thresholds."""
        shake_thresholds = [1, 5, 10, 25, 50]
        
        for threshold in shake_thresholds:
            config_data = {
                'calculate_camera_stability': True,
                'calculate_video_properties': True,
                'calculate_movement': False,
                'shake_threshold': threshold,
                'movement_threshold': 1.0,
                'forward_upstream_data': True,
                'show_text_overlays': True,
                'log_interval': 3
            }
            
            config = Vizcal.normalize_config(config_data)
            filter_instance = Vizcal(config=config)
            
            # Mock the setup method
            with patch('openfilter.filter_runtime.filter.Filter.download_cached_files'):
                filter_instance.setup(config)
            
            assert filter_instance.shake_threshold == threshold

    def test_different_movement_thresholds(self):
        """Test processing with different movement thresholds."""
        movement_thresholds = [0.1, 0.5, 1.0, 2.0, 5.0]
        
        for threshold in movement_thresholds:
            config_data = {
                'calculate_camera_stability': True,
                'calculate_video_properties': True,
                'calculate_movement': True,
                'shake_threshold': 5,
                'movement_threshold': threshold,
                'forward_upstream_data': True,
                'show_text_overlays': True,
                'log_interval': 3
            }
            
            config = Vizcal.normalize_config(config_data)
            filter_instance = Vizcal(config=config)
            
            # Mock the setup method
            with patch('openfilter.filter_runtime.filter.Filter.download_cached_files'):
                filter_instance.setup(config)
            
            assert filter_instance.movement_threshold == threshold

    def test_movement_detection_enabled(self):
        """Test processing with movement detection enabled."""
        config_data = {
            'calculate_camera_stability': True,
            'calculate_video_properties': True,
            'calculate_movement': True,
            'shake_threshold': 5,
            'movement_threshold': 1.0,
            'forward_upstream_data': True,
            'show_text_overlays': True,
            'log_interval': 3
        }
        
        config = Vizcal.normalize_config(config_data)
        filter_instance = Vizcal(config=config)
        
        # Mock the setup method
        with patch('openfilter.filter_runtime.filter.Filter.download_cached_files'):
            filter_instance.setup(config)
        
        assert filter_instance.calculate_movement is True

    def test_string_config_conversion(self):
        """Test that string configs are properly converted to types."""
        # Test with string values that should be converted
        config_data = {
            'calculate_camera_stability': 'true',
            'calculate_video_properties': 'false',
            'calculate_movement': 'true',
            'shake_threshold': '15',
            'movement_threshold': '2.5',
            'roi': '[100, 200, 300, 400]',
            'forward_upstream_data': 'false',
            'show_text_overlays': 'true',
            'log_interval': '5'
        }
        
        config = Vizcal.normalize_config(config_data)
        
        # Check that string values are converted to correct types
        assert config.calculate_camera_stability is True
        assert config.calculate_video_properties is False
        assert config.calculate_movement is True
        assert config.shake_threshold == 15  # Now properly converted
        assert config.movement_threshold == 2.5  # Now properly converted
        assert config.forward_upstream_data is False
        assert config.show_text_overlays is True
        assert config.log_interval == 5

    def test_error_handling_invalid_config(self):
        """Test error handling for invalid configuration values."""
        # Test with invalid boolean value
        config_invalid_boolean = {
            'calculate_camera_stability': 'maybe',  # Invalid value
            'shake_threshold': 5
        }
        
        # Should handle gracefully
        config = Vizcal.normalize_config(config_invalid_boolean)
        assert isinstance(config, VizcalConfig)

    def test_environment_variable_loading(self):
        """Test environment variable configuration loading."""
        # Set environment variables
        os.environ['FILTER_CALCULATE_CAMERA_STABILITY'] = 'true'
        os.environ['FILTER_CALCULATE_VIDEO_PROPERTIES'] = 'false'
        os.environ['FILTER_CALCULATE_MOVEMENT'] = 'true'
        os.environ['FILTER_SHAKE_THRESHOLD'] = '20'
        os.environ['FILTER_MOVEMENT_THRESHOLD'] = '3.0'
        os.environ['FILTER_FORWARD_UPSTREAM_DATA'] = 'false'
        os.environ['FILTER_SHOW_TEXT_OVERLAYS'] = 'true'
        os.environ['FILTER_LOG_INTERVAL'] = '5'
        
        try:
            config = VizcalConfig()
            normalized = Vizcal.normalize_config(config)
            
            # Note: VizCal doesn't currently load from environment variables in normalize_config
            # This test documents the current behavior
            assert normalized.calculate_camera_stability is True  # Default value
            assert normalized.calculate_video_properties is True  # Default value
            assert normalized.calculate_movement is True  # Default value
            assert normalized.shake_threshold == 5  # Default value
            assert normalized.movement_threshold == 1.0  # Default value
            assert normalized.forward_upstream_data is True  # Default value
            assert normalized.show_text_overlays is True  # Default value
            assert normalized.log_interval == 3  # Default value
            
        finally:
            # Clean up environment variables
            for key in ['FILTER_CALCULATE_CAMERA_STABILITY', 'FILTER_CALCULATE_VIDEO_PROPERTIES', 
                       'FILTER_CALCULATE_MOVEMENT', 'FILTER_SHAKE_THRESHOLD', 'FILTER_MOVEMENT_THRESHOLD', 
                       'FILTER_FORWARD_UPSTREAM_DATA', 'FILTER_SHOW_TEXT_OVERLAYS', 'FILTER_LOG_INTERVAL']:
                if key in os.environ:
                    del os.environ[key]

    def test_text_overlays_handling(self):
        """Test text overlays handling."""
        config_data = {
            'calculate_camera_stability': True,
            'calculate_video_properties': True,
            'calculate_movement': False,
            'shake_threshold': 5,
            'movement_threshold': 1.0,
            'forward_upstream_data': True,
            'show_text_overlays': True,
            'log_interval': 3
        }
        
        config = Vizcal.normalize_config(config_data)
        filter_instance = Vizcal(config=config)
        
        # Mock the setup method
        with patch('openfilter.filter_runtime.filter.Filter.download_cached_files'):
            filter_instance.setup(config)
        
        assert filter_instance.show_text_overlays is True


@pytest.fixture
def temp_workdir():
    """Create a temporary working directory for tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir
