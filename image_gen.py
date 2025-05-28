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
    
    async def _queue_prompt(self, workflow: Dict[str, Any]) -> str:
        """Queue a prompt for generation in ComfyUI."""
        try:
            # Use queue lock to prevent concurrent queuing conflicts
            async with self._queue_lock:
                client_id = str(uuid.uuid4())
                self.logger.info(f"🔄 Queuing prompt with client_id: {client_id}")
                
                prompt_data = {
                    "prompt": workflow,
                    "client_id": client_id
                }
                
                # Add timeout to prevent hanging
                timeout = aiohttp.ClientTimeout(total=30)
                async with self.session.post(
                    f"{self.base_url}/prompt",
                    json=prompt_data,
                    timeout=timeout
                ) as response:
                    self.logger.info(f"📋 Queue response status: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        self.logger.info(f"📋 Queue response: {str(result)[:100]}...")
                        
                        if 'prompt_id' in result:
                            prompt_id = result['prompt_id']
                            self.logger.info(f"✅ Successfully queued prompt with ID: {prompt_id}")
                            return prompt_id
                        else:
                            raise ComfyUIAPIError(f"No prompt_id in response: {result}")
                    else:
                        error_text = await response.text()
                        raise ComfyUIAPIError(f"Failed to queue prompt: {response.status} - {error_text}")
                        
        except asyncio.TimeoutError:
            raise ComfyUIAPIError("Timeout while queuing prompt - ComfyUI may be overloaded")
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
            
            # Send initial progress
            if progress_callback:
                await progress_callback(progress)
            
            # Simple polling approach first - WebSocket was getting too many irrelevant messages
            self.logger.info(f"Using polling method for prompt {prompt_id}")
            return await self._wait_for_completion_polling(prompt_id, progress_callback)
                
        except Exception as e:
            self.logger.error(f"Error in WebSocket progress monitoring: {e}")
            # Fallback to polling method
            return await self._wait_for_completion_polling(prompt_id, progress_callback)
    
    async def _wait_for_completion_polling(self, prompt_id: str, progress_callback=None) -> Dict[str, Any]:
        """Simplified polling method focused on getting results with proper ComfyUI queue integration."""
        try:
            max_wait_time = self.config.comfyui.timeout
            check_interval = 3.0  # Check every 3 seconds
            start_time = time.time()
            
            progress = ProgressInfo()
            
            self.logger.info(f"Starting polling for prompt {prompt_id}")
            
            while time.time() - start_time < max_wait_time:
                # Check history first for completion
                try:
                    async with self.session.get(f"{self.base_url}/history/{prompt_id}") as response:
                        if response.status == 200:
                            try:
                                history_data = await response.json()
                                # Robust null checking for concurrent operations
                                if history_data is not None and isinstance(history_data, dict) and prompt_id in history_data:
                                    # Mark as completed and return
                                    progress.mark_completed()
                                    if progress_callback:
                                        try:
                                            await progress_callback(progress)
                                        except Exception:
                                            pass
                                    return history_data[prompt_id]
                            except (ValueError, TypeError) as json_error:
                                # Invalid JSON response - might be temporary during high load
                                self.logger.debug(f"Invalid JSON in history response: {json_error}")
                except Exception as e:
                    # Only log occasionally to avoid spam
                    if (time.time() - start_time) % 30 < check_interval:
                        self.logger.warning(f"Error checking history: {e}")
                
                # Check ComfyUI queue status for proper queue integration
                try:
                    async with self.session.get(f"{self.base_url}/queue") as response:
                        if response.status == 200:
                            try:
                                queue_data = await response.json()
                                
                                # Robust null checking for concurrent operations
                                if queue_data is not None and isinstance(queue_data, dict):
                                    queue_running = queue_data.get('queue_running')
                                    queue_pending = queue_data.get('queue_pending')
                                    
                                    # Additional validation for queue data
                                    if queue_running is not None and queue_pending is not None:
                                        # Check if our prompt is currently running
                                        is_running = False
                                        if isinstance(queue_running, list):
                                            for item in queue_running:
                                                try:
                                                    # ComfyUI queue format: [number, {prompt_id: ...}]
                                                    if isinstance(item, list) and len(item) >= 2:
                                                        if isinstance(item[1], dict) and item[1].get('prompt_id') == prompt_id:
                                                            is_running = True
                                                            self.logger.debug(f"Prompt {prompt_id} is currently running")
                                                            break
                                                    # Also handle direct dict format just in case
                                                    elif isinstance(item, dict) and item.get('prompt_id') == prompt_id:
                                                        is_running = True
                                                        self.logger.debug(f"Prompt {prompt_id} is currently running (direct format)")
                                                        break
                                                except (AttributeError, TypeError):
                                                    # Skip malformed queue items
                                                    continue
                                        
                                        if is_running:
                                            # Prompt is actively running
                                            if progress.status != "running":
                                                progress.status = "running"
                                                progress.phase = "Generating"
                                                progress.queue_position = 0
                                                self.logger.info(f"Prompt {prompt_id} started running")
                                        else:
                                            # Check if prompt is in pending queue
                                            queue_position = None
                                            if isinstance(queue_pending, list):
                                                for i, item in enumerate(queue_pending):
                                                    try:
                                                        # ComfyUI queue format: [number, {prompt_id: ...}]
                                                        if isinstance(item, list) and len(item) >= 2:
                                                            if isinstance(item[1], dict) and item[1].get('prompt_id') == prompt_id:
                                                                queue_position = i + 1
                                                                break
                                                        # Also handle direct dict format just in case
                                                        elif isinstance(item, dict) and item.get('prompt_id') == prompt_id:
                                                            queue_position = i + 1
                                                            break
                                                    except (AttributeError, TypeError):
                                                        # Skip malformed queue items
                                                        continue
                                            
                                            if queue_position is not None:
                                                # Prompt is in queue
                                                if progress.status != "queued" or progress.queue_position != queue_position:
                                                    progress.update_queue_status(queue_position)
                                                    self.logger.info(f"Prompt {prompt_id} is #{queue_position} in queue")
                                            else:
                                                # Prompt not found in queue - might be starting up or just completed
                                                if progress.status == "initializing":
                                                    progress.status = "running"
                                                    progress.phase = "Starting"
                                                    progress.queue_position = 0
                                        
                                        # Send progress update every 10 seconds
                                        elapsed = time.time() - start_time
                                        if progress_callback and (elapsed % 10 < check_interval or progress.status != getattr(progress, '_last_status', None)):
                                            try:
                                                await progress_callback(progress)
                                                progress._last_status = progress.status
                                            except Exception:
                                                pass
                                else:
                                    # Queue data is None or invalid - might be temporary during high load
                                    self.logger.debug(f"Invalid queue data format: {type(queue_data)}")
                                    
                            except (ValueError, TypeError) as json_error:
                                # Invalid JSON response - might be temporary during high load
                                self.logger.debug(f"Invalid JSON in queue response: {json_error}")
                        else:
                            self.logger.debug(f"Queue endpoint returned status {response.status}")
                            
                except Exception as e:
                    # Only warn occasionally to reduce log spam
                    if (time.time() - start_time) % 30 < check_interval:
                        self.logger.warning(f"Error checking queue: {e}")
                
                # Wait before next check
                await asyncio.sleep(check_interval)
                
                # Log progress every 30 seconds only
                elapsed = time.time() - start_time
                if elapsed % 30 < check_interval and elapsed > 30:
                    status_info = f"Status: {progress.status}"
                    if progress.status == "queued":
                        status_info += f" (#{progress.queue_position})"
                    self.logger.info(f"Still waiting for prompt {prompt_id}... ({elapsed:.0f}s elapsed) - {status_info}")
            
            # Timeout reached
            raise ComfyUIAPIError(f"Timeout waiting for prompt {prompt_id} after {max_wait_time} seconds")
            
        except Exception as e:
            if "Timeout" not in str(e):
                self.logger.error(f"Error in polling method: {e}")
            raise
    
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
            prompt_id = await self._queue_prompt(updated_workflow)
            
            # Wait for completion
            history = await self._wait_for_completion_with_websocket(prompt_id, updated_workflow, progress_callback)
            
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