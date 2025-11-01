"""
Unit tests for progress tracker.

Following pytest best practices.
"""

import pytest
from core.progress.tracker import ProgressTracker, ProgressStatus


class TestProgressTracker:
    """Test ProgressTracker class."""
    
    def test_initial_state(self):
        """Test initial tracker state."""
        tracker = ProgressTracker()
        
        assert tracker.state.status == ProgressStatus.INITIALIZING
        assert tracker.state.metrics.percentage == 0.0
        assert tracker.state.phase == "Preparing"
    
    def test_update_step_progress(self):
        """Test updating step progress."""
        tracker = ProgressTracker()
        tracker.update_execution_start()
        
        tracker.update_step_progress(5, 10)
        
        assert tracker.state.metrics.current_step == 5
        assert tracker.state.metrics.total_steps == 10
        assert tracker.state.status == ProgressStatus.RUNNING
    
    def test_update_node_execution(self):
        """Test updating node execution."""
        tracker = ProgressTracker()
        tracker.update_execution_start()
        
        tracker.update_node_execution("node_1")
        
        assert tracker._current_node_id == "node_1"
    
    def test_mark_completed(self):
        """Test marking progress as completed."""
        tracker = ProgressTracker()
        tracker.update_step_progress(10, 10)
        
        tracker.mark_completed()
        
        assert tracker.state.status == ProgressStatus.COMPLETED
        assert tracker.state.phase == "Complete"
    
    def test_update_queue_status(self):
        """Test updating queue status."""
        tracker = ProgressTracker()
        
        tracker.update_queue_status(3)
        
        assert tracker.state.status == ProgressStatus.QUEUED
        assert tracker.state.queue_position == 3
    
    def test_metrics_percentage(self):
        """Test percentage calculation."""
        tracker = ProgressTracker()
        tracker.update_execution_start()
        tracker.update_step_progress(5, 10)
        
        # Should calculate percentage from steps
        assert tracker.state.metrics.percentage > 0.0
    
    def test_to_user_friendly(self):
        """Test converting to user-friendly format."""
        tracker = ProgressTracker()
        tracker.update_execution_start()
        tracker.update_step_progress(5, 10)
        
        title, description, color = tracker.state.to_user_friendly()
        
        assert title is not None
        assert description is not None
        assert isinstance(color, int)

