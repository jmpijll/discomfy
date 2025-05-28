"""
Image generation component for Discord ComfyUI Bot.
Handles all image generation logic and ComfyUI API calls.
"""

import json
import uuid
import asyncio
import logging
import requests
import random
from io import BytesIO
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union, Callable
from PIL import Image
import aiohttp
import time
import threading

from config import get_config, BotConfig

class ComfyUIAPIError(Exception):
    """Custom exception for ComfyUI API errors."""
    pass

class ProgressInfo:
    """Class to hold simplified progress information for users."""
    def __init__(self):
        self.status = "initializing"  # initializing, queued, running, completed, failed
        self.queue_position = 0
        self.start_time = time.time()
        self.percentage = 0.0
        self.estimated_time_remaining = None
        self.phase = "Preparing"  # User-friendly phase description
        
        # Internal tracking (not shown to users)
        self._total_nodes = 0
        self._completed_nodes = 0
        self._current_step = 0
        self._total_steps = 0
        self._last_update_time = time.time()
        self._progress_history = []  # For better time estimation
        self._current_node_id = None
        self._execution_started = False
        
    def update_queue_status(self, position: int):
        """Update queue position."""
        self.status = "queued"
        self.queue_position = position
        self.phase = f"In queue (#{position})"
        self.percentage = 0.0
        
    def update_execution_start(self, total_nodes: int):
        """Update when execution starts."""
        self.status = "running"
        self.queue_position = 0
        self._total_nodes = total_nodes
        self._execution_started = True
        self.start_time = time.time()
        self._last_update_time = time.time()
        self.phase = "Starting generation"
        self.percentage = 5.0  # Show some initial progress
        
    def update_node_execution(self, node_id: str):
        """Update when a new node starts executing."""
        if not self._execution_started:
            return
            
        self._current_node_id = node_id
        if node_id and node_id != "None":
            self._completed_nodes += 1
            current_time = time.time()
            
            if self._total_nodes > 0:
                # Calculate base percentage (reserve last 10% for finalization)
                base_percentage = (self._completed_nodes / self._total_nodes) * 90
                self.percentage = min(90, max(5, base_percentage))
                
                # Update user-friendly phase based on progress
                progress_ratio = self._completed_nodes / self._total_nodes
                if progress_ratio < 0.1:
                    self.phase = "Initializing"
                elif progress_ratio < 0.3:
                    self.phase = "Processing prompt"
                elif progress_ratio < 0.7:
                    self.phase = "Generating image"
                elif progress_ratio < 0.9:
                    self.phase = "Refining details"
                else:
                    self.phase = "Finalizing"
            
            # Track progress for time estimation
            self._progress_history.append((current_time, self.percentage))
            # Keep only last 10 data points
            if len(self._progress_history) > 10:
                self._progress_history.pop(0)
                
            self._last_update_time = current_time
            
    def update_step_progress(self, current: int, total: int):
        """Update K-Sampler step progress."""
        if not self._execution_started:
            return
            
        self._current_step = current
        self._total_steps = total
        
        if self._total_steps > 0 and self.status == "running":
            # Add step-level granularity to the percentage
            if self._total_nodes > 0:
                # Calculate step progress within current node
                step_progress = (self._current_step / self._total_steps) * (90 / self._total_nodes)
                base_progress = (self._completed_nodes / self._total_nodes) * 90
                self.percentage = min(90, max(5, base_progress + step_progress))
            
            # Update phase for sampling
            if self._current_step > 0:
                self.phase = f"Sampling ({current}/{total})"
            
    def estimate_time_remaining(self):
        """Estimate time remaining based on progress history."""
        if len(self._progress_history) < 2 or self.percentage <= 5:
            # Not enough data for estimation
            self.estimated_time_remaining = None
            return None
            
        # Use linear regression on recent progress
        recent_history = self._progress_history[-5:]  # Last 5 data points
        if len(recent_history) < 2:
            return None
            
        # Calculate average progress rate
        time_diff = recent_history[-1][0] - recent_history[0][0]
        progress_diff = recent_history[-1][1] - recent_history[0][1]
        
        if time_diff <= 0 or progress_diff <= 0:
            return None
            
        progress_rate = progress_diff / time_diff  # percentage per second
        remaining_progress = 100 - self.percentage
        
        if progress_rate > 0:
            self.estimated_time_remaining = remaining_progress / progress_rate
            # Cap at reasonable maximum (10 minutes)
            self.estimated_time_remaining = min(self.estimated_time_remaining, 600)
        else:
            self.estimated_time_remaining = None
            
        return self.estimated_time_remaining
        
    def mark_completed(self):
        """Mark the process as completed."""
        self.status = "completed"
        self.percentage = 100.0
        self.phase = "Complete"
        self.estimated_time_remaining = 0
        
    def format_time(self, seconds: float) -> str:
        """Format time in a human-readable way."""
        if seconds is None or seconds <= 0:
            return "Unknown"
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            return f"{int(seconds // 60)}m {int(seconds % 60)}s"
        else:
            return f"{int(seconds // 3600)}h {int((seconds % 3600) // 60)}m"
            
    def get_progress_bar(self, length: int = 20) -> str:
        """Generate a visual progress bar."""
        filled_length = int(length * self.percentage // 100)
        return "█" * filled_length + "░" * (length - filled_length)
        
    def get_user_friendly_status(self) -> tuple[str, str, int]:
        """Get user-friendly status information.
        
        Returns:
            tuple: (title, description, color_value)
        """
        # Always calculate elapsed time for visual feedback
        elapsed = time.time() - self.start_time
        elapsed_str = self.format_time(elapsed)
        
        if self.status == "queued":
            title = "⏳ In Queue"
            description = f"📍 Position #{self.queue_position} in queue\n⏱️ Elapsed: {elapsed_str}\n🔄 Waiting to start..."
            color = 0xFFA500  # Orange
            
        elif self.status == "running":
            title = "🎨 Generating"
            progress_bar = self.get_progress_bar()
            description = f"📊 {self.percentage:.0f}% `{progress_bar}`\n"
            description += f"🔄 {self.phase}\n"
            description += f"⏱️ Elapsed: {elapsed_str}"
            
            if self.estimated_time_remaining and self.estimated_time_remaining > 0:
                description += f" | ETA: {self.format_time(self.estimated_time_remaining)}"
                
            color = 0x3498DB  # Blue
            
        elif self.status == "completed":
            title = "✅ Complete"
            progress_bar = self.get_progress_bar()
            description = f"📊 100% `{progress_bar}`\n⏱️ Total time: {elapsed_str}"
            color = 0x2ECC71  # Green
            
        else:  # initializing or other
            title = "🔄 Starting"
            description = f"⚙️ {self.phase}...\n⏱️ Elapsed: {elapsed_str}"
            color = 0x3498DB  # Blue
            
        return title, description, color

class ImageGenerator:
    """Handles image generation using ComfyUI API."""
    
    def __init__(self):
        self.config: BotConfig = get_config()
        self.logger = logging.getLogger(__name__)
        self.base_url = self.config.comfyui.url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
        self._session_lock = asyncio.Lock()
        
    async def __aenter__(self):
        """Async context manager entry."""
        async with self._session_lock:
            if self.session is None or self.session.closed:
                self.session = aiohttp.ClientSession(
                    timeout=aiohttp.ClientTimeout(total=self.config.comfyui.timeout),
                    connector=aiohttp.TCPConnector(limit=10, limit_per_host=5)
                )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        async with self._session_lock:
            if self.session and not self.session.closed:
                await self.session.close()
                self.session = None
    
    async def test_connection(self) -> bool:
        """Test connection to ComfyUI server."""
        try:
            if not self.session:
                raise RuntimeError("Session not initialized. Use async context manager.")
            
            async with self.session.get(f"{self.base_url}/system_stats") as response:
                if response.status == 200:
                    self.logger.info("ComfyUI connection successful")
                    return True
                else:
                    self.logger.error(f"ComfyUI connection failed: {response.status}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Failed to connect to ComfyUI: {e}")
            return False
    
    def _load_workflow(self, workflow_name: str) -> Dict[str, Any]:
        """Load workflow JSON from file."""
        try:
            workflow_config = self.config.workflows.get(workflow_name)
            if not workflow_config:
                # Fallback to default workflow
                workflow_file = f"{workflow_name}.json"
            else:
                workflow_file = workflow_config.file
            
            workflow_path = Path("workflows") / workflow_file
            
            if not workflow_path.exists():
                raise FileNotFoundError(f"Workflow file not found: {workflow_path}")
            
            with open(workflow_path, 'r', encoding='utf-8') as f:
                workflow = json.load(f)
            
            self.logger.debug(f"Loaded workflow: {workflow_name}")
            return workflow
            
        except Exception as e:
            self.logger.error(f"Failed to load workflow {workflow_name}: {e}")
            raise ComfyUIAPIError(f"Failed to load workflow: {e}")
    
    def _update_workflow_parameters(
        self,
        workflow: Dict[str, Any],
        prompt: str,
        negative_prompt: str = "",
        width: int = 1024,
        height: int = 1024,
        steps: int = 50,
        cfg: float = 5.0,
        seed: Optional[int] = None,
        batch_size: int = 1
    ) -> Dict[str, Any]:
        """Update workflow parameters with user inputs."""
        try:
            # Create a copy to avoid modifying the original
            updated_workflow = json.loads(json.dumps(workflow))
            
            # Generate random seed if not provided
            if seed is None:
                seed = random.randint(0, 2**32 - 1)
            
            # Find node types in the workflow
            node_types = {node_id: node_data.get('class_type') for node_id, node_data in updated_workflow.items()}
            
            # Update KSampler node
            ksampler_nodes = [node_id for node_id, class_type in node_types.items() if class_type == 'KSampler']
            if ksampler_nodes:
                ksampler_id = ksampler_nodes[0]
                ksampler_node = updated_workflow[ksampler_id]
                
                # Update sampling parameters
                ksampler_node['inputs']['seed'] = seed
                ksampler_node['inputs']['steps'] = steps
                ksampler_node['inputs']['cfg'] = cfg
                
                # Update positive prompt
                positive_input = ksampler_node['inputs'].get('positive')
                if positive_input and isinstance(positive_input, list) and len(positive_input) >= 1:
                    positive_node_id = positive_input[0]
                    if positive_node_id in updated_workflow:
                        updated_workflow[positive_node_id]['inputs']['text'] = prompt
                
                # Update negative prompt
                negative_input = ksampler_node['inputs'].get('negative')
                if negative_input and isinstance(negative_input, list) and len(negative_input) >= 1:
                    negative_node_id = negative_input[0]
                    if negative_node_id in updated_workflow:
                        updated_workflow[negative_node_id]['inputs']['text'] = negative_prompt
            
            # Update EmptySD3LatentImage or EmptyLatentImage node for dimensions
            latent_nodes = [
                node_id for node_id, class_type in node_types.items() 
                if class_type in ['EmptySD3LatentImage', 'EmptyLatentImage']
            ]
            if latent_nodes:
                latent_id = latent_nodes[0]
                latent_node = updated_workflow[latent_id]
                latent_node['inputs']['width'] = width
                latent_node['inputs']['height'] = height
                latent_node['inputs']['batch_size'] = batch_size
            
            self.logger.debug(f"Updated workflow parameters: prompt='{prompt[:50]}...', size={width}x{height}")
            return updated_workflow
            
        except Exception as e:
            self.logger.error(f"Failed to update workflow parameters: {e}")
            raise ComfyUIAPIError(f"Failed to update workflow parameters: {e}")
    
    async def _queue_prompt(self, workflow: Dict[str, Any]) -> str:
        """Queue a prompt for execution and return the prompt ID."""
        try:
            if not self.session:
                raise RuntimeError("Session not initialized")
            
            client_id = str(uuid.uuid4())
            prompt_data = {
                "prompt": workflow,
                "client_id": client_id
            }
            
            async with self.session.post(
                f"{self.base_url}/prompt",
                json=prompt_data,
                headers={"Content-Type": "application/json"}
            ) as response:
                
                if response.status != 200:
                    error_text = await response.text()
                    raise ComfyUIAPIError(f"Failed to queue prompt: {response.status} - {error_text}")
                
                result = await response.json()
                
                if 'error' in result:
                    raise ComfyUIAPIError(f"ComfyUI error: {result['error']}")
                
                prompt_id = result.get('prompt_id')
                if not prompt_id:
                    raise ComfyUIAPIError("No prompt_id returned from ComfyUI")
                
                self.logger.info(f"Queued prompt with ID: {prompt_id}")
                return prompt_id
                
        except Exception as e:
            self.logger.error(f"Failed to queue prompt: {e}")
            raise ComfyUIAPIError(f"Failed to queue prompt: {e}")
    
    async def _wait_for_completion_with_websocket(
        self, 
        prompt_id: str, 
        workflow: Dict[str, Any],
        progress_callback: Optional[Callable[[ProgressInfo], None]] = None
    ) -> Dict[str, Any]:
        """Wait for prompt completion using WebSocket for real-time progress."""
        try:
            progress = ProgressInfo()
            
            if progress_callback:
                await progress_callback(progress)
            
            # Create WebSocket connection URL without client_id initially
            ws_url = f"ws://{self.base_url.replace('http://', '').replace('https://', '')}/ws"
            
            self.logger.info(f"Connecting to WebSocket: {ws_url}")
            
            # Use aiohttp WebSocket client with timeout
            timeout = aiohttp.ClientTimeout(total=300)  # 5 minute timeout
            
            async with self.session.ws_connect(ws_url, timeout=timeout) as ws:
                self.logger.info(f"WebSocket connected for prompt {prompt_id}")
                
                # Track if we've started execution
                execution_started = False
                last_message_time = time.time()
                last_progress_update = time.time()
                
                # Add periodic progress updates
                async def send_periodic_update():
                    nonlocal last_progress_update
                    current_time = time.time()
                    if current_time - last_progress_update > 2.0:  # Update every 2 seconds
                        if progress_callback:
                            await progress_callback(progress)
                        last_progress_update = current_time
                
                while True:
                    try:
                        # Wait for WebSocket message with timeout
                        msg = await asyncio.wait_for(ws.receive(), timeout=3.0)
                        
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            last_message_time = time.time()
                            try:
                                data = json.loads(msg.data)
                                message_type = data.get('type')
                                message_data = data.get('data', {})
                                
                                self.logger.debug(f"WebSocket message: {message_type} - {message_data}")
                                
                                if message_type == 'status':
                                    # Queue status update
                                    status_data = message_data.get('status', {})
                                    exec_info = status_data.get('exec_info', {})
                                    queue_remaining = exec_info.get('queue_remaining', 0)
                                    
                                    if queue_remaining > 0 and not execution_started:
                                        progress.update_queue_status(queue_remaining)
                                        if progress_callback:
                                            await progress_callback(progress)
                                
                                elif message_type == 'execution_start':
                                    # Execution started
                                    if message_data.get('prompt_id') == prompt_id:
                                        execution_started = True
                                        progress.update_execution_start(len(workflow))
                                        if progress_callback:
                                            await progress_callback(progress)
                                        self.logger.info(f"Execution started for prompt {prompt_id}")
                                
                                elif message_type == 'execution_cached':
                                    # Some nodes were cached
                                    if message_data.get('prompt_id') == prompt_id:
                                        cached_nodes = message_data.get('nodes', [])
                                        for node in cached_nodes:
                                            progress.update_node_execution(node)
                                        if progress_callback:
                                            await progress_callback(progress)
                                
                                elif message_type == 'executing':
                                    # Node execution update
                                    if message_data.get('prompt_id') == prompt_id:
                                        current_node = message_data.get('node')
                                        
                                        if current_node is None:
                                            # Execution completed
                                            progress.mark_completed()
                                            if progress_callback:
                                                await progress_callback(progress)
                                            self.logger.info(f"Execution completed for prompt {prompt_id}")
                                            break
                                        else:
                                            # Node started executing
                                            progress.update_node_execution(current_node)
                                            progress.estimate_time_remaining()
                                            if progress_callback:
                                                await progress_callback(progress)
                                
                                elif message_type == 'progress':
                                    # K-Sampler progress
                                    current_step = message_data.get('value', 0)
                                    max_steps = message_data.get('max', 1)
                                    progress.update_step_progress(current_step, max_steps)
                                    progress.estimate_time_remaining()
                                    if progress_callback:
                                        await progress_callback(progress)
                                
                                elif message_type == 'executed':
                                    # Node execution completed
                                    if message_data.get('prompt_id') == prompt_id:
                                        node_id = message_data.get('node')
                                        self.logger.debug(f"Node {node_id} executed for prompt {prompt_id}")
                            
                            except json.JSONDecodeError as e:
                                self.logger.warning(f"Failed to parse WebSocket message: {e}")
                                continue
                        
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            self.logger.error(f"WebSocket error: {ws.exception()}")
                            break
                        
                        elif msg.type == aiohttp.WSMsgType.CLOSE:
                            self.logger.info("WebSocket connection closed")
                            break
                    
                    except asyncio.TimeoutError:
                        # No message received in timeout period
                        current_time = time.time()
                        
                        # Send periodic update
                        await send_periodic_update()
                        
                        # Check if we've been waiting too long without messages
                        if current_time - last_message_time > 30.0:
                            self.logger.warning(f"No WebSocket messages for 30 seconds, checking completion...")
                            
                            # Check if completed via API
                            async with self.session.get(f"{self.base_url}/history/{prompt_id}") as response:
                                if response.status == 200:
                                    history = await response.json()
                                    if prompt_id in history:
                                        progress.mark_completed()
                                        if progress_callback:
                                            await progress_callback(progress)
                                        self.logger.info(f"Prompt {prompt_id} completed (detected via API)")
                                        return history[prompt_id]
                            
                            # Check queue status
                            async with self.session.get(f"{self.base_url}/queue") as response:
                                if response.status == 200:
                                    queue_data = await response.json()
                                    queue_running = queue_data.get('queue_running', [])
                                    queue_pending = queue_data.get('queue_pending', [])
                                    
                                    is_running = any(item[1] == prompt_id for item in queue_running)
                                    is_pending = any(item[1] == prompt_id for item in queue_pending)
                                    
                                    if not is_running and not is_pending:
                                        self.logger.warning(f"Prompt {prompt_id} no longer in queue, falling back to polling")
                                        break
                                    
                                    if is_pending:
                                        # Update queue position
                                        queue_position = 1
                                        for i, item in enumerate(queue_pending):
                                            if item[1] == prompt_id:
                                                queue_position = i + 1
                                                break
                                        progress.update_queue_status(queue_position)
                                        if progress_callback:
                                            await progress_callback(progress)
                                    elif is_running and not execution_started:
                                        # Execution might have started but we missed the message
                                        execution_started = True
                                        progress.update_execution_start(len(workflow))
                                        if progress_callback:
                                            await progress_callback(progress)
                        continue
                
                # Get the final result from history
                async with self.session.get(f"{self.base_url}/history/{prompt_id}") as response:
                    if response.status == 200:
                        history = await response.json()
                        if prompt_id in history:
                            return history[prompt_id]
                
                raise ComfyUIAPIError(f"Failed to get completion status for prompt {prompt_id}")
                
        except Exception as e:
            self.logger.error(f"Error in WebSocket progress monitoring: {e}")
            # Fallback to polling method
            return await self._wait_for_completion_polling(prompt_id, progress_callback)
    
    async def _wait_for_completion_polling(self, prompt_id: str, progress_callback=None) -> Dict[str, Any]:
        """Fallback polling method for progress monitoring."""
        try:
            max_wait_time = self.config.comfyui.timeout
            check_interval = 2.0
            start_time = time.time()
            progress = ProgressInfo()
            execution_started = False
            last_progress_update = time.time()
            
            while time.time() - start_time < max_wait_time:
                current_time = time.time()
                
                # Send periodic progress updates
                if current_time - last_progress_update > 2.0:
                    if progress_callback:
                        await progress_callback(progress)
                    last_progress_update = current_time
                
                # Check history for completion
                async with self.session.get(f"{self.base_url}/history/{prompt_id}") as response:
                    if response.status == 200:
                        history = await response.json()
                        if prompt_id in history:
                            progress.mark_completed()
                            if progress_callback:
                                await progress_callback(progress)
                            self.logger.info(f"Prompt {prompt_id} completed successfully (polling)")
                            return history[prompt_id]
                
                # Check queue status
                async with self.session.get(f"{self.base_url}/queue") as response:
                    if response.status == 200:
                        queue_data = await response.json()
                        
                        # Check if prompt is still in queue
                        queue_running = queue_data.get('queue_running', [])
                        queue_pending = queue_data.get('queue_pending', [])
                        
                        is_running = any(item[1] == prompt_id for item in queue_running)
                        is_pending = any(item[1] == prompt_id for item in queue_pending)
                        
                        if not is_running and not is_pending:
                            # Prompt is no longer in queue, check history one more time
                            async with self.session.get(f"{self.base_url}/history/{prompt_id}") as hist_response:
                                if hist_response.status == 200:
                                    history = await hist_response.json()
                                    if prompt_id in history:
                                        progress.mark_completed()
                                        if progress_callback:
                                            await progress_callback(progress)
                                        return history[prompt_id]
                            
                            raise ComfyUIAPIError(f"Prompt {prompt_id} disappeared from queue without completion")
                        
                        if is_pending:
                            # Calculate actual queue position
                            queue_position = 1
                            for i, item in enumerate(queue_pending):
                                if item[1] == prompt_id:
                                    queue_position = i + 1
                                    break
                            progress.update_queue_status(queue_position)
                            self.logger.debug(f"Prompt {prompt_id} in queue position {queue_position}")
                        elif is_running and not execution_started:
                            # Execution started
                            execution_started = True
                            # Estimate total nodes (we don't have exact count in polling)
                            progress.update_execution_start(10)  # Rough estimate
                            progress.phase = "Generating (polling mode)"
                            self.logger.info(f"Prompt {prompt_id} execution started (polling)")
                        elif is_running:
                            # Update progress based on elapsed time (rough estimate)
                            elapsed = time.time() - start_time
                            # Assume average generation takes 60 seconds
                            estimated_progress = min(90, (elapsed / 60) * 100)
                            progress.percentage = estimated_progress
                            progress.estimate_time_remaining()
                
                await asyncio.sleep(check_interval)
            
            raise ComfyUIAPIError(f"Timeout waiting for prompt {prompt_id} to complete")
            
        except Exception as e:
            self.logger.error(f"Error waiting for completion: {e}")
            raise ComfyUIAPIError(f"Error waiting for completion: {e}")
    
    async def _download_images(self, history: Dict[str, Any]) -> List[bytes]:
        """Download generated images from ComfyUI."""
        try:
            images = []
            outputs = history.get('outputs', {})
            
            for node_id, node_output in outputs.items():
                if 'images' in node_output:
                    for image_info in node_output['images']:
                        filename = image_info['filename']
                        subfolder = image_info.get('subfolder', '')
                        image_type = image_info.get('type', 'output')
                        
                        # Download image
                        params = {
                            'filename': filename,
                            'subfolder': subfolder,
                            'type': image_type
                        }
                        
                        async with self.session.get(f"{self.base_url}/view", params=params) as response:
                            if response.status == 200:
                                image_data = await response.read()
                                images.append(image_data)
                                self.logger.debug(f"Downloaded image: {filename}")
                            else:
                                self.logger.error(f"Failed to download image {filename}: {response.status}")
            
            if not images:
                raise ComfyUIAPIError("No images found in generation output")
            
            self.logger.info(f"Downloaded {len(images)} images")
            return images
            
        except Exception as e:
            self.logger.error(f"Failed to download images: {e}")
            raise ComfyUIAPIError(f"Failed to download images: {e}")
    
    def _create_collage(self, images: List[bytes], max_width: int = 2048) -> bytes:
        """Create a collage from multiple images."""
        try:
            if len(images) == 1:
                return images[0]
            
            # Load images
            pil_images = []
            for img_data in images:
                img = Image.open(BytesIO(img_data))
                pil_images.append(img)
            
            # Calculate grid dimensions
            num_images = len(pil_images)
            if num_images <= 2:
                cols, rows = num_images, 1
            elif num_images <= 4:
                cols, rows = 2, 2
            else:
                cols = 3
                rows = (num_images + cols - 1) // cols
            
            # Get dimensions of first image for reference
            img_width, img_height = pil_images[0].size
            
            # Scale down if necessary
            scale_factor = min(1.0, max_width / (img_width * cols))
            if scale_factor < 1.0:
                new_width = int(img_width * scale_factor)
                new_height = int(img_height * scale_factor)
                pil_images = [img.resize((new_width, new_height), Image.Resampling.LANCZOS) for img in pil_images]
                img_width, img_height = new_width, new_height
            
            # Create collage
            collage_width = img_width * cols
            collage_height = img_height * rows
            collage = Image.new('RGB', (collage_width, collage_height), (0, 0, 0))
            
            for i, img in enumerate(pil_images):
                row = i // cols
                col = i % cols
                x = col * img_width
                y = row * img_height
                collage.paste(img, (x, y))
            
            # Convert to bytes
            output = BytesIO()
            collage.save(output, format='PNG', optimize=True)
            output.seek(0)
            
            self.logger.info(f"Created collage from {len(images)} images ({collage_width}x{collage_height})")
            return output.getvalue()
            
        except Exception as e:
            self.logger.error(f"Failed to create collage: {e}")
            # Return first image as fallback
            return images[0] if images else b''
    
    async def generate_image(
        self,
        prompt: str,
        negative_prompt: str = "",
        workflow_name: Optional[str] = None,
        width: int = 1024,
        height: int = 1024,
        steps: int = 50,
        cfg: float = 5.0,
        seed: Optional[int] = None,
        batch_size: int = 1,
        progress_callback=None
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Generate images using ComfyUI.
        
        Args:
            prompt: Positive prompt for generation
            negative_prompt: Negative prompt for generation
            workflow_name: Name of workflow to use (defaults to config default)
            width: Image width
            height: Image height
            steps: Number of sampling steps
            cfg: CFG scale
            seed: Random seed (auto-generated if None)
            batch_size: Number of images to generate
            progress_callback: Optional callback for progress updates
        
        Returns:
            Tuple of (image_data, generation_info)
        """
        try:
            # Validate inputs
            if not prompt.strip():
                raise ValueError("Prompt cannot be empty")
            
            if len(prompt) > self.config.security.max_prompt_length:
                raise ValueError(f"Prompt too long (max {self.config.security.max_prompt_length} characters)")
            
            if batch_size > self.config.generation.max_batch_size:
                raise ValueError(f"Batch size too large (max {self.config.generation.max_batch_size})")
            
            # Use default workflow if none specified
            if not workflow_name:
                workflow_name = self.config.generation.default_workflow
            
            self.logger.info(f"Starting image generation: '{prompt[:50]}...' ({batch_size} images)")
            
            # Load and update workflow
            workflow = self._load_workflow(workflow_name)
            updated_workflow = self._update_workflow_parameters(
                workflow, prompt, negative_prompt, width, height, steps, cfg, seed, batch_size
            )
            
            # Queue prompt
            prompt_id = await self._queue_prompt(updated_workflow)
            
            # Wait for completion
            history = await self._wait_for_completion_with_websocket(prompt_id, updated_workflow, progress_callback)
            
            # Download images
            images = await self._download_images(history)
            
            # Create collage if multiple images
            if len(images) > 1:
                final_image = self._create_collage(images)
            else:
                final_image = images[0]
            
            # Prepare generation info
            generation_info = {
                'prompt_id': prompt_id,
                'prompt': prompt,
                'negative_prompt': negative_prompt,
                'workflow': workflow_name,
                'width': width,
                'height': height,
                'steps': steps,
                'cfg': cfg,
                'seed': seed,
                'batch_size': batch_size,
                'num_images': len(images),
                'timestamp': time.time()
            }
            
            self.logger.info(f"Image generation completed successfully: {len(images)} images")
            return final_image, generation_info
            
        except Exception as e:
            self.logger.error(f"Image generation failed: {e}")
            raise ComfyUIAPIError(f"Image generation failed: {e}")
    
    async def get_available_workflows(self) -> List[Dict[str, str]]:
        """Get list of available workflows."""
        try:
            workflows = []
            
            # Get configured workflows
            for name, config in self.config.workflows.items():
                if config.enabled:
                    workflows.append({
                        'name': name,
                        'display_name': config.name,
                        'description': config.description
                    })
            
            # If no configured workflows, scan workflow directory
            if not workflows:
                workflows_dir = Path("workflows")
                if workflows_dir.exists():
                    for workflow_file in workflows_dir.glob("*.json"):
                        name = workflow_file.stem
                        workflows.append({
                            'name': name,
                            'display_name': name.replace('_', ' ').title(),
                            'description': f"Workflow from {workflow_file.name}"
                        })
            
            return workflows
            
        except Exception as e:
            self.logger.error(f"Failed to get available workflows: {e}")
            return []
    
    async def generate_upscale(
        self,
        input_image_data: bytes,
        prompt: str = "",
        negative_prompt: str = "",
        upscale_factor: float = 2.0,
        denoise: float = 0.35,
        steps: int = 20,
        cfg: float = 7.0,
        seed: Optional[int] = None,
        progress_callback=None
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Upscale an image using ComfyUI upscale workflow.
        
        Args:
            input_image_data: Image data as bytes
            prompt: Positive prompt for upscaling
            negative_prompt: Negative prompt for upscaling
            upscale_factor: Upscaling factor (default: 2.0)
            denoise: Denoising strength (default: 0.35)
            steps: Number of sampling steps (default: 20)
            cfg: CFG scale (default: 7.0)
            seed: Random seed (auto-generated if None)
            progress_callback: Optional callback for progress updates
        
        Returns:
            Tuple of (upscaled_image_data, upscale_info)
        """
        try:
            # Validate inputs
            if not input_image_data:
                raise ValueError("Input image data cannot be empty")
            
            # Upload image to ComfyUI
            upload_filename = f"upscale_input_{int(time.time())}.png"
            uploaded_filename = await self.upload_image(input_image_data, upload_filename)
            
            # Use upscale workflow
            workflow_name = "upscale_config-1"
            
            self.logger.info(f"Starting image upscaling: {uploaded_filename} (factor: {upscale_factor}x)")
            
            # Load and update workflow
            workflow = self._load_workflow(workflow_name)
            updated_workflow = self._update_upscale_workflow_parameters(
                workflow, uploaded_filename, prompt, negative_prompt, upscale_factor, denoise, steps, cfg, seed
            )
            
            # Queue prompt
            prompt_id = await self._queue_prompt(updated_workflow)
            
            # Wait for completion
            history = await self._wait_for_completion_with_websocket(prompt_id, updated_workflow, progress_callback)
            
            # Download upscaled image
            images = await self._download_images(history)
            upscaled_image_data = images[0] if images else b''
            
            # Prepare upscale info
            upscale_info = {
                'prompt_id': prompt_id,
                'input_image': uploaded_filename,
                'prompt': prompt,
                'negative_prompt': negative_prompt,
                'upscale_factor': upscale_factor,
                'denoise': denoise,
                'steps': steps,
                'cfg': cfg,
                'seed': seed,
                'workflow': workflow_name,
                'timestamp': time.time(),
                'type': 'upscale'
            }
            
            self.logger.info(f"Image upscaling completed successfully")
            return upscaled_image_data, upscale_info
            
        except Exception as e:
            self.logger.error(f"Image upscaling failed: {e}")
            raise ComfyUIAPIError(f"Image upscaling failed: {e}")
    
    def _update_upscale_workflow_parameters(
        self,
        workflow: Dict[str, Any],
        input_image_path: str,
        prompt: str = "",
        negative_prompt: str = "",
        upscale_factor: float = 2.0,
        denoise: float = 0.35,
        steps: int = 20,
        cfg: float = 7.0,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update upscale workflow parameters with user inputs."""
        try:
            # Create a copy to avoid modifying the original
            updated_workflow = json.loads(json.dumps(workflow))
            
            # Generate random seed if not provided
            if seed is None:
                import random
                seed = random.randint(0, 2**32 - 1)
            
            # Update workflow parameters based on the upscale workflow structure
            for node_id, node_data in updated_workflow.items():
                class_type = node_data.get('class_type')
                
                if class_type == 'LoadImage':
                    # Update input image
                    node_data['inputs']['image'] = input_image_path
                
                elif class_type == 'CLIPTextEncode':
                    title = node_data.get('_meta', {}).get('title', '')
                    if 'positive' in title.lower():
                        node_data['inputs']['text'] = prompt
                    elif 'negative' in title.lower():
                        node_data['inputs']['text'] = negative_prompt
                
                elif class_type == 'UltimateSDUpscale':
                    # Update upscaling parameters
                    node_data['inputs']['upscale_by'] = upscale_factor
                    node_data['inputs']['seed'] = seed
                    node_data['inputs']['steps'] = steps
                    node_data['inputs']['cfg'] = cfg
                    node_data['inputs']['denoise'] = denoise
                
                elif class_type == 'LoraTextExtractor-b1f83aa2':
                    # Update LoRA text extractor with prompt
                    node_data['inputs']['text'] = prompt
            
            self.logger.debug(f"Updated upscale workflow parameters: input={input_image_path}, factor={upscale_factor}x")
            return updated_workflow
            
        except Exception as e:
            self.logger.error(f"Failed to update upscale workflow parameters: {e}")
            raise ComfyUIAPIError(f"Failed to update upscale workflow parameters: {e}")
    
    async def upload_image(self, image_data: bytes, filename: str) -> str:
        """Upload image data to ComfyUI input directory."""
        try:
            if not self.session:
                raise RuntimeError("Session not initialized")
            
            # Create form data for file upload
            data = aiohttp.FormData()
            data.add_field('image', 
                          image_data, 
                          filename=filename, 
                          content_type='image/png')
            
            # Upload to ComfyUI
            async with self.session.post(f"{self.base_url}/upload/image", data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    uploaded_filename = result.get('name', filename)
                    self.logger.info(f"Successfully uploaded image: {uploaded_filename}")
                    return uploaded_filename
                else:
                    error_text = await response.text()
                    raise ComfyUIAPIError(f"Failed to upload image: {response.status} - {error_text}")
                    
        except Exception as e:
            self.logger.error(f"Failed to upload image: {e}")
            raise ComfyUIAPIError(f"Failed to upload image: {e}")

# Utility functions for file management
def save_output_image(image_data: bytes, filename: str) -> Path:
    """Save generated image to output directory."""
    try:
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)
        
        output_path = output_dir / filename
        with open(output_path, 'wb') as f:
            f.write(image_data)
        
        return output_path
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to save output image: {e}")
        raise

def cleanup_old_outputs(max_files: int = 50) -> None:
    """Clean up old output files, keeping only the most recent ones."""
    try:
        output_dir = Path("outputs")
        if not output_dir.exists():
            return
        
        # Get all files sorted by modification time (newest first)
        files = sorted(
            output_dir.glob("*"),
            key=lambda p: p.stat().st_mtime,
            reverse=True
        )
        
        # Remove excess files
        for file_path in files[max_files:]:
            if file_path.is_file():
                file_path.unlink()
                logging.getLogger(__name__).debug(f"Removed old output file: {file_path}")
        
        if len(files) > max_files:
            logging.getLogger(__name__).info(f"Cleaned up {len(files) - max_files} old output files")
            
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to cleanup old outputs: {e}")

def get_unique_filename(base_name: str, extension: str = ".png") -> str:
    """Generate a unique filename for output."""
    timestamp = int(time.time())
    random_suffix = random.randint(1000, 9999)
    return f"{base_name}_{timestamp}_{random_suffix}{extension}" 