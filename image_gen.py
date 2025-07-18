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
        self._workflow_nodes = set()  # All nodes in the workflow
        self._executed_nodes = set()  # Nodes that have been executed
        self._cached_nodes = set()   # Nodes that were cached (skipped)
        self._workflow_data = None  # Store the full workflow for video detection
        
        # Step-based progress tracking
        self._first_step_reached = False
        self._step_progress_history = []  # Track multiple step sequences for upscaling
        self._current_step_sequence = 0  # For multi-iteration workflows like upscaling
        
    def set_workflow_nodes(self, workflow: Dict[str, Any]):
        """Initialize with all nodes from workflow for accurate progress tracking."""
        self._workflow_nodes = set(workflow.keys())
        self._total_nodes = len(self._workflow_nodes)
        self._workflow_data = workflow  # Store the full workflow for video detection
        
    def update_queue_status(self, position: int):
        """Update queue position - only when genuinely queued."""
        self.status = "queued"
        self.queue_position = position
        self.phase = f"In queue (#{position})"
        self.percentage = 0.0
        
    def update_execution_start(self):
        """Update when execution starts - switches from queued to running."""
        if self.status != "running":  # Only log the transition once
            self.status = "running"
            self.queue_position = 0  # Clear queue position when running
            self._execution_started = True
            self.start_time = time.time()  # Reset start time for accurate elapsed time
            self._last_update_time = time.time()
            if not self._first_step_reached:
                self.phase = "Loading"
                self.percentage = 0.0  # Start at 0% until first step
            
    def update_cached_nodes(self, cached_nodes: list):
        """Update when nodes are cached (execution skipped)."""
        if not self._execution_started:
            return
            
        for node_id in cached_nodes:
            if node_id in self._workflow_nodes:
                self._cached_nodes.add(node_id)
        
        # Don't update progress from nodes anymore - only from steps
        
    def update_node_execution(self, node_id: str):
        """Update when a new node starts executing."""
        if not self._execution_started:
            return
            
        self._current_node_id = node_id
        
        # Add to executed nodes if it's a valid node
        if node_id and node_id != "None" and node_id in self._workflow_nodes:
            self._executed_nodes.add(node_id)
            
        # Don't update progress from nodes anymore - only from steps
        
    def update_step_progress(self, current: int, total: int):
        """Update K-Sampler step progress - this is now the PRIMARY progress method."""
        if not self._execution_started:
            return
            
        self._current_step = current
        self._total_steps = total
        
        # Mark that we've reached the first step
        if current > 0 and not self._first_step_reached:
            self._first_step_reached = True
            self.phase = f"Sampling ({current}/{total})"
        
        if self._total_steps > 0 and current > 0:
            # Check if this is a new sequence (for multi-iteration workflows like upscaling)
            if current == 1 and self._current_step > 1:
                self._current_step_sequence += 1
                
            # Calculate step-based progress
            if self._first_step_reached:
                # For single sequence (normal generation/video)
                if self._current_step_sequence == 0:
                    step_percentage = (current / total) * 100
                    self.percentage = min(95, step_percentage)  # Reserve 5% for finalization
                else:
                    # For multi-sequence (upscaling) - each sequence contributes to total
                    # Estimate total sequences based on typical upscaling (3-4 iterations)
                    estimated_sequences = 4
                    sequence_weight = 100 / estimated_sequences
                    
                    # Current sequence progress
                    current_seq_progress = (current / total) * sequence_weight
                    # Previous sequences progress
                    previous_seq_progress = self._current_step_sequence * sequence_weight
                    
                    self.percentage = min(95, previous_seq_progress + current_seq_progress)
                
                # Update phase for sampling
                if self._current_step_sequence > 0:
                    self.phase = f"Upscaling - Pass {self._current_step_sequence + 1} ({current}/{total})"
                else:
                    self.phase = f"Sampling ({current}/{total})"
                    
                # Track progress for time estimation
                current_time = time.time()
                self._progress_history.append((current_time, self.percentage))
                # Keep only last 10 data points
                if len(self._progress_history) > 10:
                    self._progress_history.pop(0)
                    
                self._last_update_time = current_time
                
    def estimate_time_remaining(self):
        """Estimate time remaining based on progress history."""
        if len(self._progress_history) < 2 or self.percentage <= 0:
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
            title = "⏳ Queued"
            description = f"📍 Position #{self.queue_position} in queue\n⏱️ Waiting time: {elapsed_str}\n🔄 Waiting for ComfyUI to start processing..."
            color = 0xFFA500  # Orange
            
        elif self.status == "running":
            title = "🎨 Generating"
            progress_bar = self.get_progress_bar()
            
            # Always calculate time estimation for running status
            self.estimate_time_remaining()
            
            description = f"📊 {self.percentage:.1f}% `{progress_bar}`\n"
            description += f"🔄 {self.phase}\n"
            description += f"⏱️ Elapsed: {elapsed_str}"
            
            if self.estimated_time_remaining and self.estimated_time_remaining > 0:
                description += f" | ETA: {self.format_time(self.estimated_time_remaining)}"
                
            # Show step progress if available
            if self._current_step > 0 and self._total_steps > 0:
                description += f"\n🎯 Step: {self._current_step}/{self._total_steps}"
                
                # Show sequence info for multi-iteration workflows
                if self._current_step_sequence > 0:
                    description += f" (Pass {self._current_step_sequence + 1})"
                
            color = 0x3498DB  # Blue
            
        elif self.status == "completed":
            title = "✅ Complete"
            progress_bar = self.get_progress_bar()
            description = f"📊 100% `{progress_bar}`\n⏱️ Total time: {elapsed_str}"
            color = 0x2ECC71  # Green
            
        else:  # initializing or other
            title = "🔄 Preparing"
            description = f"⚙️ {self.phase}...\n⏱️ Elapsed: {elapsed_str}\n📝 Setting up workflow..."
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
        self._queue_lock = asyncio.Lock()  # Add queue lock for concurrent request management
        
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
        batch_size: int = 1,
        lora_name: Optional[str] = None,
        lora_strength: float = 1.0
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
            
            # Update KSampler node (for HiDream workflows)
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
            
            # Update RandomNoise node (for Flux workflows)
            random_noise_nodes = [node_id for node_id, class_type in node_types.items() if class_type == 'RandomNoise']
            if random_noise_nodes:
                noise_id = random_noise_nodes[0]
                updated_workflow[noise_id]['inputs']['noise_seed'] = seed
            
            # Update BasicScheduler node (for Flux workflows)
            basic_scheduler_nodes = [node_id for node_id, class_type in node_types.items() if class_type == 'BasicScheduler']
            if basic_scheduler_nodes:
                scheduler_id = basic_scheduler_nodes[0]
                updated_workflow[scheduler_id]['inputs']['steps'] = steps
            
            # Update CLIPTextEncode nodes for prompts
            clip_encode_nodes = [node_id for node_id, class_type in node_types.items() if class_type == 'CLIPTextEncode']
            for node_id in clip_encode_nodes:
                node_data = updated_workflow[node_id]
                title = node_data.get('_meta', {}).get('title', '').lower()
                
                if 'positive' in title:
                    node_data['inputs']['text'] = prompt
                elif 'negative' in title:
                    node_data['inputs']['text'] = negative_prompt
            
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
            
            # Update LoraLoaderModelOnly node
            lora_loader_nodes = [node_id for node_id, class_type in node_types.items() if class_type == 'LoraLoaderModelOnly']
            if lora_loader_nodes:
                lora_id = lora_loader_nodes[0]
                lora_node = updated_workflow[lora_id]
                
                if lora_name and lora_name != "none":
                    # Use specified LoRA
                    lora_node['inputs']['lora_name'] = lora_name
                    lora_node['inputs']['strength_model'] = lora_strength
                    self.logger.debug(f"Using LoRA: {lora_name} with strength {lora_strength}")
                else:
                    # No LoRA - we could either remove the node or use a default
                    # For simplicity, we'll use a very low strength to effectively disable it
                    lora_node['inputs']['strength_model'] = 0.0
                    self.logger.debug("No LoRA selected - setting strength to 0.0")
            
            self.logger.debug(f"Updated workflow parameters: prompt='{prompt[:50]}...', size={width}x{height}, LoRA={lora_name}")
            return updated_workflow
            
        except Exception as e:
            self.logger.error(f"Failed to update workflow parameters: {e}")
            raise ComfyUIAPIError(f"Failed to update workflow parameters: {e}")
    
    async def _queue_prompt(self, workflow: Dict[str, Any]) -> Tuple[str, str]:
        """Queue a prompt for generation in ComfyUI and return prompt_id and client_id."""
        try:
            # Use queue lock to prevent concurrent queuing conflicts
            async with self._queue_lock:
                # First, try to connect to WebSocket to get the proper client_id from ComfyUI
                client_id = None
                try:
                    import websockets
                    ws_url = f"ws://{self.base_url.replace('http://', '').replace('https://', '')}/ws"
                    self.logger.info(f"🔌 Connecting to WebSocket to get client_id: {ws_url}")
                    
                    # Use shorter timeout for client_id retrieval
                    async with asyncio.wait_for(websockets.connect(ws_url), timeout=5.0) as websocket:
                        # Wait for the first status message to get the client_id
                        message_count = 0
                        while message_count < 10:  # Limit attempts to avoid infinite loop
                            try:
                                message = await asyncio.wait_for(websocket.recv(), timeout=3.0)
                                message_count += 1
                                
                                if isinstance(message, str):
                                    data = json.loads(message)
                                    self.logger.debug(f"WebSocket message {message_count}: {data}")
                                    
                                    # Check for client_id in different possible locations
                                    if data.get('type') == 'status' and 'sid' in data:
                                        client_id = data['sid']
                                        self.logger.info(f"🔑 Received client_id from ComfyUI: {client_id}")
                                        break
                                    elif 'client_id' in data:
                                        client_id = data['client_id']
                                        self.logger.info(f"🔑 Found client_id in message: {client_id}")
                                        break
                                    elif data.get('type') == 'status':
                                        self.logger.debug(f"Status message without sid: {data}")
                                        
                            except asyncio.TimeoutError:
                                self.logger.debug(f"No message received in 3s (attempt {message_count})")
                                break
                            except json.JSONDecodeError as e:
                                self.logger.warning(f"JSON decode error in WebSocket message: {e}")
                                continue
                        
                        if not client_id:
                            self.logger.warning(f"⚠️ Could not extract client_id from {message_count} WebSocket messages")
                        
                except asyncio.TimeoutError:
                    self.logger.warning(f"⚠️ WebSocket connection timeout after 5s")
                except Exception as ws_error:
                    self.logger.warning(f"⚠️ WebSocket client_id fetch failed: {ws_error}")
                
                # Fallback to generating client_id if WebSocket fails
                if not client_id:
                    client_id = str(uuid.uuid4())
                    self.logger.warning(f"⚠️ Using generated client_id as fallback: {client_id}")
                
                self.logger.info(f"🔄 Queuing prompt with client_id: {client_id}")
                
                prompt_data = {
                    "prompt": workflow,
                    "client_id": client_id
                }
                
                # Debug: Log the request details
                self.logger.info(f"🌐 Making POST request to: {self.base_url}/prompt")
                self.logger.info(f"📦 Payload size: {len(json.dumps(prompt_data))} bytes")
                self.logger.info(f"🔑 Using client_id: {client_id}")
                
                # Add timeout to prevent hanging
                timeout = aiohttp.ClientTimeout(total=30)
                async with self.session.post(
                    f"{self.base_url}/prompt",
                    json=prompt_data,
                    timeout=timeout
                ) as response:
                    self.logger.info(f"📋 Queue response status: {response.status}")
                    self.logger.info(f"📋 Response headers: {dict(response.headers)}")
                    
                    # Get response text for debugging
                    response_text = await response.text()
                    self.logger.info(f"📋 Raw response: {response_text}")
                    
                    if response.status == 200:
                        try:
                            result = json.loads(response_text)
                            self.logger.info(f"📋 Parsed response: {result}")
                            
                            if 'prompt_id' in result:
                                prompt_id = result['prompt_id']
                                self.logger.info(f"✅ Successfully queued prompt with ID: {prompt_id}")
                                
                                # Verify the prompt actually got queued by checking ComfyUI queue
                                try:
                                    async with self.session.get(f"{self.base_url}/queue") as queue_response:
                                        if queue_response.status == 200:
                                            queue_data = await queue_response.json()
                                            
                                            # Check if our prompt is in the queue
                                            found_in_queue = False
                                            for item in queue_data.get('queue_pending', []) + queue_data.get('queue_running', []):
                                                if isinstance(item, list) and len(item) >= 2 and item[1] == prompt_id:
                                                    found_in_queue = True
                                                    break
                                            
                                            if found_in_queue:
                                                self.logger.info(f"✅ Verified prompt {prompt_id} is in ComfyUI queue")
                                            else:
                                                self.logger.warning(f"⚠️ Prompt {prompt_id} NOT found in ComfyUI queue!")
                                                self.logger.warning(f"⚠️ Queue state: {queue_data}")
                                        else:
                                            self.logger.warning(f"⚠️ Could not verify queue status: {queue_response.status}")
                                except Exception as verify_error:
                                    self.logger.warning(f"⚠️ Error verifying queue: {verify_error}")
                                
                                return prompt_id, client_id
                            else:
                                raise ComfyUIAPIError(f"No prompt_id in response: {result}")
                        except json.JSONDecodeError as json_error:
                            raise ComfyUIAPIError(f"Invalid JSON response: {response_text}, error: {json_error}")
                    else:
                        raise ComfyUIAPIError(f"Failed to queue prompt: {response.status} - {response_text}")
                        
        except asyncio.TimeoutError:
            raise ComfyUIAPIError("Timeout while queuing prompt - ComfyUI may be overloaded")
        except Exception as e:
            self.logger.error(f"Failed to queue prompt: {e}")
            raise ComfyUIAPIError(f"Failed to queue prompt: {e}")
    
    async def _wait_for_completion_with_websocket(
        self, 
        prompt_id: str, 
        client_id: str,
        workflow: Dict[str, Any],
        progress_callback: Optional[Callable[[ProgressInfo], None]] = None
    ) -> Dict[str, Any]:
        """Wait for prompt completion using enhanced HTTP polling (WebSocket as secondary)."""
        try:
            progress = ProgressInfo()
            progress.set_workflow_nodes(workflow)
            
            # Send initial progress
            if progress_callback:
                await progress_callback(progress)
            
            # Use enhanced HTTP polling as primary method (more reliable)
            self.logger.info(f"Using enhanced HTTP polling for prompt {prompt_id} with client_id {client_id}")
            return await self._wait_for_completion_polling_enhanced(prompt_id, client_id, progress_callback, progress)
                
        except Exception as e:
            self.logger.error(f"Error in progress monitoring: {e}")
            raise ComfyUIAPIError(f"Failed to monitor generation progress: {e}")
    
    async def _track_websocket_progress(self, ws_url: str, prompt_id: str, client_id: str, progress_data: dict):
        """Background task to track node-level progress via WebSocket."""
        try:
            import websockets
            
            # Use the client_id we got from ComfyUI for WebSocket connection
            full_ws_url = f"{ws_url}?clientId={client_id}"
            self.logger.info(f"📡 Connecting to WebSocket with ComfyUI client_id: {full_ws_url}")
            
            async with websockets.connect(full_ws_url) as websocket:
                self.logger.info(f"📡 WebSocket connected for node tracking prompt {prompt_id}")
                
                while True:
                    try:
                        message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                        
                        if isinstance(message, str):
                            data = json.loads(message)
                            message_type = data.get('type')
                            message_data = data.get('data', {})
                            
                            # Log ALL WebSocket messages for debugging
                            self.logger.info(f"📡 WebSocket message: type={message_type}, data={message_data}")
                            
                            # Handle progress messages (K-Sampler steps) - NO prompt_id filter needed for progress
                            if message_type == 'progress':
                                current_step = message_data.get('value', 0)
                                max_steps = message_data.get('max', 0)
                                progress_data['step_current'] = current_step
                                progress_data['step_total'] = max_steps
                                progress_data['last_websocket_update'] = time.time()
                                self.logger.info(f"📈 Step progress: {current_step}/{max_steps}")
                            
                            # Handle execution cached (nodes skipped due to caching)
                            elif message_type == 'execution_cached':
                                # Check if it's for our prompt
                                if message_data.get('prompt_id') == prompt_id:
                                    cached_nodes = message_data.get('nodes', [])
                                    progress_data['cached_nodes'] = cached_nodes
                                    progress_data['last_websocket_update'] = time.time()
                                    self.logger.info(f"💾 Cached nodes for {prompt_id}: {cached_nodes}")
                                else:
                                    self.logger.debug(f"💾 Ignoring cached nodes for different prompt: {message_data.get('prompt_id')}")
                            
                            # Handle node execution
                            elif message_type == 'executing':
                                # Check if it's for our prompt
                                if message_data.get('prompt_id') == prompt_id:
                                    node_id = message_data.get('node')
                                    if node_id is not None:
                                        progress_data['current_node'] = str(node_id)
                                        progress_data['last_websocket_update'] = time.time()
                                        self.logger.info(f"🔧 Node executing for {prompt_id}: {node_id}")
                                    else:
                                        # node_id is None means execution completed
                                        self.logger.info(f"✅ WebSocket detected completion for prompt {prompt_id}")
                                        break
                                else:
                                    self.logger.debug(f"🔧 Ignoring node execution for different prompt: {message_data.get('prompt_id')}")
                            
                            # Also track general status updates for fallback
                            elif message_type == 'status':
                                status_data = message_data.get('status', {})
                                if 'exec_info' in status_data:
                                    exec_info = status_data['exec_info']
                                    progress_data['queue_remaining'] = exec_info.get('queue_remaining', 0)
                                    progress_data['last_websocket_update'] = time.time()
                                    self.logger.info(f"📊 Status update: queue_remaining={exec_info.get('queue_remaining', 0)}")
                                
                    except asyncio.TimeoutError:
                        # No message received in timeout period - this is normal
                        continue
                    except json.JSONDecodeError as e:
                        self.logger.warning(f"WebSocket JSON decode error: {e}")
                        continue
                        
        except Exception as e:
            self.logger.info(f"WebSocket node tracking ended: {e}")
        finally:
            self.logger.info(f"📡 WebSocket node tracking task ended for prompt {prompt_id}")
    
    async def _wait_for_completion_polling_enhanced(self, prompt_id: str, client_id: str, progress_callback=None, progress: ProgressInfo = None) -> Dict[str, Any]:
        """Enhanced HTTP polling method with optional WebSocket node tracking."""
        try:
            # Dynamic timeout based on expected generation type
            base_timeout = self.config.comfyui.timeout
            # For video workflows, use longer timeout (15 minutes for long video generation)
            workflow_json = json.dumps(progress._workflow_data)
            if ("VideoLinearCFGGuidance" in workflow_json or 
                "I2VGenXLPipeline" in workflow_json or 
                "WanVaceToVideo" in workflow_json or
                "VHS_VideoCombine" in workflow_json or
                "AnimateDiff" in workflow_json):
                max_wait_time = 900  # 15 minutes for video generation
                self.logger.info(f"🎬 Video workflow detected - using extended timeout: {max_wait_time}s (15 minutes)")
            else:
                max_wait_time = base_timeout  # Default for images
                self.logger.info(f"🖼️ Image workflow detected - using standard timeout: {max_wait_time}s")
            
            # Always use 1-second polling for accurate progress tracking
            check_interval = 1.0
            start_time = time.time()
            last_update_time = time.time()
            execution_started = False
            last_status = None
            last_progress_sent = 0.0
            progress_update_count = 0
            
            # Try to establish WebSocket for node-level tracking (optional)
            websocket_task = None
            websocket_progress = {}
            
            try:
                import websockets
                ws_url = f"ws://{self.base_url.replace('http://', '').replace('https://', '')}/ws"
                self.logger.info(f"📡 Starting WebSocket tracking with client_id: {client_id}")
                websocket_task = asyncio.create_task(self._track_websocket_progress(ws_url, prompt_id, client_id, websocket_progress))
            except Exception as ws_error:
                self.logger.warning(f"WebSocket unavailable for node tracking: {ws_error}")
            
            self.logger.info(f"Starting enhanced polling for prompt {prompt_id} (timeout: {max_wait_time}s, interval: 1s)")
            
            while time.time() - start_time < max_wait_time:
                current_time = time.time()
                
                # Check history first for completion
                try:
                    async with self.session.get(f"{self.base_url}/history/{prompt_id}") as response:
                        if response.status == 200:
                            response_text = await response.text()
                            if response_text and response_text.strip():
                                history_data = await response.json()
                                if history_data and isinstance(history_data, dict) and prompt_id in history_data:
                                    prompt_data = history_data[prompt_id]
                                    if isinstance(prompt_data, dict) and 'outputs' in prompt_data:
                                        # Generation completed!
                                        progress.mark_completed()
                                        if progress_callback:
                                            await progress_callback(progress)
                                        
                                        # Clean up WebSocket task
                                        if websocket_task:
                                            websocket_task.cancel()
                                            
                                        self.logger.info(f"✅ Generation completed for prompt {prompt_id}")
                                        self.logger.info(f"📊 Total progress updates sent: {progress_update_count}")
                                        return prompt_data
                except Exception as e:
                    self.logger.debug(f"History check error: {e}")
                
                # Check queue status for accurate progress reporting
                try:
                    async with self.session.get(f"{self.base_url}/queue") as response:
                        if response.status == 200:
                            response_text = await response.text()
                            if response_text and response_text.strip():
                                queue_data = await response.json()
                                
                                if queue_data and isinstance(queue_data, dict):
                                    queue_running = queue_data.get('queue_running', [])
                                    queue_pending = queue_data.get('queue_pending', [])
                                    
                                    # Check if our prompt is actively running
                                    is_running = False
                                    for item in queue_running:
                                        try:
                                            if isinstance(item, list) and len(item) >= 2:
                                                if isinstance(item[1], dict) and item[1].get('prompt_id') == prompt_id:
                                                    is_running = True
                                                    break
                                        except (AttributeError, TypeError, KeyError):
                                            continue
                                    
                                    # Check if prompt is in pending queue
                                    queue_position = None
                                    for i, item in enumerate(queue_pending):
                                        try:
                                            if isinstance(item, list) and len(item) >= 2:
                                                if isinstance(item[1], dict) and item[1].get('prompt_id') == prompt_id:
                                                    queue_position = i + 1
                                                    break
                                        except (AttributeError, TypeError, KeyError):
                                            continue
                                    
                                    # Update progress based on ACTUAL queue state
                                    if queue_position is not None:
                                        # Prompt is genuinely queued
                                        if progress.status != "queued" or progress.queue_position != queue_position:
                                            progress.update_queue_status(queue_position)
                                            self.logger.info(f"Prompt {prompt_id} is in queue position #{queue_position}")
                                            last_status = f"queued #{queue_position}"
                                    elif is_running:
                                        # Prompt is actively running
                                        if not execution_started:
                                            execution_started = True
                                            progress.update_execution_start()
                                            self.logger.info(f"Prompt {prompt_id} execution started")
                                            last_status = "running"
                                        
                                        # Use WebSocket node data if available and recent
                                        websocket_data_age = current_time - websocket_progress.get('last_websocket_update', 0)
                                        if websocket_progress and websocket_data_age < 10.0:  # Use WebSocket data if less than 10 seconds old
                                            # Apply WebSocket node tracking data
                                            old_percentage = progress.percentage
                                            
                                            if 'current_node' in websocket_progress:
                                                progress.update_node_execution(websocket_progress['current_node'])
                                                
                                            if 'cached_nodes' in websocket_progress:
                                                progress.update_cached_nodes(websocket_progress['cached_nodes'])
                                                
                                            if 'step_current' in websocket_progress and 'step_total' in websocket_progress:
                                                progress.update_step_progress(
                                                    websocket_progress['step_current'], 
                                                    websocket_progress['step_total']
                                                )
                                                
                                            self.logger.info(f"📊 Applied WebSocket data: node={websocket_progress.get('current_node')}, steps={websocket_progress.get('step_current')}/{websocket_progress.get('step_total')}, progress: {old_percentage:.1f}% -> {progress.percentage:.1f}%")
                                        else:
                                            # Fallback to time-based estimation if no WebSocket data or data is stale
                                            elapsed = current_time - progress.start_time
                                            if elapsed > 10:  # After 10 seconds, start showing progress
                                                # Rough estimate based on generation type
                                                if "video" in str(progress._workflow_data).lower():
                                                    estimated_total = 180  # 3 minutes average for video
                                                else:
                                                    estimated_total = 45   # 45 seconds average for image
                                                
                                                estimated_progress = min(85, (elapsed / estimated_total) * 100)
                                                if estimated_progress > progress.percentage:
                                                    old_percentage = progress.percentage
                                                    progress.percentage = estimated_progress
                                                    if progress.percentage < 30:
                                                        progress.phase = "Processing prompt"
                                                    elif progress.percentage < 60:
                                                        progress.phase = "Generating image"
                                                    else:
                                                        progress.phase = "Refining details"
                                                    self.logger.info(f"📊 Time-based estimate: {old_percentage:.1f}% -> {progress.percentage:.1f}%")
                                    else:
                                        # Not in queue and not running - check if we have WebSocket activity
                                        if not execution_started and websocket_progress and 'step_current' in websocket_progress:
                                            # We have WebSocket activity but HTTP polling doesn't see it as running
                                            # This can happen during the brief transition period
                                            execution_started = True
                                            progress.update_execution_start()
                                            self.logger.info(f"Prompt {prompt_id} execution detected via WebSocket activity")
                                            last_status = "running (WebSocket detected)"
                                            
                                        # Apply WebSocket data if we have execution activity
                                        if execution_started and websocket_progress:
                                            websocket_data_age = current_time - websocket_progress.get('last_websocket_update', 0)
                                            if websocket_data_age < 10.0:  # Use WebSocket data if less than 10 seconds old
                                                old_percentage = progress.percentage
                                                
                                                if 'current_node' in websocket_progress:
                                                    progress.update_node_execution(websocket_progress['current_node'])
                                                    
                                                if 'cached_nodes' in websocket_progress:
                                                    progress.update_cached_nodes(websocket_progress['cached_nodes'])
                                                    
                                                if 'step_current' in websocket_progress and 'step_total' in websocket_progress:
                                                    progress.update_step_progress(
                                                        websocket_progress['step_current'], 
                                                        websocket_progress['step_total']
                                                    )
                                                    
                                                self.logger.info(f"📊 Applied WebSocket data (no HTTP queue): node={websocket_progress.get('current_node')}, steps={websocket_progress.get('step_current')}/{websocket_progress.get('step_total')}, progress: {old_percentage:.1f}% -> {progress.percentage:.1f}%")
                                        
                                        # Check if execution completed but was missed by queue status
                                        if execution_started and last_status == "running":
                                            # Was running, now not found - likely completed
                                            self.logger.info(f"Prompt {prompt_id} no longer in queue - checking completion")
                                        elif not execution_started:
                                            # Never started, might be an error or very fast execution
                                            progress.phase = "Checking status..."
                
                except Exception as e:
                    self.logger.debug(f"Queue check error: {e}")
                
                # Send progress updates more frequently - every second, and with smaller thresholds
                if progress_callback and (current_time - last_update_time >= check_interval):
                    progress_change = abs(progress.percentage - last_progress_sent)
                    # Lower threshold: update if 0.5% change, queued status, or every 5 seconds
                    time_since_last = current_time - last_update_time
                    should_update = (
                        progress_change >= 0.5 or 
                        progress.status == "queued" or 
                        time_since_last >= 5.0 or
                        execution_started and time_since_last >= 2.0  # More frequent updates when running
                    )
                    
                    if should_update:
                        try:
                            self.logger.info(f"📤 Sending progress update: {progress.percentage:.1f}%, status={progress.status}, phase={progress.phase}")
                            await progress_callback(progress)
                            last_update_time = current_time
                            last_progress_sent = progress.percentage
                            progress_update_count += 1
                        except Exception as e:
                            self.logger.warning(f"Progress callback error: {e}")
                
                # Wait before next check (1 second)
                await asyncio.sleep(check_interval)
                
                # Log progress periodically (every 15 seconds for more frequent feedback)
                elapsed = current_time - start_time
                if elapsed % 15 < check_interval and elapsed > 15:
                    status_msg = f"Status: {last_status or 'unknown'}"
                    if websocket_progress:
                        ws_age = current_time - websocket_progress.get('last_websocket_update', 0)
                        status_msg += f" | WebSocket: {len(websocket_progress)} data points (age: {ws_age:.1f}s)"
                    status_msg += f" | Updates sent: {progress_update_count}"
                    self.logger.info(f"Still waiting for prompt {prompt_id}... ({elapsed:.0f}s) - {status_msg}")
            
            # Clean up WebSocket task
            if websocket_task:
                websocket_task.cancel()
            
            # Timeout reached
            elapsed = time.time() - start_time
            self.logger.error(f"Timeout waiting for prompt {prompt_id} after {elapsed:.0f} seconds")
            raise ComfyUIAPIError(f"Generation timeout after {max_wait_time} seconds - this may indicate ComfyUI is overloaded")
            
        except Exception as e:
            if "timeout" not in str(e).lower():
                self.logger.error(f"Error in enhanced polling: {e}")
            raise
    
    async def _download_images(self, history: Dict[str, Any]) -> List[bytes]:
        """Download generated images from ComfyUI."""
        try:
            images = []
            
            # Comprehensive null checking for history data
            if history is None:
                raise ComfyUIAPIError("History data is None - generation may have failed")
            
            if not isinstance(history, dict):
                raise ComfyUIAPIError(f"Invalid history data type: {type(history)}, expected dict")
            
            outputs = history.get('outputs')
            if outputs is None:
                self.logger.warning("No outputs found in history data")
                # Check if we have a different structure
                if 'prompt_id' in history and len(history) > 1:
                    self.logger.debug(f"History structure: {list(history.keys())}")
                raise ComfyUIAPIError("No outputs found in generation result")
            
            if not isinstance(outputs, dict):
                raise ComfyUIAPIError(f"Invalid outputs data type: {type(outputs)}, expected dict")
            
            for node_id, node_output in outputs.items():
                if node_output is None:
                    continue
                    
                if not isinstance(node_output, dict):
                    self.logger.debug(f"Skipping invalid node output for {node_id}: {type(node_output)}")
                    continue
                    
                if 'images' in node_output:
                    node_images = node_output['images']
                    if not isinstance(node_images, list):
                        self.logger.debug(f"Skipping invalid images data for {node_id}: {type(node_images)}")
                        continue
                        
                    for image_info in node_images:
                        if not isinstance(image_info, dict):
                            self.logger.debug(f"Skipping invalid image info: {type(image_info)}")
                            continue
                            
                        filename = image_info.get('filename')
                        if not filename:
                            self.logger.debug(f"Skipping image with missing filename: {image_info}")
                            continue
                            
                        subfolder = image_info.get('subfolder', '')
                        image_type = image_info.get('type', 'output')
                        
                        # Download image
                        params = {
                            'filename': filename,
                            'subfolder': subfolder,
                            'type': image_type
                        }
                        
                        try:
                            async with self.session.get(f"{self.base_url}/view", params=params) as response:
                                if response.status == 200:
                                    image_data = await response.read()
                                    if image_data:  # Ensure we got actual data
                                        images.append(image_data)
                                        self.logger.debug(f"Downloaded image: {filename}")
                                    else:
                                        self.logger.warning(f"Downloaded empty image data for {filename}")
                                else:
                                    self.logger.error(f"Failed to download image {filename}: {response.status}")
                        except Exception as download_error:
                            self.logger.error(f"Error downloading image {filename}: {download_error}")
                            continue
            
            if not images:
                # Log the structure for debugging
                self.logger.error(f"No images found in generation output. History structure: {list(history.keys()) if isinstance(history, dict) else type(history)}")
                if isinstance(history, dict) and 'outputs' in history:
                    self.logger.error(f"Outputs structure: {list(history['outputs'].keys()) if isinstance(history['outputs'], dict) else type(history['outputs'])}")
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
        lora_name: Optional[str] = None,
        lora_strength: float = 1.0,
        progress_callback=None
    ) -> Tuple[List[bytes], Dict[str, Any]]:
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
            lora_name: Name of LoRA to use (optional)
            lora_strength: Strength of the selected LoRA
            progress_callback: Optional callback for progress updates
        
        Returns:
            Tuple of (list_of_image_data, generation_info)
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
                workflow, prompt, negative_prompt, width, height, steps, cfg, seed, batch_size, lora_name, lora_strength
            )
            
            # Queue prompt
            prompt_id, client_id = await self._queue_prompt(updated_workflow)
            
            # Wait for completion
            history = await self._wait_for_completion_with_websocket(prompt_id, client_id, updated_workflow, progress_callback)
            
            # Download images - return as individual images, not collage
            images = await self._download_images(history)
            
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
                'lora_name': lora_name,
                'lora_strength': lora_strength,
                'timestamp': time.time()
            }
            
            self.logger.info(f"Image generation completed successfully: {len(images)} images")
            return images, generation_info
            
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
            prompt_id, client_id = await self._queue_prompt(updated_workflow)
            
            # Wait for completion
            history = await self._wait_for_completion_with_websocket(prompt_id, client_id, updated_workflow, progress_callback)
            
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
        """Update upscale workflow parameters with minimal changes - only image and prompts."""
        try:
            # Create a copy to avoid modifying the original
            updated_workflow = json.loads(json.dumps(workflow))
            
            # Generate random seed if not provided
            if seed is None:
                import random
                seed = random.randint(0, 2**32 - 1)
            
            # Update workflow parameters based on the upscale workflow structure
            # Only change essential parameters: input image and prompts
            for node_id, node_data in updated_workflow.items():
                class_type = node_data.get('class_type')
                
                if class_type == 'LoadImage':
                    # Update input image - this is essential
                    node_data['inputs']['image'] = input_image_path
                
                elif class_type == 'CLIPTextEncode':
                    title = node_data.get('_meta', {}).get('title', '')
                    if 'positive' in title.lower():
                        # Only update if prompt is provided
                        if prompt:
                            node_data['inputs']['text'] = prompt
                    elif 'negative' in title.lower():
                        # Only update if negative prompt is provided
                        if negative_prompt:
                            node_data['inputs']['text'] = negative_prompt
                
                # Note: We're NOT changing UltimateSDUpscale parameters to preserve workflow defaults
                # Note: We're NOT changing LoraTextExtractor to avoid interfering with workflow
            
            self.logger.debug(f"Updated upscale workflow parameters: input={input_image_path}, minimal changes")
            return updated_workflow
            
        except Exception as e:
            self.logger.error(f"Failed to update upscale workflow parameters: {e}")
            raise ComfyUIAPIError(f"Failed to update upscale workflow parameters: {e}")
    
    async def generate_edit(
        self,
        input_image_data: bytes,
        edit_prompt: str,
        width: int = 1024,
        height: int = 1024,
        steps: int = 20,
        cfg: float = 2.5,
        seed: Optional[int] = None,
        progress_callback=None
    ) -> Tuple[bytes, Dict[str, Any]]:
        """
        Edit an image using ComfyUI edit workflow with Flux Kontext.
        
        Args:
            input_image_data: Image data as bytes
            edit_prompt: Prompt describing the desired edit
            width: Output image width (default: 1024)
            height: Output image height (default: 1024)
            steps: Number of sampling steps (default: 20)
            cfg: CFG scale (default: 2.5)
            seed: Random seed (auto-generated if None)
            progress_callback: Optional callback for progress updates
        
        Returns:
            Tuple of (edited_image_data, edit_info)
        """
        try:
            # Validate inputs
            if not input_image_data:
                raise ValueError("Input image data cannot be empty")
            
            if not edit_prompt.strip():
                raise ValueError("Edit prompt cannot be empty")
            
            if len(edit_prompt) > self.config.security.max_prompt_length:
                raise ValueError(f"Edit prompt too long (max {self.config.security.max_prompt_length} characters)")
            
            # Upload image to ComfyUI
            upload_filename = f"edit_input_{int(time.time())}.png"
            uploaded_filename = await self.upload_image(input_image_data, upload_filename)
            
            # Use edit workflow
            workflow_name = "flux_kontext_edit"
            
            self.logger.info(f"Starting image editing: {uploaded_filename} with prompt: '{edit_prompt[:50]}...'")
            
            # Load and update workflow
            workflow = self._load_workflow(workflow_name)
            updated_workflow = self._update_edit_workflow_parameters(
                workflow, uploaded_filename, edit_prompt, width, height, steps, cfg, seed
            )
            
            # Queue prompt
            prompt_id, client_id = await self._queue_prompt(updated_workflow)
            
            # Wait for completion
            history = await self._wait_for_completion_with_websocket(prompt_id, client_id, updated_workflow, progress_callback)
            
            # Download edited image
            images = await self._download_images(history)
            edited_image_data = images[0] if images else b''
            
            # Prepare edit info
            edit_info = {
                'prompt_id': prompt_id,
                'input_image': uploaded_filename,
                'edit_prompt': edit_prompt,
                'width': width,
                'height': height,
                'steps': steps,
                'cfg': cfg,
                'seed': seed,
                'workflow': workflow_name,
                'timestamp': time.time(),
                'type': 'edit'
            }
            
            self.logger.info(f"Image editing completed successfully")
            return edited_image_data, edit_info
            
        except Exception as e:
            self.logger.error(f"Image editing failed: {e}")
            raise ComfyUIAPIError(f"Image editing failed: {e}")
    
    def _update_edit_workflow_parameters(
        self,
        workflow: Dict[str, Any],
        input_image_path: str,
        edit_prompt: str,
        width: int = 1024,
        height: int = 1024,
        steps: int = 20,
        cfg: float = 2.5,
        seed: Optional[int] = None
    ) -> Dict[str, Any]:
        """Update edit workflow parameters for Flux Kontext editing."""
        try:
            # Create a copy to avoid modifying the original
            updated_workflow = json.loads(json.dumps(workflow))
            
            # Generate random seed if not provided
            if seed is None:
                import random
                seed = random.randint(0, 2**32 - 1)
            
            # Update workflow parameters based on the flux_kontext_edit.json structure
            for node_id, node_data in updated_workflow.items():
                class_type = node_data.get('class_type')
                
                if class_type == 'LoadImage':
                    # Update input image (node 41)
                    node_data['inputs']['image'] = input_image_path
                
                elif class_type == 'CLIPTextEncode':
                    # Update edit prompt (node 6 - positive prompt)
                    title = node_data.get('_meta', {}).get('title', '')
                    if 'Positive' in title:
                        node_data['inputs']['text'] = edit_prompt
                
                elif class_type == 'RandomNoise':
                    # Update seed (node 25)
                    node_data['inputs']['noise_seed'] = seed
                
                elif class_type == 'BasicScheduler':
                    # Update steps (node 17)
                    node_data['inputs']['steps'] = steps
                
                elif class_type == 'FluxGuidance':
                    # Update CFG/guidance (node 26)
                    node_data['inputs']['guidance'] = cfg
                
                elif class_type == 'EmptySD3LatentImage':
                    # Update dimensions (node 27)
                    node_data['inputs']['width'] = width
                    node_data['inputs']['height'] = height
                
                elif class_type == 'ModelSamplingFlux':
                    # Update dimensions for ModelSamplingFlux (node 30)
                    node_data['inputs']['width'] = width
                    node_data['inputs']['height'] = height
            
            self.logger.debug(f"Updated edit workflow parameters: prompt='{edit_prompt[:50]}...', size={width}x{height}")
            return updated_workflow
            
        except Exception as e:
            self.logger.error(f"Failed to update edit workflow parameters: {e}")
            raise ComfyUIAPIError(f"Failed to update edit workflow parameters: {e}")
    
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
    
    async def get_available_loras(self) -> List[Dict[str, str]]:
        """Get list of available LoRAs from ComfyUI."""
        try:
            if not self.session:
                raise RuntimeError("Session not initialized")
            
            async with self.session.get(f"{self.base_url}/object_info/LoraLoaderModelOnly") as response:
                if response.status == 200:
                    object_info = await response.json()
                    lora_list = object_info.get("LoraLoaderModelOnly", {}).get("input", {}).get("required", {}).get("lora_name", [])
                    
                    if isinstance(lora_list, list) and len(lora_list) > 0:
                        # Extract the actual LoRA names from the nested structure
                        lora_names = lora_list[0] if isinstance(lora_list[0], list) else lora_list
                        
                        loras = []
                        for lora_name in lora_names:
                            if isinstance(lora_name, str):
                                loras.append({
                                    'filename': lora_name,
                                    'display_name': lora_name.replace('.safetensors', '').replace('_', ' ').title(),
                                    'type': 'hidream' if 'hidream' in lora_name.lower() else 'flux'
                                })
                        
                        self.logger.info(f"Found {len(loras)} LoRAs")
                        return loras
                    else:
                        self.logger.warning("No LoRAs found in ComfyUI response")
                        return []
                else:
                    self.logger.error(f"Failed to fetch LoRAs: {response.status}")
                    return []
                    
        except Exception as e:
            self.logger.error(f"Failed to get available LoRAs: {e}")
            return []
    
    def filter_loras_by_model(self, loras: List[Dict[str, str]], model_type: str) -> List[Dict[str, str]]:
        """Filter LoRAs based on the selected model type."""
        try:
            if model_type.lower() == 'hidream':
                # Only include LoRAs with 'hidream' in the name
                filtered = [lora for lora in loras if 'hidream' in lora['filename'].lower()]
            elif model_type.lower() == 'flux':
                # Include LoRAs that don't have 'hidream' in the name
                filtered = [lora for lora in loras if 'hidream' not in lora['filename'].lower()]
            else:
                # Unknown model type, return all
                filtered = loras
            
            self.logger.debug(f"Filtered {len(filtered)} LoRAs for model type '{model_type}'")
            return filtered
            
        except Exception as e:
            self.logger.error(f"Failed to filter LoRAs: {e}")
            return loras

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