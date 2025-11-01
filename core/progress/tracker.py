"""
Progress tracking for generation tasks.

Simplified design with clear separation of state and metrics.
Following Pydantic best practices from Context7.
"""

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List, Tuple, Dict, Any

from pydantic import BaseModel, Field, ConfigDict


class ProgressStatus(str, Enum):
    """Progress status enumeration."""
    INITIALIZING = "initializing"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class ProgressMetrics(BaseModel):
    """Metrics for progress calculation with Pydantic validation."""
    total_steps: int = Field(default=0, ge=0, description="Total sampling steps")
    current_step: int = Field(default=0, ge=0, description="Current step")
    total_nodes: int = Field(default=0, ge=0, description="Total nodes in workflow")
    completed_nodes: int = Field(default=0, ge=0, description="Completed nodes")
    cached_nodes: set[str] = Field(default_factory=set, description="Cached nodes")
    percentage: float = Field(default=0.0, ge=0.0, le=100.0, description="Progress percentage")
    
    model_config = ConfigDict(arbitrary_types_allowed=True, validate_assignment=True)


@dataclass
class ProgressState:
    """Current state of generation progress.
    
    Using dataclass for mutable state tracking while keeping
    metrics in immutable Pydantic model.
    """
    status: ProgressStatus = ProgressStatus.INITIALIZING
    queue_position: int = 0
    start_time: float = field(default_factory=time.time)
    metrics: ProgressMetrics = field(default_factory=ProgressMetrics)
    phase: str = "Preparing"
    
    def to_user_friendly(self) -> Tuple[str, str, int]:
        """Convert to user-friendly format for Discord embeds.
        
        Returns:
            Tuple of (title, description, color)
        """
        elapsed = time.time() - self.start_time
        
        if self.status == ProgressStatus.QUEUED:
            title = "⏳ Queued"
            description = f"Position #{self.queue_position} in queue\nWaiting time: {self._format_time(elapsed)}"
            color = 0xFFA500  # Orange
        elif self.status == ProgressStatus.RUNNING:
            title = "🎨 Generating"
            description = f"{self.metrics.percentage:.1f}% | {self.phase}"
            color = 0x3498DB  # Blue
        elif self.status == ProgressStatus.COMPLETED:
            title = "✅ Complete"
            description = f"Completed in {self._format_time(elapsed)}"
            color = 0x2ECC71  # Green
        else:
            title = "🔄 Preparing"
            description = f"{self.phase}..."
            color = 0x3498DB  # Blue
        
        return title, description, color
    
    @staticmethod
    def _format_time(seconds: float) -> str:
        """Format time in human-readable way."""
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m {int(seconds % 60)}s"
        else:
            return f"{int(seconds // 3600)}h {int((seconds % 3600) // 60)}m"


