import unittest
from unittest.mock import patch, MagicMock
from vizcal.filter import Vizcal, VizcalConfig
from openfilter.filter_runtime import Frame
import numpy as np

class TestVizcal(unittest.TestCase):

    def setUp(self):
        self.config = VizcalConfig(
            calculate_camera_stability=True,
            calculate_video_properties=True,
            calculate_movement=False,
            shake_threshold=5,
            movement_threshold=1.0,
            roi=[0, 0, 640, 480],
            forward_upstream_data=True,
            show_text_overlays=True,
            log_interval=3
        )
        # Mock the download_cached_files method to avoid model download
        with patch('openfilter.filter_runtime.filter.Filter.download_cached_files'):
            self.vizcal = Vizcal(self.config)

    def test_normalize_config(self):
        config = Vizcal.normalize_config(self.config)
        self.assertIsInstance(config, VizcalConfig)
        self.assertTrue(config.calculate_camera_stability)  # Should be True
        self.assertTrue(config.calculate_video_properties)  # Should be True
        self.assertFalse(config.calculate_movement)  # Should be False

    def test_setup(self):
        self.vizcal.setup(self.config)
        self.assertTrue(self.vizcal.calculate_camera_stability)  # Should be True
        self.assertTrue(self.vizcal.calculate_video_properties)  # Should be True
        self.assertFalse(self.vizcal.calculate_movement)  # Should be False
        self.assertEqual(self.vizcal.roi, [0, 0, 640, 480])
        self.assertEqual(self.vizcal.movement_threshold, 1.0)
        self.assertEqual(self.vizcal.shake_threshold, 5)
        self.assertTrue(self.vizcal.forward_upstream_data)  # Should be True
        self.assertTrue(self.vizcal.show_text_overlays)  # Should be True
        self.assertEqual(self.vizcal.log_interval, 3)

    def test_calculate_camera_stability_metrics(self):
        """Test camera stability metrics calculation."""
        # Mock the camera stability calculation
        with patch.object(self.vizcal, 'calculate_camera_stability_metrics') as mock_calc:
            mock_calc.return_value = {'shake_distance': 0.5, 'is_stable': True}
            
            # Test that the method can be called
            result = mock_calc()
            self.assertEqual(result['shake_distance'], 0.5)
            self.assertTrue(result['is_stable'])

    @patch('vizcal.filter.detect_camera_shake')
    def test_calculate_camera_stability_metrics(self, mock_detect_camera_shake):
        mock_detect_camera_shake.return_value = (0.5, True)
        frame = np.zeros((480, 640, 3), dtype=np.uint8)
        
        # Ensure the filter is properly set up
        with patch('openfilter.filter_runtime.filter.Filter.download_cached_files'):
            self.vizcal.setup(self.config)
        
        self.vizcal.prv_frame = np.zeros((480, 640, 3), dtype=np.uint8)  # Ensure prv_frame is not None
        result = self.vizcal.calculate_camera_stability_metrics(frame)
        self.assertIsInstance(result, dict)
        self.assertIn('Average Shake Distance', result)
        self.assertIn('Camera Stability Category', result)

    @patch('vizcal.filter.flag_stability')
    @patch('vizcal.filter.text_on_image')
    @patch('vizcal.filter.calc_video_properties')
    @patch('vizcal.filter.convert_dict_to_serializable')
    def test_process_single_topic(self, mock_convert_dict_to_serializable, mock_calc_video_properties, mock_text_on_image, mock_flag_stability):
        mock_calc_video_properties.return_value = {'Frame Width': 640, 'Frame Height': 480}
        mock_convert_dict_to_serializable.return_value = {'test': 'data'}
        # Create a dummy image
        dummy_image = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_text_on_image.return_value = dummy_image
        mock_flag_stability.return_value = dummy_image

        frames = {'main': MagicMock()}
        frames['main'].rw.image = dummy_image
        frames['main'].rw.data = {'meta': {'src': 'file://test.mp4'}}

        self.vizcal.setup(self.config)
        result = self.vizcal.process(frames)
        self.assertIsInstance(result, dict)
        self.assertIn('main', result)
        self.assertIsInstance(result['main'], Frame)

    @patch('vizcal.filter.flag_stability')
    @patch('vizcal.filter.text_on_image')
    @patch('vizcal.filter.calc_video_properties')
    @patch('vizcal.filter.convert_dict_to_serializable')
    def test_process_multi_topic(self, mock_convert_dict_to_serializable, mock_calc_video_properties, mock_text_on_image, mock_flag_stability):
        """Test processing multiple topics with independent analysis."""
        mock_calc_video_properties.return_value = {'Frame Width': 640, 'Frame Height': 480}
        mock_convert_dict_to_serializable.return_value = {'test': 'data'}
        # Create a dummy image
        dummy_image = np.zeros((480, 640, 3), dtype=np.uint8)
        mock_text_on_image.return_value = dummy_image
        mock_flag_stability.return_value = dummy_image

        # Create frames with multiple topics
        frames = {
            'main': MagicMock(),
            'stream2': MagicMock()
        }
        frames['main'].rw.image = dummy_image
        frames['main'].rw.data = {'meta': {'src': 'file://test.mp4'}}
        frames['stream2'].rw.image = dummy_image
        frames['stream2'].rw.data = {'meta': {'src': 'file://test.mp4'}}

        self.vizcal.setup(self.config)
        result = self.vizcal.process(frames)
        
        # Should process both topics
        self.assertIsInstance(result, dict)
        self.assertIn('main', result)
        self.assertIn('stream2', result)
        self.assertIsInstance(result['main'], Frame)
        self.assertIsInstance(result['stream2'], Frame)
        
        # Each topic should have independent state
        self.assertIn('main', self.vizcal.topic_states)
        self.assertIn('stream2', self.vizcal.topic_states)
        
        # Topic states should be independent
        self.assertNotEqual(self.vizcal.topic_states['main'], self.vizcal.topic_states['stream2'])

    def test_topic_state_initialization(self):
        """Test that topic states are properly initialized."""
        self.vizcal.setup(self.config)
        
        # Initially no topic states
        self.assertEqual(len(self.vizcal.topic_states), 0)
        
        # Create frames with multiple topics
        dummy_image = np.zeros((480, 640, 3), dtype=np.uint8)
        frames = {
            'main': MagicMock(),
            'stream2': MagicMock(),
            'stream3': MagicMock()
        }
        
        for topic, frame in frames.items():
            frame.rw.image = dummy_image
            frame.rw.data = {'meta': {'src': 'file://test.mp4'}}
            frame.has_image = True
        
        # Process frames - should initialize topic states
        with patch('vizcal.filter.convert_dict_to_serializable', return_value={}):
            result = self.vizcal.process(frames)
        
        # Should have created states for all topics
        self.assertEqual(len(self.vizcal.topic_states), 3)
        self.assertIn('main', self.vizcal.topic_states)
        self.assertIn('stream2', self.vizcal.topic_states)
        self.assertIn('stream3', self.vizcal.topic_states)
        
        # Each topic state should have required fields
        for topic_state in self.vizcal.topic_states.values():
            self.assertIn('prv_frame', topic_state)
            self.assertIn('old_gray', topic_state)
            self.assertIn('p0', topic_state)
            self.assertIn('video_properties_calculated', topic_state)
            self.assertIn('video_properties', topic_state)
            self.assertIn('frame_count', topic_state)

    def test_non_image_frame_forwarding(self):
        """Test that non-image frames are forwarded as-is."""
        self.vizcal.setup(self.config)
        
        # Create a non-image frame
        non_image_frame = MagicMock()
        non_image_frame.has_image = False
        
        frames = {'metadata': non_image_frame}
        
        result = self.vizcal.process(frames)
        
        # Non-image frame should be forwarded as-is
        self.assertIn('metadata', result)
        self.assertEqual(result['metadata'], non_image_frame)

if __name__ == '__main__':
    unittest.main()