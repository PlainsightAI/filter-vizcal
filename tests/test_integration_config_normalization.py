"""
Integration tests for VizCal configuration normalization.
Tests the normalize_config method with various input types and edge cases.
"""

import os
import pytest
import tempfile
from vizcal.filter import Vizcal, VizcalConfig


class TestIntegrationConfigNormalization:
    """Test configuration normalization with various inputs."""

    def test_string_to_type_conversions(self):
        """Test that string configurations are properly converted to correct types."""
        
        config_with_string_values = {
            'calculate_camera_stability': 'true',  # String bool
            'calculate_video_properties': 'false',  # String bool
            'calculate_movement': 'true',  # String bool
            'shake_threshold': '10',  # String int
            'movement_threshold': '2.5',  # String float
            'roi': '[100, 200, 300, 400]',  # String list
            'forward_upstream_data': 'true',  # String bool
            'show_text_overlays': 'false',  # String bool
            'log_interval': '5'  # String int
        }
        
        normalized = Vizcal.normalize_config(config_with_string_values)
        
        # Check that string values are converted to correct types
        assert isinstance(normalized.calculate_camera_stability, bool)
        assert normalized.calculate_camera_stability is True
        assert isinstance(normalized.calculate_video_properties, bool)
        assert normalized.calculate_video_properties is False
        assert isinstance(normalized.calculate_movement, bool)
        assert normalized.calculate_movement is True
        assert isinstance(normalized.shake_threshold, int)
        assert normalized.shake_threshold == 10
        assert isinstance(normalized.movement_threshold, float)
        assert normalized.movement_threshold == 2.5
        assert isinstance(normalized.forward_upstream_data, bool)
        assert normalized.forward_upstream_data is True
        assert isinstance(normalized.show_text_overlays, bool)
        assert normalized.show_text_overlays is False
        assert isinstance(normalized.log_interval, int)
        assert normalized.log_interval == 5

    def test_required_vs_optional_parameters(self):
        """Test that required parameters are validated correctly."""
        
        # Test minimal valid configuration
        minimal_config = {
            'calculate_camera_stability': True,
            'shake_threshold': 5
        }
        
        normalized = Vizcal.normalize_config(minimal_config)
        assert normalized.calculate_camera_stability is True
        assert normalized.shake_threshold == 5
        assert normalized.calculate_video_properties is True  # Default value
        assert normalized.calculate_movement is True  # Default value
        assert normalized.movement_threshold == 1.0  # Default value
        assert normalized.roi == []  # Default value
        assert normalized.forward_upstream_data is True  # Default value
        assert normalized.show_text_overlays is True  # Default value
        assert normalized.log_interval == 3  # Default value

    def test_boolean_validation(self):
        """Test boolean validation and conversion for new configuration parameters."""
        
        # Test valid boolean values for calculate_camera_stability
        valid_values = [True, False, 'true', 'false', 'True', 'False']
        expected_results = [True, False, True, False, True, False]
        
        for value, expected in zip(valid_values, expected_results):
            config = {
                'calculate_camera_stability': value,
                'shake_threshold': 5
            }
            normalized = Vizcal.normalize_config(config)
            assert normalized.calculate_camera_stability == expected

    def test_shake_threshold_validation(self):
        """Test shake threshold validation."""
        
        # Test valid shake thresholds
        valid_thresholds = [1, 5, 10, 50, 100]
        
        for threshold in valid_thresholds:
            config = {
                'calculate_camera_stability': True,
                'shake_threshold': threshold
            }
            normalized = Vizcal.normalize_config(config)
            assert normalized.shake_threshold == threshold

    def test_movement_threshold_validation(self):
        """Test movement threshold validation."""
        
        # Test valid movement thresholds
        valid_thresholds = [0.1, 0.5, 1.0, 2.5, 5.0]
        
        for threshold in valid_thresholds:
            config = {
                'calculate_camera_stability': True,
                'shake_threshold': 5,
                'movement_threshold': threshold
            }
            normalized = Vizcal.normalize_config(config)
            assert normalized.movement_threshold == threshold

    def test_roi_validation(self):
        """Test ROI validation and conversion."""
        
        # Test valid ROI formats
        valid_rois = [
            [100, 200, 300, 400],
            []
        ]
        
        for roi in valid_rois:
            config = {
                'calculate_camera_stability': True,
                'shake_threshold': 5,
                'roi': roi
            }
            normalized = Vizcal.normalize_config(config)
            assert isinstance(normalized.roi, list)
        
        # Test string ROI - VizCal doesn't currently convert string lists
        config_string_roi = {
            'calculate_camera_stability': True,
            'shake_threshold': 5,
            'roi': '[]'
        }
        normalized = Vizcal.normalize_config(config_string_roi)
        # Note: VizCal doesn't currently convert string lists to actual lists
        assert normalized.roi == '[]'  # Currently stays as string

    def test_boolean_configuration(self):
        """Test boolean configuration options for new parameters."""
        
        # Test calculate_camera_stability = True
        config_camera_true = {
            'calculate_camera_stability': True,
            'shake_threshold': 5
        }
        
        normalized = Vizcal.normalize_config(config_camera_true)
        assert normalized.calculate_camera_stability is True
        
        # Test calculate_camera_stability = False
        config_camera_false = {
            'calculate_camera_stability': False,
            'shake_threshold': 5
        }
        
        normalized = Vizcal.normalize_config(config_camera_false)
        assert normalized.calculate_camera_stability is False
        
        # Test calculate_camera_stability = "true" (string)
        config_camera_string_true = {
            'calculate_camera_stability': "true",
            'shake_threshold': 5
        }
        
        normalized = Vizcal.normalize_config(config_camera_string_true)
        assert normalized.calculate_camera_stability is True
        
        # Test calculate_camera_stability = "false" (string)
        config_camera_string_false = {
            'calculate_camera_stability': "false",
            'shake_threshold': 5
        }
        
        normalized = Vizcal.normalize_config(config_camera_string_false)
        assert normalized.calculate_camera_stability is False

    def test_environment_variable_loading(self):
        """Test environment variable configuration loading."""
        
        # Set environment variables
        os.environ['FILTER_CALCULATE_CAMERA_STABILITY'] = 'true'
        os.environ['FILTER_CALCULATE_VIDEO_PROPERTIES'] = 'false'
        os.environ['FILTER_CALCULATE_MOVEMENT'] = 'true'
        os.environ['FILTER_SHAKE_THRESHOLD'] = '15'
        os.environ['FILTER_MOVEMENT_THRESHOLD'] = '2.0'
        os.environ['FILTER_FORWARD_UPSTREAM_DATA'] = 'false'
        os.environ['FILTER_SHOW_TEXT_OVERLAYS'] = 'true'
        os.environ['FILTER_LOG_INTERVAL'] = '5'
        
        try:
            # Test that environment variables are loaded
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

    def test_edge_cases_and_error_handling(self):
        """Test edge cases and error handling."""
        
        # Test with empty configuration
        empty_config = {}
        normalized = Vizcal.normalize_config(empty_config)
        assert isinstance(normalized, VizcalConfig)
        
        # Test with None values
        config_with_none = {
            'calculate_camera_stability': None,
            'shake_threshold': None,
            'movement_threshold': None
        }
        normalized = Vizcal.normalize_config(config_with_none)
        assert isinstance(normalized, VizcalConfig)

    def test_unknown_config_key_validation(self):
        """Test that unknown config keys are handled gracefully."""
        
        config_with_unknown_keys = {
            'calculate_camera_stability': True,
            'shake_threshold': 5,
            'unknown_key': 'unknown_value',
            'another_unknown': 123
        }
        
        # Should not raise an error
        normalized = Vizcal.normalize_config(config_with_unknown_keys)
        assert isinstance(normalized, VizcalConfig)
        assert normalized.calculate_camera_stability is True
        assert normalized.shake_threshold == 5

    def test_runtime_keys_ignored(self):
        """Test that runtime keys are ignored during validation."""
        
        config_with_runtime_keys = {
            'calculate_camera_stability': True,
            'shake_threshold': 5,
            'mq_log': 'pretty',
            'id': 'test_filter',
            'sources': 'tcp://localhost:5550',
            'outputs': 'tcp://localhost:5552'
        }
        
        normalized = Vizcal.normalize_config(config_with_runtime_keys)
        assert isinstance(normalized, VizcalConfig)
        assert normalized.calculate_camera_stability is True
        assert normalized.shake_threshold == 5

    def test_comprehensive_configuration(self):
        """Test a comprehensive configuration with all parameters."""
        
        comprehensive_config = {
            'calculate_camera_stability': True,
            'calculate_video_properties': True,
            'calculate_movement': False,
            'shake_threshold': 25,
            'movement_threshold': 1.5,
            'roi': [100, 150, 200, 250],
            'forward_upstream_data': False,
            'show_text_overlays': True,
            'log_interval': 5
        }
        
        normalized = Vizcal.normalize_config(comprehensive_config)
        
        assert normalized.calculate_camera_stability is True
        assert normalized.calculate_video_properties is True
        assert normalized.calculate_movement is False
        assert normalized.shake_threshold == 25
        assert normalized.movement_threshold == 1.5
        assert normalized.roi == [100, 150, 200, 250]
        assert normalized.forward_upstream_data is False
        assert normalized.show_text_overlays is True
        assert normalized.log_interval == 5
