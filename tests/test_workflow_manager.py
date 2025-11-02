"""
Unit tests for workflow manager.

Following pytest best practices.
"""

import pytest
from unittest.mock import Mock, patch, mock_open
import json
from pathlib import Path

from core.comfyui.workflows.manager import WorkflowManager
from core.exceptions import WorkflowError


@pytest.mark.asyncio
class TestWorkflowManager:
    """Test WorkflowManager class."""
    
    def test_load_workflow_success(self, sample_workflow):
        """Test successful workflow loading."""
        manager = WorkflowManager(workflows_dir="test_workflows")
        
        workflow_file = "test_workflow.json"
        workflow_path = Path("test_workflows") / workflow_file
        
        with patch.object(Path, "exists", return_value=True):
            with patch("builtins.open", mock_open(read_data=json.dumps(sample_workflow))):
                workflow = manager.load_workflow(workflow_file)
                
                assert workflow is not None
                assert "1" in workflow
    
    def test_load_workflow_not_found(self):
        """Test loading non-existent workflow raises error."""
        manager = WorkflowManager()
        
        workflow_file = "nonexistent.json"
        workflow_path = manager.workflows_dir / workflow_file
        
        with patch.object(Path, "exists", return_value=False):
            with pytest.raises(WorkflowError):
                manager.load_workflow(workflow_file)
    
    def test_load_workflow_invalid_json(self):
        """Test loading invalid JSON raises error."""
        manager = WorkflowManager()
        
        workflow_file = "invalid.json"
        workflow_path = manager.workflows_dir / workflow_file
        
        with patch("builtins.open", mock_open(read_data="invalid json")):
            with patch.object(Path, "exists", return_value=True):
                with pytest.raises(WorkflowError):
                    manager.load_workflow(workflow_file)
    
    def test_validate_workflow_structure(self, sample_workflow):
        """Test workflow structure validation."""
        manager = WorkflowManager()
        
        # Valid workflow should pass (via load_workflow)
        workflow_file = "test.json"
        with patch("builtins.open", mock_open(read_data=json.dumps(sample_workflow))):
            with patch.object(Path, "exists", return_value=True):
                workflow = manager.load_workflow(workflow_file)
                assert workflow is not None
        
        # Invalid workflow should fail
        invalid_workflow = {"invalid": "structure"}
        with pytest.raises(WorkflowError):
            manager._validate_workflow(invalid_workflow)
    
    def test_get_workflow_cached(self, sample_workflow):
        """Test that workflows are cached after first load."""
        manager = WorkflowManager()
        
        workflow_file = "test_workflow.json"
        with patch("builtins.open", mock_open(read_data=json.dumps(sample_workflow))):
            with patch.object(Path, "exists", return_value=True):
                # Load twice
                workflow1 = manager.load_workflow(workflow_file)
                workflow2 = manager.load_workflow(workflow_file)
                
                # Should be the same object (cached)
                assert workflow1 is workflow2
    
    def test_clear_cache(self, sample_workflow):
        """Test clearing workflow cache."""
        manager = WorkflowManager()
        
        workflow_file = "test_workflow.json"
        with patch("builtins.open", mock_open(read_data=json.dumps(sample_workflow))):
            with patch.object(Path, "exists", return_value=True):
                # Load workflow
                workflow1 = manager.load_workflow(workflow_file)
                
                # Clear cache
                manager.clear_cache()
                
                # Load again (should create new object, but same content)
                workflow2 = manager.load_workflow(workflow_file)
                
                # Should have same content
                assert workflow1 == workflow2
    
    def test_list_workflows(self):
        """Test listing available workflows."""
        manager = WorkflowManager()
        
        # Create proper Path mock objects
        mock_file1 = Mock(spec=Path)
        mock_file1.name = "workflow1.json"
        mock_file1.suffix = ".json"
        mock_file1.is_file.return_value = True
        
        mock_file2 = Mock(spec=Path)
        mock_file2.name = "workflow2.json"
        mock_file2.suffix = ".json"
        mock_file2.is_file.return_value = True
        
        mock_file3 = Mock(spec=Path)
        mock_file3.name = "not_a_workflow.txt"
        mock_file3.suffix = ".txt"
        mock_file3.is_file.return_value = True
        
        mock_files = [mock_file1, mock_file2, mock_file3]
        
        # Patch at the Path class level
        with patch.object(Path, "exists", return_value=True):
            with patch.object(Path, "iterdir", return_value=mock_files):
                workflows = manager.list_workflows()
                
                # Should return only .json files
                assert len(workflows) == 2
                assert "workflow1.json" in workflows
                assert "workflow2.json" in workflows
