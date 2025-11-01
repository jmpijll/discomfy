"""
Unit tests for ComfyUI client.

Following pytest best practices.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import aiohttp

from core.comfyui.client import ComfyUIClient
from core.exceptions import ComfyUIError


@pytest.mark.asyncio
class TestComfyUIClient:
    """Test ComfyUIClient class."""
    
    async def test_initialize_creates_session(self):
        """Test that initialize creates a ClientSession."""
        client = ComfyUIClient(base_url="http://localhost:8188")
        
        await client.initialize()
        
        assert client.session is not None
        assert isinstance(client.session, aiohttp.ClientSession)
        assert not client.session.closed
    
    async def test_close_closes_session(self):
        """Test that close properly closes the session."""
        client = ComfyUIClient(base_url="http://localhost:8188")
        await client.initialize()
        
        await client.close()
        
        assert client.session.closed
        assert client._initialized is False
    
    async def test_context_manager(self):
        """Test async context manager support."""
        async with ComfyUIClient(base_url="http://localhost:8188") as client:
            assert client.session is not None
            assert not client.session.closed
        
        # Session should be closed after context exit
        assert client.session.closed
    
    async def test_queue_prompt_success(self):
        """Test successful prompt queueing."""
        client = ComfyUIClient(base_url="http://localhost:8188")
        await client.initialize()
        
        workflow = {"1": {"inputs": {}, "class_type": "Test"}}
        
        # Mock successful response
        with patch.object(client.session, 'post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value="success")
            mock_response.json = AsyncMock(return_value={"prompt_id": "test_id_123"})
            mock_post.return_value.__aenter__.return_value = mock_response
            
            prompt_id = await client.queue_prompt(workflow)
            
            assert prompt_id == "test_id_123"
            mock_post.assert_called_once()
    
    async def test_queue_prompt_missing_prompt_id(self):
        """Test that missing prompt_id raises ComfyUIError."""
        client = ComfyUIClient(base_url="http://localhost:8188")
        await client.initialize()
        
        workflow = {"1": {"inputs": {}, "class_type": "Test"}}
        
        with patch.object(client.session, 'post') as mock_post:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value="success")
            mock_response.json = AsyncMock(return_value={})  # No prompt_id
            mock_post.return_value.__aenter__.return_value = mock_response
            
            with pytest.raises(ComfyUIError) as exc_info:
                await client.queue_prompt(workflow)
            
            assert "prompt_id" in str(exc_info.value).lower()
    
    async def test_test_connection_success(self):
        """Test successful connection test."""
        client = ComfyUIClient(base_url="http://localhost:8188")
        await client.initialize()
        
        with patch.object(client.session, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_get.return_value.__aenter__.return_value = mock_response
            
            result = await client.test_connection()
            
            assert result is True
    
    async def test_test_connection_failure(self):
        """Test connection test failure."""
        client = ComfyUIClient(base_url="http://localhost:8188")
        await client.initialize()
        
        with patch.object(client.session, 'get') as mock_get:
            mock_get.side_effect = aiohttp.ClientError("Connection failed")
            
            result = await client.test_connection()
            
            assert result is False
    
    async def test_get_history_success(self):
        """Test successful history retrieval."""
        client = ComfyUIClient(base_url="http://localhost:8188")
        await client.initialize()
        
        prompt_id = "test_id_123"
        expected_history = {
            prompt_id: {
                "outputs": {},
                "status": {"completed": True}
            }
        }
        
        with patch.object(client.session, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.text = AsyncMock(return_value="success")
            mock_response.json = AsyncMock(return_value=expected_history)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            history = await client.get_history(prompt_id)
            
            assert history == expected_history
    
    async def test_download_output_success(self):
        """Test successful output download."""
        client = ComfyUIClient(base_url="http://localhost:8188")
        await client.initialize()
        
        expected_data = b"fake_image_data"
        
        with patch.object(client.session, 'get') as mock_get:
            mock_response = AsyncMock()
            mock_response.status = 200
            mock_response.read = AsyncMock(return_value=expected_data)
            mock_get.return_value.__aenter__.return_value = mock_response
            
            data = await client.download_output("test.png", "output", "output")
            
            assert data == expected_data

