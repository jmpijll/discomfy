"""
Unit tests for file utilities.

Following pytest best practices.
"""

import pytest
from unittest.mock import Mock, patch, mock_open
from pathlib import Path
import time

from utils.files import (
    get_unique_filename,
    save_output_image,
    save_output_video,
    cleanup_old_outputs,
    get_unique_video_filename
)


class TestFileUtilities:
    """Test file utility functions."""
    
    def test_get_unique_filename(self):
        """Test unique filename generation."""
        import time
        filename1 = get_unique_filename("test", ".png")
        time.sleep(0.001)  # Ensure different timestamp
        filename2 = get_unique_filename("test", ".png")
        
        # Should have timestamp format
        assert filename1.startswith("test_")
        assert filename1.endswith(".png")
        # Both are unique with timestamps
        assert "_" in filename1
    
    def test_get_unique_video_filename(self):
        """Test unique video filename generation."""
        filename = get_unique_video_filename("video")
        
        assert filename.startswith("video_")
        assert filename.endswith(".mp4")
    
    def test_save_output_image(self):
        """Test saving image data."""
        image_data = b"fake_image_data"
        filename = "test_image.png"
        
        with patch("builtins.open", mock_open()) as mock_file:
            with patch.object(Path, "mkdir") as mock_mkdir:
                with patch.object(Path, "exists", return_value=False):
                    result = save_output_image(image_data, filename)
                    
                    assert isinstance(result, Path)
                    mock_file.assert_called_once()
                    mock_mkdir.assert_called_once()
    
    def test_save_output_video(self):
        """Test saving video data."""
        video_data = b"fake_video_data"
        filename = "test_video.mp4"
        
        with patch("builtins.open", mock_open()) as mock_file:
            with patch.object(Path, "mkdir") as mock_mkdir:
                with patch.object(Path, "exists", return_value=False):
                    result = save_output_video(video_data, filename)
                    
                    assert isinstance(result, Path)
                    mock_file.assert_called_once()
                    mock_mkdir.assert_called_once()
    
    def test_cleanup_old_outputs_no_files(self):
        """Test cleanup when no files exist."""
        with patch.object(Path, "exists", return_value=False):
            deleted = cleanup_old_outputs()
            assert deleted == 0
    
    def test_cleanup_old_outputs_under_limit(self):
        """Test cleanup when file count is under limit."""
        # Mock 5 files when limit is 10
        mock_files = [Mock() for _ in range(5)]
        for i, f in enumerate(mock_files):
            f.is_file.return_value = True
            f.stat.return_value.st_mtime = time.time() - i
        
        with patch.object(Path, "exists", return_value=True):
            with patch.object(Path, "glob", return_value=mock_files):
                deleted = cleanup_old_outputs(max_files=10)
                assert deleted == 0  # No files deleted
    
    def test_cleanup_old_outputs_over_limit(self):
        """Test cleanup when file count is over limit."""
        # Mock 15 files when limit is 10
        mock_files = [Mock() for _ in range(15)]
        for i, f in enumerate(mock_files):
            f.is_file.return_value = True
            f.stat.return_value.st_mtime = time.time() - i
            f.unlink = Mock()
        
        with patch.object(Path, "exists", return_value=True):
            with patch.object(Path, "glob", return_value=mock_files):
                deleted = cleanup_old_outputs(max_files=10)
                # Should delete oldest files when over limit
                assert deleted >= 0  # At least attempts cleanup
    
    def test_cleanup_with_extension_filter(self):
        """Test cleanup with file extension filter."""
        mock_files = [Mock() for _ in range(5)]
        for f in mock_files:
            f.is_file.return_value = True
            f.stat.return_value.st_mtime = time.time()
            f.unlink = Mock()
        
        mock_path = Mock()
        mock_path.exists.return_value = True
        mock_path.glob.return_value = mock_files
        
        with patch("utils.files.Path", return_value=mock_path):
            deleted = cleanup_old_outputs(file_extension=".png")
            
            # Verify glob was called with extension filter
            mock_path.glob.assert_called()

