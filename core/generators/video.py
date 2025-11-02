"""
Video Generator for DisComfy v2.0.

Refactored from old video_gen.py to follow the new BaseGenerator architecture.
"""

import json
import logging
import random
import time
from typing import Dict, Any, Optional, Tuple
from pathlib import Path

from core.generators.base import BaseGenerator, GenerationRequest, GenerationResult, GeneratorType
from core.comfyui.client import ComfyUIClient
from core.exceptions import ValidationError, ComfyUIError, GenerationError


class VideoGenerationRequest(GenerationRequest):
    """Extended request for video generation with video-specific parameters."""
    negative_prompt: str = ""
    width: int = 720
    height: int = 720
    steps: int = 6
    cfg: float = 1.0
    length: int = 81  # Video length in frames
    strength: float = 0.7  # Strength for image-to-video conversion
    image_data: Optional[bytes] = None  # Optional input image for I2V


class VideoGenerator(BaseGenerator):
    """
    Handles video generation using ComfyUI API.
    
    Follows the new v2.0 architecture pattern from BaseGenerator.
    """
    
    def __init__(self, comfyui_client: ComfyUIClient, config):
        """Initialize video generator with shared ComfyUI client."""
        super().__init__(comfyui_client, config)
        self.logger = logging.getLogger(__name__)
    
    @property
    def generator_type(self) -> GeneratorType:
        """Return video generator type."""
        return GeneratorType.VIDEO
    
    async def validate_request(self, request: VideoGenerationRequest) -> None:
        """
        Validate video generation request.
        
        Args:
            request: Video generation request to validate
            
        Raises:
            ValidationError: If request is invalid
        """
        # Video-specific validation
        if request.length < 1:
            raise ValidationError("Video length must be at least 1 frame")
        
        if request.length > 300:  # Reasonable upper limit
            raise ValidationError("Video length cannot exceed 300 frames")
        
        if not 0.0 <= request.strength <= 1.0:
            raise ValidationError("Strength must be between 0.0 and 1.0")
    
    async def generate(
        self,
        request: VideoGenerationRequest,
        progress_callback=None
    ) -> GenerationResult:
        """
        Generate video using ComfyUI.
        
        Args:
            request: Video generation request
            progress_callback: Optional callback for progress updates
            
        Returns:
            GenerationResult with video data
            
        Raises:
            GenerationError: If generation fails
        """
        try:
            # Validate request
            await self.validate_request(request)
            
            # Upload input image if provided
            uploaded_filename = None
            if request.image_data:
                upload_filename = f"video_input_{int(__import__('time').time())}.png"
                uploaded_filename = await self.client.upload_image(
                    request.image_data, 
                    upload_filename
                )
            
            # Load and update workflow
            workflow = await self._load_workflow(request.workflow_name)
            updated_workflow = self._update_video_workflow_parameters(
                workflow=workflow,
                prompt=request.prompt,
                negative_prompt=request.negative_prompt,
                width=request.width,
                height=request.height,
                steps=request.steps,
                cfg=request.cfg,
                length=request.length,
                strength=request.strength,
                seed=request.seed,
                input_image_path=uploaded_filename
            )
            
            self.logger.info(
                f"🎬 Starting video generation: '{request.prompt[:50]}...' "
                f"(length: {request.length} frames, {request.width}x{request.height})"
            )
            
            # Queue prompt
            prompt_id = await self.client.queue_prompt(updated_workflow)
            
            if not prompt_id:
                raise GenerationError("Failed to get prompt_id from queue response")
            
            # Wait for completion with progress updates
            history = await self._wait_for_completion(
                prompt_id=prompt_id,
                workflow=updated_workflow,
                progress_callback=progress_callback
            )
            
            # Download video
            video_data, filename = await self._download_videos(history)
            
            # Return result
            generation_info = {
                'prompt_id': prompt_id,
                'prompt': request.prompt,
                'negative_prompt': request.negative_prompt,
                'workflow': request.workflow_name,
                'width': request.width,
                'height': request.height,
                'steps': request.steps,
                'cfg': request.cfg,
                'length': request.length,
                'strength': request.strength,
                'seed': request.seed,
                'input_image': uploaded_filename,
                'filename': filename,
                'type': 'video'
            }
            
            return GenerationResult(
                output_data=video_data,
                generation_info=generation_info,
                generation_type=GeneratorType.VIDEO
            )
            
        except ValidationError:
            raise
        except ComfyUIError:
            raise
        except Exception as e:
            self.logger.error(f"Video generation failed: {e}")
            raise GenerationError(f"Video generation failed: {e}")
    
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
        """
        Update video workflow parameters with user inputs.
        
        Args:
            workflow: Base workflow dictionary
            prompt: Positive prompt
            negative_prompt: Negative prompt
            width: Video width
            height: Video height
            steps: Sampling steps
            cfg: CFG scale
            length: Video length in frames
            strength: Strength for I2V
            seed: Random seed (auto-generated if None)
            input_image_path: Path to uploaded input image
            
        Returns:
            Updated workflow dictionary
        """
        try:
            # Create a copy to avoid modifying the original
            import json as json_module
            updated_workflow = json_module.loads(json_module.dumps(workflow))
            
            # Generate random seed if not provided
            if seed is None:
                seed = random.randint(0, 2**32 - 1)
            
            # Update text prompts and parameters
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
            
            self.logger.debug(
                f"Updated video workflow parameters: prompt='{prompt[:50]}...', "
                f"size={width}x{height}, length={length}"
            )
            return updated_workflow
            
        except Exception as e:
            self.logger.error(f"Failed to update video workflow parameters: {e}")
            raise GenerationError(f"Failed to update video workflow parameters: {e}")
    
    async def _download_videos(self, history: Dict[str, Any]) -> Tuple[bytes, str]:
        """
        Download generated video from ComfyUI.
        
        Args:
            history: History response from ComfyUI
            
        Returns:
            Tuple of (video_data, filename)
            
        Raises:
            ComfyUIError: If video download fails
        """
        try:
            outputs = history.get('outputs', {})
            self.logger.info(f"📥 Checking outputs from {len(outputs)} nodes for video files")
            
            # Log all outputs for debugging
            for node_id, node_output in outputs.items():
                output_keys = list(node_output.keys())
                self.logger.info(f"📋 Node {node_id} outputs: {output_keys}")
            
            for node_id, node_output in outputs.items():
                # Check for video files in 'gifs' key (VHS_VideoCombine output)
                if 'gifs' in node_output:
                    self.logger.info(f"🎬 Found video output in node {node_id}")
                    for video_info in node_output['gifs']:
                        video_data = await self._download_video_file(video_info)
                        if video_data:
                            return video_data, video_info['filename']
                
                # Also check for 'videos' key
                if 'videos' in node_output:
                    self.logger.info(f"🎬 Found video output in 'videos' key of node {node_id}")
                    for video_info in node_output['videos']:
                        video_data = await self._download_video_file(video_info)
                        if video_data:
                            return video_data, video_info['filename']
            
            # Log the full outputs structure for debugging
            self.logger.error(f"❌ No video found in any output. Full outputs: {outputs}")
            raise ComfyUIError("No video found in generation output")
            
        except ComfyUIError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to download video: {e}")
            raise ComfyUIError(f"Failed to download video: {e}")
    
    async def _download_video_file(self, video_info: Dict[str, Any]) -> Optional[bytes]:
        """
        Download a single video file from ComfyUI.
        
        Args:
            video_info: Video info dictionary with filename, subfolder, type
            
        Returns:
            Video data bytes, or None if download fails
        """
        filename = video_info['filename']
        subfolder = video_info.get('subfolder', '')
        video_type = video_info.get('type', 'output')
        
        self.logger.info(
            f"📹 Attempting to download video: {filename} "
            f"(subfolder: '{subfolder}', type: {video_type})"
        )
        
        try:
            video_data = await self.client.download_output(
                filename=filename,
                subfolder=subfolder,
                output_type=video_type
            )
            self.logger.info(f"✅ Downloaded video: {filename} ({len(video_data)} bytes)")
            return video_data
        except Exception as e:
            self.logger.error(f"❌ Failed to download video {filename}: {e}")
            return None
    
    async def _load_workflow(self, workflow_name: str) -> Dict[str, Any]:
        """
        Load a video workflow by name.
        
        Args:
            workflow_name: Name of workflow to load
            
        Returns:
            Workflow dictionary
            
        Raises:
            GenerationError: If workflow cannot be loaded
        """
        try:
            workflows_dir = Path(__file__).parent.parent.parent / "workflows"
            workflow_path = workflows_dir / f"{workflow_name}.json"
            
            if not workflow_path.exists():
                # Try to find first available video workflow
                for path in workflows_dir.glob("*video*.json"):
                    workflow_path = path
                    self.logger.warning(
                        f"Workflow '{workflow_name}' not found, using {path.name}"
                    )
                    break
            
            if not workflow_path.exists():
                raise GenerationError(f"No video workflow found for '{workflow_name}'")
            
            with open(workflow_path, 'r') as f:
                return json.load(f)
                
        except Exception as e:
            self.logger.error(f"Failed to load workflow '{workflow_name}': {e}")
            raise GenerationError(f"Failed to load workflow: {e}")
    
    async def _wait_for_completion(
        self,
        prompt_id: str,
        workflow: Dict[str, Any],
        progress_callback=None
    ) -> Dict[str, Any]:
        """
        Wait for video generation to complete with progress tracking.
        
        Args:
            prompt_id: Prompt ID to wait for
            workflow: Workflow dictionary for node counting
            progress_callback: Optional progress callback
            
        Returns:
            History dictionary from ComfyUI
            
        Raises:
            GenerationError: If generation fails
        """
        # Create progress tracker (like ImageGenerator)
        from core.progress.tracker import ProgressTracker
        tracker = ProgressTracker()
        tracker.set_workflow_nodes(workflow)
        
        import asyncio
        start_time = time.time()
        max_wait_time = 1500  # 25 minutes (for concurrent operations)
        check_interval = 1.0
        last_progress_update = 0
        
        self.logger.info(f"⏳ Waiting for video completion: {prompt_id}")
        
        while time.time() - start_time < max_wait_time:
            try:
                history = await self.client.get_history(prompt_id)
                
                if prompt_id in history:
                    prompt_history = history[prompt_id]
                    
                    # Check if completed
                    if 'outputs' in prompt_history and prompt_history['outputs']:
                        self.logger.info(f"✅ Video generation completed (prompt_id: {prompt_id})")
                        
                        # Mark as completed
                        tracker.mark_completed()
                        if progress_callback:
                            try:
                                await progress_callback(tracker)
                            except Exception as e:
                                self.logger.debug(f"Progress callback error: {e}")
                        
                        return prompt_history
                    
                    # Check for errors
                    if 'status' in prompt_history:
                        status = prompt_history['status']
                        if 'error' in status:
                            error_msg = status.get('error', 'Unknown error')
                            raise GenerationError(f"ComfyUI error: {error_msg}")
                
                # Update progress periodically (estimate based on time)
                current_time = time.time()
                if progress_callback and (current_time - last_progress_update >= 5.0):
                    elapsed = current_time - start_time
                    estimated_progress = min(95.0, (elapsed / max_wait_time) * 100)
                    
                    tracker.state.metrics.percentage = estimated_progress
                    tracker.state.phase = f"Generating video... ({int(elapsed)}s)"
                    
                    try:
                        await progress_callback(tracker)
                        last_progress_update = current_time
                    except Exception as e:
                        self.logger.debug(f"Progress callback error: {e}")
                
                # Wait before next poll
                await asyncio.sleep(check_interval)
                    
            except GenerationError:
                raise
            except Exception as e:
                self.logger.error(f"Error polling for completion: {e}")
        
        raise GenerationError(f"Video generation timed out after {int(max_wait_time)}s")
    
    # Backward compatibility method
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
        Generate video (backward compatibility method).
        
        Maintains old interface for existing UI code.
        """
        # Use default workflow if none specified
        if not workflow_name:
            workflow_name = "video_wan_vace_14B_i2v"
        
        # Create new-style request
        request = VideoGenerationRequest(
            prompt=prompt,
            negative_prompt=negative_prompt,
            workflow_name=workflow_name,
            width=width,
            height=height,
            steps=steps,
            cfg=cfg,
            length=length,
            strength=strength,
            seed=seed,
            image_data=input_image_data
        )
        
        # Generate using new method
        result = await self.generate(request, progress_callback)
        
        # Extract video filename from generation_info
        filename = result.generation_info.get('filename', 'output.mp4')
        
        return result.output_data, filename, result.generation_info


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