class ProgressTracker:
    """Tracks and manages generation progress.
    
    Simplified design:
    - Separation of state and metrics
    - Clear progression through states
    - Time estimation based on history
    """
    
    def __init__(self):
        """Initialize progress tracker."""
        self.state = ProgressState()
        self._history: List[Tuple[float, float]] = []  # (time, percentage)
        self._workflow_nodes: set[str] = set()
        self._executed_nodes: set[str] = set()
        self._cached_nodes: set[str] = set()
        self._current_node_id: Optional[str] = None
        self._execution_started: bool = False
        self._first_step_reached: bool = False
        self._current_step_sequence: int = 0
    
    def set_workflow_nodes(self, workflow: Dict[str, Any]) -> None:
        """Initialize with all nodes from workflow for accurate progress tracking.
        
        Args:
            workflow: Workflow dictionary
        """
        self._workflow_nodes = set(workflow.keys())
        self.state.metrics.total_nodes = len(self._workflow_nodes)
    
    def update_queue_status(self, position: int) -> None:
        """Update queue position.
        
        Args:
            position: Queue position
        """
        self.state.status = ProgressStatus.QUEUED
        self.state.queue_position = position
        self.state.phase = f"In queue (#{position})"
        self.state.metrics.current_step = 0
        self.state.metrics.total_steps = 0
    
    def update_execution_start(self) -> None:
        """Update when execution starts."""
        if self.state.status != ProgressStatus.RUNNING:
            self.state.status = ProgressStatus.RUNNING
            self.state.queue_position = 0
            self._execution_started = True
            self.state.start_time = time.time()
            if not self._first_step_reached:
                self.state.phase = "Loading"
    
    def update_cached_nodes(self, cached_nodes: List[str]) -> None:
        """Update when nodes are cached (execution skipped).
        
        Args:
            cached_nodes: List of cached node IDs
        """
        if not self._execution_started:
            return
        
        for node_id in cached_nodes:
            if node_id in self._workflow_nodes:
                self._cached_nodes.add(node_id)
                self.state.metrics.cached_nodes.add(node_id)
    
    def update_node_execution(self, node_id: str) -> None:
        """Update when a new node starts executing.
        
        Args:
            node_id: Node ID that started executing
        """
        if not self._execution_started:
            return
        
        self._current_node_id = node_id
        
        if node_id and node_id != "None" and node_id in self._workflow_nodes:
            self._executed_nodes.add(node_id)
            self.state.metrics.completed_nodes = len(self._executed_nodes)
    
    def update_step_progress(self, current: int, total: int) -> None:
        """Update step progress (primary progress method).
        
        Args:
            current: Current step number
            total: Total steps
        """
        if not self._execution_started:
            return
        
        self.state.metrics.current_step = current
        self.state.metrics.total_steps = total
        
        # Mark that we've reached the first step
        if current > 0 and not self._first_step_reached:
            self._first_step_reached = True
            self.state.phase = f"Sampling ({current}/{total})"
        
        if total > 0 and current > 0:
            # Check if this is a new sequence (for multi-iteration workflows)
            if current == 1 and self.state.metrics.current_step > 1:
                self._current_step_sequence += 1
            
            # Calculate step-based progress
            if self._first_step_reached:
                # For single sequence (normal generation)
                if self._current_step_sequence == 0:
                    step_percentage = (current / total) * 100
                    self.state.metrics.percentage = min(95, step_percentage)  # Reserve 5% for finalization
                else:
                    # For multi-sequence (upscaling)
                    estimated_sequences = 4
                    sequence_weight = 100 / estimated_sequences
                    current_seq_progress = (current / total) * sequence_weight
                    previous_seq_progress = self._current_step_sequence * sequence_weight
                    self.state.metrics.percentage = min(95, previous_seq_progress + current_seq_progress)
                
                # Update phase
                if self._current_step_sequence > 0:
                    self.state.phase = f"Upscaling - Pass {self._current_step_sequence + 1} ({current}/{total})"
                else:
                    self.state.phase = f"Sampling ({current}/{total})"
                
                # Track progress for time estimation
                self._update_history()
    
    def update_from_websocket(self, message: Dict[str, Any]) -> None:
        """Update progress from WebSocket message.
        
        Args:
            message: WebSocket message dictionary
        """
        msg_type = message.get('type')
        data = message.get('data', {})
        
        if msg_type == 'progress':
            # Update step progress
            current = data.get('value', 0)
            total = data.get('max', 0)
            
            self.state.metrics.current_step = current
            self.state.metrics.total_steps = total
            
            if current > 0:
                self.state.phase = f"Sampling ({current}/{total})"
                self._update_history()
                
        elif msg_type == 'executing':
            node_id = data.get('node')
            if node_id:
                # Node executing
                self.update_node_execution(node_id)
            else:
                # Execution complete
                self.state.status = ProgressStatus.COMPLETED
        
        elif msg_type == 'execution_cached':
            # Nodes were cached (skipped)
            cached = set(data.get('nodes', []))
            self.update_cached_nodes(list(cached))
    
    def mark_completed(self) -> None:
        """Mark the process as completed."""
        self.state.status = ProgressStatus.COMPLETED
        self.state.metrics.current_step = self.state.metrics.total_steps
        self.state.metrics.percentage = 100.0
        self.state.phase = "Complete"
    
    def estimate_time_remaining(self) -> Optional[float]:
        """Estimate time remaining based on progress history.
        
        Returns:
            Estimated seconds remaining, or None if not enough data
        """
        if len(self._history) < 2:
            return None
        
        # Use last 5 data points for estimation
        recent = self._history[-5:]
        time_diff = recent[-1][0] - recent[0][0]
        progress_diff = recent[-1][1] - recent[0][1]
        
        if time_diff > 0 and progress_diff > 0:
            rate = progress_diff / time_diff  # % per second
            remaining = 100 - self.state.metrics.percentage
            return min(remaining / rate, 600)  # Cap at 10 minutes
        
        return None
    
    def _update_history(self) -> None:
        """Update progress history for time estimation."""
        self._history.append((
            time.time(),
            self.state.metrics.percentage
        ))
        # Keep only last 10 data points
        if len(self._history) > 10:
            self._history.pop(0)
    
    def format_time(self, seconds: float) -> str:
        """Format time in a human-readable way.
        
        Args:
            seconds: Time in seconds
            
        Returns:
            Formatted time string
        """
        if seconds is None or seconds <= 0:
            return "Unknown"
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m {int(seconds % 60)}s"
        else:
            return f"{int(seconds // 3600)}h {int((seconds % 3600) // 60)}m"

