"""
Workflow loading and validation manager.

Following best practices for file I/O and error handling.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

from core.exceptions import WorkflowError


class WorkflowManager:
    """Manages workflow loading and validation."""
    
    def __init__(self, workflows_dir: str = "workflows"):
        """
        Initialize workflow manager.
        
        Args:
            workflows_dir: Directory containing workflow JSON files
        """
        self.workflows_dir = Path(workflows_dir)
        self._workflow_cache: Dict[str, Dict[str, Any]] = {}
    
    def load_workflow(self, workflow_file: str) -> Dict[str, Any]:
        """Load workflow from file.
        
        Args:
            workflow_file: Name of the workflow file
            
        Returns:
            Workflow dictionary
            
        Raises:
            WorkflowError: If workflow cannot be loaded
        """
        # Check cache first
        if workflow_file in self._workflow_cache:
            return self._workflow_cache[workflow_file]
        
        workflow_path = self.workflows_dir / workflow_file
        
        if not workflow_path.exists():
            raise WorkflowError(f"Workflow file not found: {workflow_path}")
        
        try:
            with open(workflow_path, 'r', encoding='utf-8') as f:
                workflow = json.load(f)
            
            # Validate workflow structure
            self._validate_workflow(workflow)
            
            # Cache for future use
            self._workflow_cache[workflow_file] = workflow
            
            return workflow
            
        except json.JSONDecodeError as e:
            raise WorkflowError(f"Invalid JSON in workflow file: {e}")
        except Exception as e:
            raise WorkflowError(f"Failed to load workflow: {e}")
    
    def _validate_workflow(self, workflow: Dict[str, Any]) -> None:
        """Validate workflow structure.
        
        Args:
            workflow: Workflow dictionary to validate
            
        Raises:
            WorkflowError: If workflow is invalid
        """
        if not isinstance(workflow, dict):
            raise WorkflowError("Workflow must be a dictionary")
        
        if len(workflow) == 0:
            raise WorkflowError("Workflow is empty")
        
        # Check that all nodes have required fields
        for node_id, node_data in workflow.items():
            if not isinstance(node_data, dict):
                raise WorkflowError(f"Node {node_id} is not a dictionary")
            
            if 'class_type' not in node_data:
                raise WorkflowError(f"Node {node_id} missing 'class_type'")
    
    def clear_cache(self) -> None:
        """Clear workflow cache."""
        self._workflow_cache.clear()
    
    def list_workflows(self) -> list[str]:
        """List all available workflow files.
        
        Returns:
            List of workflow file names
        """
        if not self.workflows_dir.exists():
            return []
        
        return [
            f.name for f in self.workflows_dir.iterdir()
            if f.suffix == '.json' and f.is_file()
        ]





