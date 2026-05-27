#!/usr/bin/env python3
"""
Unit tests for validators.py in slack-gif-creator

Tests GIF validation for Slack including:
- Emoji GIF validation (dimensions, size)
- Message GIF validation
- File size checks
- Frame count and duration calculations
- Error handling
"""

import unittest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, Mock
import sys

# Mock PIL if not installed (common in CI environments)
try:
    import PIL
except ImportError:
    sys.modules['PIL'] = Mock()
    sys.modules['PIL.Image'] = Mock()

from validators import validate_gif, is_slack_ready


class TestValidators(unittest.TestCase):
    """Test suite for slack-gif-creator validators.py"""

    def create_mock_gif(self, width, height, frame_count=10, duration_ms=100, size_kb=50):
        """Helper to create a mock GIF file with metadata"""
        temp_dir = tempfile.mkdtemp()
        gif_path = Path(temp_dir) / "test.gif"

        # Create a small file to simulate the GIF
        gif_path.write_bytes(b'\x00' * int(size_kb * 1024))

        return gif_path, width, height, frame_count, duration_ms

    @patch('PIL.Image')
    def test_validate_emoji_optimal_dimensions(self, mock_image_class):
        """Test validation of optimal emoji dimensions (128x128)"""
        gif_path, width, height, frames, duration = self.create_mock_gif(128, 128)

        # Mock PIL Image
        mock_img = MagicMock()
        mock_img.size = (128, 128)
        mock_img.info.get.return_value = 100
        mock_img.seek.side_effect = [None] * 10 + [EOFError()]
        mock_image_class.open.return_value.__enter__.return_value = mock_img

        passes, results = validate_gif(gif_path, is_emoji=True, verbose=False)

        self.assertTrue(passes)
        self.assertEqual(results['width'], 128)
        self.assertEqual(results['height'], 128)
        self.assertTrue(results['optimal'])

    @patch('PIL.Image')
    def test_validate_emoji_acceptable_dimensions(self, mock_image_class):
        """Test validation of acceptable emoji dimensions (64-128, square)"""
        gif_path, width, height, frames, duration = self.create_mock_gif(100, 100)

        mock_img = MagicMock()
        mock_img.size = (100, 100)
        mock_img.info.get.return_value = 100
        mock_img.seek.side_effect = [None] * 10 + [EOFError()]
        mock_image_class.open.return_value.__enter__.return_value = mock_img

        passes, results = validate_gif(gif_path, is_emoji=True, verbose=False)

        self.assertTrue(passes)
        self.assertEqual(results['width'], 100)
        self.assertEqual(results['height'], 100)
        self.assertFalse(results['optimal'])

    @patch('PIL.Image')
    def test_validate_emoji_too_small(self, mock_image_class):
        """Test validation fails for emoji too small (<64px)"""
        gif_path, width, height, frames, duration = self.create_mock_gif(50, 50)

        mock_img = MagicMock()
        mock_img.size = (50, 50)
        mock_img.info.get.return_value = 100
        mock_img.seek.side_effect = [None] * 10 + [EOFError()]
        mock_image_class.open.return_value.__enter__.return_value = mock_img

        passes, results = validate_gif(gif_path, is_emoji=True, verbose=False)

        self.assertFalse(passes)

    @patch('PIL.Image')
    def test_validate_emoji_too_large(self, mock_image_class):
        """Test validation fails for emoji too large (>128px)"""
        gif_path, width, height, frames, duration = self.create_mock_gif(150, 150)

        mock_img = MagicMock()
        mock_img.size = (150, 150)
        mock_img.info.get.return_value = 100
        mock_img.seek.side_effect = [None] * 10 + [EOFError()]
        mock_image_class.open.return_value.__enter__.return_value = mock_img

        passes, results = validate_gif(gif_path, is_emoji=True, verbose=False)

        self.assertFalse(passes)

    @patch('PIL.Image')
    def test_validate_emoji_not_square(self, mock_image_class):
        """Test validation fails for non-square emoji"""
        gif_path, width, height, frames, duration = self.create_mock_gif(128, 100)

        mock_img = MagicMock()
        mock_img.size = (128, 100)
        mock_img.info.get.return_value = 100
        mock_img.seek.side_effect = [None] * 10 + [EOFError()]
        mock_image_class.open.return_value.__enter__.return_value = mock_img

        passes, results = validate_gif(gif_path, is_emoji=True, verbose=False)

        self.assertFalse(passes)

    @patch('PIL.Image')
    def test_validate_message_gif_valid_dimensions(self, mock_image_class):
        """Test validation of message GIF with valid dimensions"""
        gif_path, width, height, frames, duration = self.create_mock_gif(480, 320)

        mock_img = MagicMock()
        mock_img.size = (480, 320)
        mock_img.info.get.return_value = 100
        mock_img.seek.side_effect = [None] * 10 + [EOFError()]
        mock_image_class.open.return_value.__enter__.return_value = mock_img

        passes, results = validate_gif(gif_path, is_emoji=False, verbose=False)

        self.assertTrue(passes)
        self.assertEqual(results['width'], 480)
        self.assertEqual(results['height'], 320)

    @patch('PIL.Image')
    def test_validate_message_gif_aspect_ratio_too_high(self, mock_image_class):
        """Test validation fails for message GIF with aspect ratio >2:1"""
        gif_path, width, height, frames, duration = self.create_mock_gif(640, 200)

        mock_img = MagicMock()
        mock_img.size = (640, 200)
        mock_img.info.get.return_value = 100
        mock_img.seek.side_effect = [None] * 10 + [EOFError()]
        mock_image_class.open.return_value.__enter__.return_value = mock_img

        passes, results = validate_gif(gif_path, is_emoji=False, verbose=False)

        self.assertFalse(passes)

    @patch('PIL.Image')
    def test_validate_frame_count(self, mock_image_class):
        """Test that frame count is correctly calculated"""
        gif_path, width, height, frames, duration = self.create_mock_gif(128, 128)

        mock_img = MagicMock()
        mock_img.size = (128, 128)
        mock_img.info.get.return_value = 100
        # Simulate 15 frames
        mock_img.seek.side_effect = [None] * 15 + [EOFError()]
        mock_image_class.open.return_value.__enter__.return_value = mock_img

        passes, results = validate_gif(gif_path, is_emoji=True, verbose=False)

        self.assertEqual(results['frame_count'], 15)

    @patch('PIL.Image')
    def test_validate_calculates_duration(self, mock_image_class):
        """Test that duration and FPS are calculated correctly"""
        gif_path, width, height, frames, duration = self.create_mock_gif(128, 128)

        mock_img = MagicMock()
        mock_img.size = (128, 128)
        mock_img.info.get.return_value = 50  # 50ms per frame
        mock_img.seek.side_effect = [None] * 20 + [EOFError()]  # 20 frames
        mock_image_class.open.return_value.__enter__.return_value = mock_img

        passes, results = validate_gif(gif_path, is_emoji=True, verbose=False)

        # 20 frames * 50ms = 1000ms = 1 second
        self.assertEqual(results['frame_count'], 20)
        self.assertAlmostEqual(results['duration_seconds'], 1.0, places=1)
        self.assertAlmostEqual(results['fps'], 20.0, places=1)

    @patch('PIL.Image')
    def test_validate_file_size_reporting(self, mock_image_class):
        """Test that file size is correctly reported in KB and MB"""
        gif_path, width, height, frames, duration = self.create_mock_gif(128, 128, size_kb=1500)

        mock_img = MagicMock()
        mock_img.size = (128, 128)
        mock_img.info.get.return_value = 100
        mock_img.seek.side_effect = [None] * 10 + [EOFError()]
        mock_image_class.open.return_value.__enter__.return_value = mock_img

        passes, results = validate_gif(gif_path, is_emoji=True, verbose=False)

        self.assertAlmostEqual(results['size_kb'], 1500, delta=10)
        self.assertAlmostEqual(results['size_mb'], 1.5, delta=0.05)

    def test_validate_nonexistent_file(self):
        """Test validation fails gracefully for nonexistent file"""
        passes, results = validate_gif("/nonexistent/file.gif", verbose=False)

        self.assertFalse(passes)
        self.assertIn('error', results)
        self.assertIn('not found', results['error'])

    @patch('PIL.Image')
    def test_validate_corrupted_gif(self, mock_image_class):
        """Test validation fails gracefully for corrupted GIF"""
        gif_path, width, height, frames, duration = self.create_mock_gif(128, 128)

        mock_image_class.open.side_effect = Exception("Corrupted file")

        passes, results = validate_gif(gif_path, verbose=False)

        self.assertFalse(passes)
        self.assertIn('error', results)
        self.assertIn('Failed to read GIF', results['error'])

    @patch('PIL.Image')
    def test_is_slack_ready_emoji(self, mock_image_class):
        """Test is_slack_ready convenience function for emoji"""
        gif_path, width, height, frames, duration = self.create_mock_gif(128, 128)

        mock_img = MagicMock()
        mock_img.size = (128, 128)
        mock_img.info.get.return_value = 100
        mock_img.seek.side_effect = [None] * 10 + [EOFError()]
        mock_image_class.open.return_value.__enter__.return_value = mock_img

        result = is_slack_ready(gif_path, is_emoji=True, verbose=False)

        self.assertTrue(result)

    @patch('PIL.Image')
    def test_is_slack_ready_message_gif(self, mock_image_class):
        """Test is_slack_ready convenience function for message GIF"""
        gif_path, width, height, frames, duration = self.create_mock_gif(480, 320)

        mock_img = MagicMock()
        mock_img.size = (480, 320)
        mock_img.info.get.return_value = 100
        mock_img.seek.side_effect = [None] * 10 + [EOFError()]
        mock_image_class.open.return_value.__enter__.return_value = mock_img

        result = is_slack_ready(gif_path, is_emoji=False, verbose=False)

        self.assertTrue(result)

    @patch('PIL.Image')
    def test_validate_results_structure(self, mock_image_class):
        """Test that results dictionary has expected structure"""
        gif_path, width, height, frames, duration = self.create_mock_gif(128, 128)

        mock_img = MagicMock()
        mock_img.size = (128, 128)
        mock_img.info.get.return_value = 100
        mock_img.seek.side_effect = [None] * 10 + [EOFError()]
        mock_image_class.open.return_value.__enter__.return_value = mock_img

        passes, results = validate_gif(gif_path, is_emoji=True, verbose=False)

        # Check all expected keys are present
        expected_keys = {
            'file', 'passes', 'width', 'height', 'size_kb', 'size_mb',
            'frame_count', 'duration_seconds', 'fps', 'is_emoji', 'optimal'
        }
        self.assertEqual(set(results.keys()), expected_keys)


if __name__ == '__main__':
    unittest.main()
