"""
ComfyUI HTTP API client following aiohttp best practices.

Based on Context7 aiohttp patterns:
- Proper ClientSession lifecycle management
- Async context manager support
- Connection pooling with TCPConnector
"""

import uuid
import json
from typing import Optional, Dict, Any
import aiohttp

from core.exceptions import ComfyUIError


class ComfyUIClient:
    """HTTP-based ComfyUI client following aiohttp best practices.
    
    Based on Context7 aiohttp patterns:
    - Proper ClientSession lifecycle management
    - Async context manager support
    - Connection pooling with TCPConnector
    """
    
    def __init__(self, base_url: str, timeout: int = 300, client_id: Optional[str] = None):
        """
        Initialize ComfyUI client.
        
        Args:
            base_url: Base URL for ComfyUI API (e.g., "http://localhost:8188")
            timeout: Request timeout in seconds
            client_id: Optional client ID (generated if not provided)
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session: Optional[aiohttp.ClientSession] = None
        self._client_id = client_id or str(uuid.uuid4())
        self._initialized = False
        
    async def __aenter__(self):
        """Async context manager entry - creates session with proper config."""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit - properly closes session."""
        await self.close()
    
    async def initialize(self):
        """Initialize the client session.
        
        Following aiohttp best practices from Context7:
        - Create session with proper timeout configuration
        - Use TCPConnector for connection pooling
        """
        if self._initialized and self.session and not self.session.closed:
            return
        
        # Following aiohttp best practices from Context7
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.timeout),
            connector=aiohttp.TCPConnector(
                limit=10,  # Total connection pool limit
                limit_per_host=5  # Per-host connection limit
            )
        )
        self._initialized = True
    
    async def close(self):
        """Close the client session."""
        if self.session and not self.session.closed:
            await self.session.close()
            self._initialized = False
    
    @property
    def client_id(self) -> str:
        """Get the client ID."""
        return self._client_id
    
    async def queue_prompt(self, workflow: Dict[str, Any]) -> str:
        """Queue a prompt and return prompt_id.
        
        Following aiohttp request patterns from Context7.
        
        Args:
            workflow: ComfyUI workflow dictionary
            
        Returns:
            prompt_id from ComfyUI
            
        Raises:
            ComfyUIError: If queueing fails
        """
        if not self.session or self.session.closed:
            raise ComfyUIError("Client session not initialized")
        
        prompt_data = {
            "prompt": workflow,
            "client_id": self._client_id
        }
        
        try:
            # aiohttp best practice: use async with for automatic cleanup
            async with self.session.post(
                f"{self.base_url}/prompt",
                json=prompt_data
            ) as response:
                if response.status != 200:
                    response_text = await response.text()
                    raise ComfyUIError(
                        f"Failed to queue prompt: {response.status} - {response_text}",
                        status_code=response.status
                    )
                
                result = await response.json()
                if 'prompt_id' not in result:
                    raise ComfyUIError(f"No prompt_id in response: {result}")
                
                return result['prompt_id']
                
        except aiohttp.ClientError as e:
            raise ComfyUIError(f"HTTP error while queuing prompt: {e}")
        except json.JSONDecodeError as e:
            raise ComfyUIError(f"Invalid JSON response: {e}")
    
    async def get_history(self, prompt_id: str) -> Dict[str, Any]:
        """Get execution history for a prompt.
        
        Args:
            prompt_id: Prompt ID to get history for
            
        Returns:
            History dictionary from ComfyUI
            
        Raises:
            ComfyUIError: If request fails
        """
        if not self.session or self.session.closed:
            raise ComfyUIError("Client session not initialized")
        
        try:
            async with self.session.get(
                f"{self.base_url}/history/{prompt_id}"
            ) as response:
                if response.status != 200:
                    response_text = await response.text()
                    raise ComfyUIError(
                        f"Failed to get history: {response.status} - {response_text}",
                        status_code=response.status
                    )
                
                return await response.json()
                
        except aiohttp.ClientError as e:
            raise ComfyUIError(f"HTTP error while getting history: {e}")
        except json.JSONDecodeError as e:
            raise ComfyUIError(f"Invalid JSON response: {e}")
    
    async def download_output(
        self,
        filename: str,
        subfolder: str = "",
        output_type: str = "output"
    ) -> bytes:
        """Download generated output file.
        
        Args:
            filename: Name of the file to download
            subfolder: Subfolder path (optional)
            output_type: Output type (default: "output")
            
        Returns:
            File contents as bytes
            
        Raises:
            ComfyUIError: If download fails
        """
        if not self.session or self.session.closed:
            raise ComfyUIError("Client session not initialized")
        
        params = {
            'filename': filename,
            'subfolder': subfolder,
            'type': output_type
        }
        
        try:
            async with self.session.get(
                f"{self.base_url}/view",
                params=params
            ) as response:
                if response.status != 200:
                    raise ComfyUIError(
                        f"Failed to download output: {response.status}",
                        status_code=response.status
                    )
                
                return await response.read()
                
        except aiohttp.ClientError as e:
            raise ComfyUIError(f"HTTP error while downloading output: {e}")
    
    async def get_queue(self) -> Dict[str, Any]:
        """Get current queue status.
        
        Returns:
            Queue information dictionary
            
        Raises:
            ComfyUIError: If request fails
        """
        if not self.session or self.session.closed:
            raise ComfyUIError("Client session not initialized")
        
        try:
            async with self.session.get(f"{self.base_url}/queue") as response:
                if response.status != 200:
                    response_text = await response.text()
                    raise ComfyUIError(
                        f"Failed to get queue: {response.status} - {response_text}",
                        status_code=response.status
                    )
                
                return await response.json()
                
        except aiohttp.ClientError as e:
            raise ComfyUIError(f"HTTP error while getting queue: {e}")
        except json.JSONDecodeError as e:
            raise ComfyUIError(f"Invalid JSON response: {e}")
    
    async def upload_image(self, image_data: bytes, filename: str) -> str:
        """Upload image data to ComfyUI input directory.
        
        Following aiohttp file upload patterns from Context7:
        - Use FormData for multipart/form-data encoding
        - Proper error handling
        
        Args:
            image_data: Image data as bytes
            filename: Desired filename for the image
            
        Returns:
            Uploaded filename from ComfyUI
            
        Raises:
            ComfyUIError: If upload fails
        """
        if not self.session or self.session.closed:
            raise ComfyUIError("Client session not initialized")
        
        try:
            # Create form data for file upload (Context7 pattern)
            data = aiohttp.FormData()
            data.add_field('image', 
                          image_data, 
                          filename=filename, 
                          content_type='image/png')
            
            # Upload to ComfyUI
            async with self.session.post(
                f"{self.base_url}/upload/image",
                data=data
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise ComfyUIError(
                        f"Failed to upload image: {response.status} - {error_text}",
                        status_code=response.status
                    )
                
                result = await response.json()
                uploaded_filename = result.get('name', filename)
                return uploaded_filename
                
        except aiohttp.ClientError as e:
            raise ComfyUIError(f"HTTP error while uploading image: {e}")
        except json.JSONDecodeError as e:
            raise ComfyUIError(f"Invalid JSON response from upload: {e}")
    
    async def test_connection(self) -> bool:
        """Test connection to ComfyUI server.
        
        Returns:
            True if connection is successful, False otherwise
        """
        if not self.session or self.session.closed:
            return False
        
        try:
            async with self.session.get(
                f"{self.base_url}/system_stats",
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                return response.status == 200
        except Exception:
            return False


