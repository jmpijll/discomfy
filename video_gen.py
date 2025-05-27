"""
Video generation component for Discord ComfyUI Bot.
Handles video generation logic and ComfyUI API calls for video workflows.
"""

import json
import asyncio
import logging
from io import BytesIO
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
import aiohttp

from image_gen import ImageGenerator, ComfyUIAPIError
from config import get_config, BotConfig

class VideoGenerator(ImageGenerator):
    """Handles video generation using ComfyUI API, extending ImageGenerator."""
    
    def __init__(self):
        super().__init__()
        self.logger = logging.getLogger(__name__)
    
    def _update_video_workflow_parameters(
        self,
        workflow: Dict[str, Any],
        prompt: str,
        negative_prompt: str = "",
        width: int = 720,
        height: int = 720,
        steps: int = 6,
        cfg: float = 1.0,
        length: int = 81,
        strength: float = 0.7,
        seed: Optional[int] = None,
        input_image_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update video workflow parameters with user inputs."""
        try:
            # Create a copy to avoid modifying the original
            updated_workflow = json.loads(json.dumps(workflow))
            
            # Generate random seed if not provided
            if seed is None:
                import random
                seed = random.randint(0, 2**32 - 1)
            
            # Find node types in the workflow
            node_types = {node_id: node_data.get('class_type') for node_id, node_data in updated_workflow.items()}
            
            # Update text prompts
            for node_id, node_data in updated_workflow.items():
                class_type = node_data.get('class_type')
                
                if class_type == 'CLIPTextEncode':
                    title = node_data.get('_meta', {}).get('title', '')
                    if 'Positive' in title:
                        node_data['inputs']['text'] = prompt
                    elif 'Negative' in title:
                        node_data['inputs']['text'] = negative_prompt
                
                elif class_type == 'KSampler':
                    node_data['inputs']['seed'] = seed
                    node_data['inputs']['steps'] = steps
                    node_data['inputs']['cfg'] = cfg
                
                elif class_type == 'WanVaceToVideo':
                    node_data['inputs']['width'] = width
                    node_data['inputs']['height'] = height
                    node_data['inputs']['strength'] = strength
                
                elif class_type == 'PrimitiveInt' and node_data.get('_meta', {}).get('title') == 'Length':
                    node_data['inputs']['value'] = length
                
                elif class_type == 'ImageResizeKJv2':
                    node_data['inputs']['width'] = width
                    node_data['inputs']['height'] = height
                
                elif class_type == 'LoadImage' and input_image_path:
                    node_data['inputs']['image'] = input_image_path
            
            self.logger.debug(f"Updated video workflow parameters: prompt='{prompt[:50]}...', size={width}x{height}, length={length}")
            return updated_workflow
            
        except Exception as e:
            self.logger.error(f"Failed to update video workflow parameters: {e}")
            raise ComfyUIAPIError(f"Failed to update video workflow parameters: {e}")
    
    async def _download_videos(self, history: Dict[str, Any]) -> Tuple[bytes, str]:
        """Download generated video from ComfyUI."""
        try:
            outputs = history.get('outputs', {})
            
            for node_id, node_output in outputs.items():
                if 'gifs' in node_output:
                    # Handle video output from VHS_VideoCombine
                    for video_info in node_output['gifs']:
                        filename = video_info['filename']
                        subfolder = video_info.get('subfolder', '')
                        video_type = video_info.get('type', 'output')
                        
                        # Download video
                        params = {
                            'filename': filename,
                            'subfolder': subfolder,
                            'type': video_type
                        }
                        
                        async with self.session.get(f"{self.base_url}/view", params=params) as response:
                            if response.status == 200:
                                video_data = await response.read()
                                self.logger.info(f"Downloaded video: {filename} ({len(video_data)} bytes)")
                                return video_data, filename
                            else:
                                self.logger.error(f"Failed to download video {filename}: {response.status}")
            
            raise ComfyUIAPIError("No video found in generation output")
            
        except Exception as e:
            self.logger.error(f"Failed to download video: {e}")
            raise ComfyUIAPIError(f"Failed to download video: {e}")
    
    async def generate_video(
        self,
        prompt: str,
        negative_prompt: str = "",
        workflow_name: Optional[str] = None,
        width: int = 720,
        height: int = 720,
        steps: int = 6,
        cfg: float = 1.0,
        length: int = 81,
        strength: float = 0.7,
        seed: Optional[int] = None,
        input_image_data: Optional[bytes] = None,
        progress_callback=None
    ) -> Tuple[bytes, str, Dict[str, Any]]:
        """
        Generate video using ComfyUI.
        
        Args:
            prompt: Positive prompt for generation
            negative_prompt: Negative prompt for generation
            workflow_name: Name of workflow to use
            width: Video width
            height: Video height
            steps: Number of sampling steps
            cfg: CFG scale
            length: Video length in frames
            strength: Strength for image-to-video conversion
            seed: Random seed (auto-generated if None)
            input_image_data: Image data as bytes for I2V
            progress_callback: Optional callback for progress updates
        
        Returns:
            Tuple of (video_data, filename, generation_info)
        """
        try:
            # Validate inputs
            if not prompt.strip():
                raise ValueError("Prompt cannot be empty")
            
            if len(prompt) > self.config.security.max_prompt_length:
                raise ValueError(f"Prompt too long (max {self.config.security.max_prompt_length} characters)")
            
            # Upload image to ComfyUI if provided
            uploaded_filename = None
            if input_image_data:
                upload_filename = f"video_input_{int(__import__('time').time())}.png"
                uploaded_filename = await self.upload_image(input_image_data, upload_filename)
            
            # Use default video workflow if none specified
            if not workflow_name:
                # Find first video workflow
                for name, config in self.config.workflows.items():
                    if config.type == 'video' and config.enabled:
                        workflow_name = name
                        break
                
                if not workflow_name:
                    raise ValueError("No video workflow available")
            
            self.logger.info(f"Starting video generation: '{prompt[:50]}...' (length: {length} frames)")
            
            # Load and update workflow
            workflow = self._load_workflow(workflow_name)
            updated_workflow = self._update_video_workflow_parameters(
                workflow, prompt, negative_prompt, width, height, steps, cfg, length, strength, seed, uploaded_filename
            )
            
            # Queue prompt
            prompt_id = await self._queue_prompt(updated_workflow)
            
            # Wait for completion
            history = await self._wait_for_completion(prompt_id, progress_callback)
            
            # Download video
            video_data, filename = await self._download_videos(history)
            
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
                'length': length,
                'strength': strength,
                'seed': seed,
                'input_image': uploaded_filename,
                'filename': filename,
                'timestamp': __import__('time').time(),
                'type': 'video'
            }
            
            self.logger.info(f"Video generation completed successfully: {filename}")
            return video_data, filename, generation_info
            
        except Exception as e:
            self.logger.error(f"Video generation failed: {e}")
            raise ComfyUIAPIError(f"Video generation failed: {e}")

# Utility functions for video file management
def save_output_video(video_data: bytes, filename: str) -> Path:
    """Save generated video to output directory."""
    try:
        output_dir = Path("outputs")
        output_dir.mkdir(exist_ok=True)
        
        output_path = output_dir / filename
        with open(output_path, 'wb') as f:
            f.write(video_data)
        
        return output_path
        
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to save output video: {e}")
        raise

def get_unique_video_filename(base_name: str, extension: str = ".mp4") -> str:
    """Generate a unique filename for video output."""
    import time
    import random
    timestamp = int(time.time())
    random_suffix = random.randint(1000, 9999)
    return f"{base_name}_{timestamp}_{random_suffix}{extension}" 