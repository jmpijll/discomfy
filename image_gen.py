"""
Image generation component for Discord ComfyUI Bot.
Handles all image generation logic and ComfyUI API calls.
"""

import json
import uuid
import asyncio
import logging
import websocket
import requests
import random
from io import BytesIO
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Union
from PIL import Image
import aiohttp
import time

from config import get_config, BotConfig

class ComfyUIAPIError(Exception):
    """Custom exception for ComfyUI API errors."""
    pass

class ImageGenerator:
    """Handles image generation using ComfyUI API."""
    
    def __init__(self):
        self.config: BotConfig = get_config()
        self.logger = logging.getLogger(__name__)
        self.base_url = self.config.comfyui.url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def __aenter__(self):
        """Async context manager entry."""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=self.config.comfyui.timeout)
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.session:
            await self.session.close()
    
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
    
    async def _wait_for_completion(self, prompt_id: str, progress_callback=None) -> Dict[str, Any]:
        """Wait for prompt completion and return the history."""
        try:
            max_wait_time = self.config.comfyui.timeout
            check_interval = 2.0
            start_time = time.time()
            
            while time.time() - start_time < max_wait_time:
                # Check history for completion
                async with self.session.get(f"{self.base_url}/history/{prompt_id}") as response:
                    if response.status == 200:
                        history = await response.json()
                        if prompt_id in history:
                            self.logger.info(f"Prompt {prompt_id} completed successfully")
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
                                        return history[prompt_id]
                            
                            raise ComfyUIAPIError(f"Prompt {prompt_id} disappeared from queue without completion")
                        
                        if progress_callback:
                            status = "running" if is_running else "pending"
                            queue_position = len(queue_pending) if is_pending else 0
                            await progress_callback(status, queue_position)
                
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
            history = await self._wait_for_completion(prompt_id, progress_callback)
            
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