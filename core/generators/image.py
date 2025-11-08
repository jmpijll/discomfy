"""
Image generation using ComfyUI with v2.0 architecture.

Refactored to use:
- ComfyUIClient for HTTP requests
- WorkflowManager for workflow loading
- WorkflowUpdater for parameter updates
- ProgressTracker for progress tracking
- BaseGenerator for common functionality
"""

import asyncio
import logging
import time
import random
from typing import Dict, Any, List, Optional, Tuple, Callable

from core.generators.base import (
    BaseGenerator, GeneratorType, GenerationRequest, GenerationResult,
    UpscaleGenerationRequest, EditGenerationRequest
)
from core.comfyui.client import ComfyUIClient
from core.comfyui.websocket import ComfyUIWebSocket
from core.comfyui.workflows.manager import WorkflowManager
from core.comfyui.workflows.updater import WorkflowUpdater, WorkflowParameters
from core.progress.tracker import ProgressTracker, ProgressStatus
from core.exceptions import ComfyUIError, WorkflowError, GenerationError
from core.validators.image import PromptParameters, ValidationError as ValidatorError


class ImageGenerationRequest(GenerationRequest):
    """Extended request for image generation."""
    negative_prompt: str = ""
    width: int = 1024
    height: int = 1024
    steps: int = 50
    cfg: float = 5.0
    batch_size: int = 1
    lora_name: Optional[str] = None
    lora_strength: float = 1.0
    dype_exponent: Optional[float] = None


class ImageGenerator(BaseGenerator):
    """Image generator using ComfyUI with v2.0 architecture."""
    
    def __init__(self, comfyui_client: ComfyUIClient, config):
        """
        Initialize image generator.
        
        Args:
            comfyui_client: ComfyUI client instance
            config: Bot configuration
        """
        super().__init__(comfyui_client, config)
        self.workflow_manager = WorkflowManager()
        self.workflow_updater = WorkflowUpdater()
        self._queue_lock = asyncio.Lock()
        
        # WebSocket for real-time progress tracking (v1.4.0 implementation)
        self.websocket = ComfyUIWebSocket(config.comfyui.url, comfyui_client.client_id)
        self._active_generations: Dict[str, dict] = {}
        
        # Backward compatibility properties for video_gen
        self._session_lock = asyncio.Lock()
        self._bot_client_id = comfyui_client.client_id
        self._persistent_websocket = None
        self._websocket_task = None
        self._websocket_connected = False
        self._websocket_lock = asyncio.Lock()
    
    async def initialize(self):
        """Initialize the image generator (call once at bot startup)."""
        self.logger.info("🎨 Initializing ImageGenerator with WebSocket support...")
        
        # Start WebSocket connection for real-time progress
        await self.websocket.connect()
        
        self.logger.info("✅ ImageGenerator initialized successfully")
    
    async def shutdown(self):
        """Shutdown the image generator (call once at bot shutdown)."""
        self.logger.info("🛑 Shutting down ImageGenerator...")
        
        # Disconnect WebSocket
        await self.websocket.disconnect()
        
        self.logger.info("✅ ImageGenerator shutdown complete")
    
    @property
    def session(self):
        """Backward compatibility: expose ComfyUI client session."""
        return self.client.session if self.client else None
    
    @property
    def base_url(self):
        """Backward compatibility: expose base URL."""
        return self.client.base_url if self.client else None
    
    async def test_connection(self) -> bool:
        """Backward compatibility: test connection to ComfyUI server."""
        try:
            if not self.client:
                self.logger.error("ComfyUI client not initialized")
                return False
            return await self.client.test_connection()
        except Exception as e:
            self.logger.error(f"Failed to test connection: {e}")
            return False
    
    async def get_available_loras(self) -> List[Dict[str, str]]:
        """Backward compatibility: get list of available LoRAs from ComfyUI."""
        try:
            if not self.client or not self.client.session:
                self.logger.error("Session not initialized")
                return []
            
            async with self.client.session.get(f"{self.client.base_url}/object_info/LoraLoaderModelOnly") as response:
                if response.status == 200:
                    object_info = await response.json()
                    lora_list = object_info.get("LoraLoaderModelOnly", {}).get("input", {}).get("required", {}).get("lora_name", [])
                    
                    if isinstance(lora_list, list) and len(lora_list) > 0:
                        lora_names = lora_list[0] if isinstance(lora_list[0], list) else lora_list
                        
                        loras = []
                        for lora_name in lora_names:
                            if isinstance(lora_name, str):
                                loras.append({
                                    'filename': lora_name,
                                    'display_name': lora_name.replace('.safetensors', '').replace('_', ' ').title(),
                                })
                        return loras
            
            return []
        except Exception as e:
            self.logger.error(f"Error fetching LoRAs: {e}")
            return []
    
    async def generate_qwen_edit(self, *args, **kwargs):
        """Backward compatibility: Qwen edit is now handled through generate method."""
        raise NotImplementedError(
            "Use generate() method with appropriate workflow instead. "
            "This is handled through the new v2.0 architecture."
        )
    
    def filter_loras_by_model(self, loras: List[Dict[str, str]], model_type: str) -> List[Dict[str, str]]:
        """Backward compatibility: filter LoRAs based on the selected model type."""
        try:
            original_count = len(loras)

            # First, exclude WAN LoRAs (used for video animation workflows)
            loras = [lora for lora in loras if 'wan' not in lora['filename'].lower()]

            if model_type.lower() == 'hidream':
                # Only include LoRAs with 'hidream' in the name
                filtered = [lora for lora in loras if 'hidream' in lora['filename'].lower()]
            elif model_type.lower() in ['flux', 'flux_krea', 'dype_flux_krea']:
                # Include LoRAs that don't have 'hidream' in the name
                filtered = [lora for lora in loras if 'hidream' not in lora['filename'].lower()]

                # Fallback: if no flux-specific LoRAs found, allow all LoRAs
                if not filtered and loras:
                    self.logger.warning(f"No flux-specific LoRAs found, allowing all {len(loras)} LoRAs for flux models")
                    filtered = loras
            else:
                # Unknown model type, return all (minus WAN)
                filtered = loras

            self.logger.debug(f"Filtered {len(filtered)}/{original_count} LoRAs for model type '{model_type}' (excluded WAN LoRAs)")
            return filtered

        except Exception as e:
            self.logger.error(f"Failed to filter LoRAs: {e}")
            return loras
    
    @property
    def generator_type(self) -> GeneratorType:
        """Get generator type."""
        return GeneratorType.IMAGE
    
    def validate_request(self, request: GenerationRequest) -> bool:
        """
        Validate generation request.
        
        Args:
            request: Request to validate
            
        Returns:
            True if valid
            
        Raises:
            ValidatorError: If validation fails
        """
        if not isinstance(request, ImageGenerationRequest):
            raise ValidatorError("Invalid request type")
        
        # Validate prompt using Pydantic
        try:
            PromptParameters(prompt=request.prompt)
        except Exception as e:
            raise ValidatorError(f"Invalid prompt: {e}")
        
        # Validate batch size
        if request.batch_size > self.config.generation.max_batch_size:
            raise ValidatorError(
                f"Batch size too large (max {self.config.generation.max_batch_size})"
            )
        
        # Validate prompt length
        if len(request.prompt) > self.config.security.max_prompt_length:
            raise ValidatorError(
                f"Prompt too long (max {self.config.security.max_prompt_length} characters)"
            )
        
        return True
    
    async def generate(self, request: GenerationRequest) -> GenerationResult:
        """
        Generate images from request.
        
        Handles ImageGenerationRequest, UpscaleGenerationRequest, and EditGenerationRequest.
        
        Args:
            request: Generation request (Image, Upscale, or Edit)
            
        Returns:
            Generation result with images
        """
        # Route to appropriate handler based on request type
        if isinstance(request, UpscaleGenerationRequest):
            return await self._generate_upscale(request)
        elif isinstance(request, EditGenerationRequest):
            return await self._generate_edit(request)
        elif isinstance(request, ImageGenerationRequest):
            # Validate request
            self.validate_request(request)
            return await self._generate_image(request)
        else:
            raise GenerationError(f"Invalid request type: {type(request).__name__}")
    
    async def _generate_image(self, request: ImageGenerationRequest) -> GenerationResult:
        """Generate images using standard workflow."""
        # Use default workflow if none specified
        workflow_name = request.workflow_name or self.config.generation.default_workflow
        
        self.logger.info(f"Starting image generation: '{request.prompt[:50]}...'")
        
        try:
            # Load workflow
            workflow = self.workflow_manager.load_workflow(
                self.config.workflows[workflow_name].file
            )
            
            # Create workflow parameters
            workflow_params = WorkflowParameters(
                prompt=request.prompt,
                negative_prompt=request.negative_prompt,
                width=request.width,
                height=request.height,
                steps=request.steps,
                cfg=request.cfg,
                seed=request.seed,
                batch_size=request.batch_size,
                lora_name=request.lora_name,
                lora_strength=request.lora_strength,
                dype_exponent=request.dype_exponent
            )
            
            # Update workflow
            updated_workflow = self.workflow_updater.update_workflow(workflow, workflow_params)
            
            # Queue prompt
            prompt_id = await self.client.queue_prompt(updated_workflow)
            
            # Wait for completion and download images
            history = await self._wait_for_completion(
                prompt_id,
                updated_workflow,
                request.progress_callback
            )
            
            # Download images
            images = await self._download_images(history)
            
            # Create result
            generation_info = {
                'prompt_id': prompt_id,
                'prompt': request.prompt,
                'workflow': workflow_name,
                'width': request.width,
                'height': request.height,
                'steps': request.steps,
                'seed': workflow_params.seed,
                'num_images': len(images),
                'timestamp': time.time()
            }
            
            # For multiple images, combine into single result
            # (Discord expects single file or list of files)
            if len(images) > 1:
                # Use first image as primary output
                output_data = images[0]
                generation_info['additional_images'] = images[1:]
            else:
                output_data = images[0] if images else b''
            
            return GenerationResult(
                output_data=output_data,
                generation_info=generation_info,
                generation_type=self.generator_type
            )
            
        except Exception as e:
            self.logger.error(f"Image generation failed: {e}")
            raise GenerationError(f"Image generation failed: {e}")
    
    async def _generate_upscale(self, request: UpscaleGenerationRequest) -> GenerationResult:
        """Generate upscaled image."""
        try:
            # Upload image to ComfyUI
            upload_filename = f"upscale_input_{int(time.time())}.png"
            uploaded_filename = await self.client.upload_image(request.input_image_data, upload_filename)
            
            self.logger.info(f"Starting upscale: {uploaded_filename} (factor: {request.upscale_factor}x)")
            
            # Load workflow
            workflow = self.workflow_manager.load_workflow(f"{request.workflow_name}.json")
            
            # Update workflow nodes manually (upscale workflows need special handling)
            seed_value = request.seed if request.seed is not None else random.randint(0, 2**32 - 1)
            
            for node_id, node in workflow.items():
                if node.get('class_type') == 'LoadImage':
                    node['inputs']['image'] = uploaded_filename
                elif node.get('class_type') in ['KSampler', 'KSamplerAdvanced']:
                    node['inputs']['seed'] = seed_value
                    node['inputs']['steps'] = request.steps
                    node['inputs']['cfg'] = request.cfg
                    if 'denoise' in node['inputs']:
                        node['inputs']['denoise'] = request.denoise
            
            # Queue and wait
            prompt_id = await self.client.queue_prompt(workflow)
            history = await self._wait_for_completion(prompt_id, workflow, request.progress_callback)
            
            # Download result
            images = await self._download_images(history)
            upscaled_data = images[0] if images else b''
            
            # Create result
            generation_info = {
                'prompt_id': prompt_id,
                'input_image': uploaded_filename,
                'upscale_factor': request.upscale_factor,
                'denoise': request.denoise,
                'steps': request.steps,
                'cfg': request.cfg,
                'seed': seed_value,
                'workflow': request.workflow_name,
                'timestamp': time.time(),
                'type': 'upscale'
            }
            
            return GenerationResult(
                output_data=upscaled_data,
                generation_info=generation_info,
                generation_type=GeneratorType.UPSCALE
            )
            
        except Exception as e:
            self.logger.error(f"Upscale failed: {e}")
            raise GenerationError(f"Upscale failed: {e}")
    
    async def _generate_edit(self, request: EditGenerationRequest) -> GenerationResult:
        """Generate edited image."""
        try:
            # Upload primary image
            upload_filename = f"edit_input_{int(time.time())}.png"
            uploaded_filename = await self.client.upload_image(request.input_image_data, upload_filename)
            
            # Upload additional images for Qwen if provided
            uploaded_additional = []
            if request.additional_images:
                for idx, img_data in enumerate(request.additional_images):
                    additional_filename = f"edit_input_{int(time.time())}_{idx+2}.png"
                    uploaded = await self.client.upload_image(img_data, additional_filename)
                    uploaded_additional.append(uploaded)
                    await asyncio.sleep(0.1)
            
            # Select workflow
            if request.workflow_type.lower() == "qwen":
                total_images = 1 + len(uploaded_additional)
                if total_images == 1:
                    workflow_name = "qwen_image_edit"
                elif total_images == 2:
                    workflow_name = "qwen_image_edit_2"
                elif total_images == 3:
                    workflow_name = "qwen_image_edit_3"
                else:
                    raise ValueError(f"Qwen supports 1-3 images, got {total_images}")
            else:
                workflow_name = "flux_kontext_edit"
            
            self.logger.info(f"Starting {request.workflow_type} edit: {request.edit_prompt[:50]}...")
            
            # Load workflow
            workflow = self.workflow_manager.load_workflow(f"{workflow_name}.json")
            
            # Update workflow nodes manually (following main branch pattern)
            seed_value = request.seed if request.seed is not None else random.randint(0, 2**32 - 1)
            
            # Collect LoadImage nodes for multi-image assignment (Qwen)
            load_image_nodes = []
            for node_id, node in workflow.items():
                if node.get('class_type') == 'LoadImage':
                    load_image_nodes.append((node_id, node))
            load_image_nodes.sort(key=lambda x: int(x[0]))
            
            for node_id, node in workflow.items():
                class_type = node.get('class_type')
                
                if class_type == 'LoadImage':
                    # Assign images based on node order (for Qwen multi-image)
                    node_index = next((i for i, (nid, _) in enumerate(load_image_nodes) if nid == node_id), 0)
                    
                    if node_index == 0:
                        node['inputs']['image'] = uploaded_filename
                    elif uploaded_additional and node_index - 1 < len(uploaded_additional):
                        node['inputs']['image'] = uploaded_additional[node_index - 1]
                
                elif class_type == 'CLIPTextEncode':
                    # Check title to find positive prompt node (Flux Kontext)
                    title = node.get('_meta', {}).get('title', '')
                    if 'Positive' in title:
                        node['inputs']['text'] = request.edit_prompt
                
                elif class_type == 'TextEncodeQwenImageEditPlus':
                    # Qwen edit prompt node - check if it's the positive prompt node
                    prompt_value = node['inputs'].get('prompt', '')
                    if prompt_value and prompt_value.strip():
                        node['inputs']['prompt'] = request.edit_prompt
                
                elif class_type == 'RandomNoise':
                    # Flux seed
                    node['inputs']['noise_seed'] = seed_value
                
                elif class_type == 'BasicScheduler':
                    # Flux steps
                    node['inputs']['steps'] = request.steps
                
                elif class_type == 'FluxGuidance':
                    # Flux CFG/guidance
                    node['inputs']['guidance'] = request.cfg
                
                elif class_type == 'EmptySD3LatentImage':
                    # Flux dimensions
                    node['inputs']['width'] = request.width
                    node['inputs']['height'] = request.height
                
                elif class_type == 'KSampler':
                    # Qwen sampling parameters
                    node['inputs']['seed'] = seed_value
                    node['inputs']['steps'] = request.steps
                    node['inputs']['cfg'] = request.cfg
            
            # Queue and wait
            prompt_id = await self.client.queue_prompt(workflow)
            history = await self._wait_for_completion(prompt_id, workflow, request.progress_callback)
            
            # Download result
            images = await self._download_images(history)
            edited_data = images[0] if images else b''
            
            # Create result
            generation_info = {
                'prompt_id': prompt_id,
                'input_image': uploaded_filename,
                'edit_prompt': request.edit_prompt,
                'workflow_type': request.workflow_type,
                'width': request.width,
                'height': request.height,
                'steps': request.steps,
                'cfg': request.cfg,
                'seed': seed_value,
                'workflow': workflow_name,
                'timestamp': time.time(),
                'type': 'edit'
            }
            
            return GenerationResult(
                output_data=edited_data,
                generation_info=generation_info,
                generation_type=GeneratorType.EDIT
            )
            
        except Exception as e:
            self.logger.error(f"Edit failed: {e}")
            raise GenerationError(f"Edit failed: {e}")
    
    async def _wait_for_completion(
        self,
        prompt_id: str,
        workflow: Dict[str, Any],
        progress_callback: Optional[Callable] = None
    ) -> Dict[str, Any]:
        """
        Wait for generation to complete with WebSocket progress tracking.
        
        Args:
            prompt_id: Prompt ID to wait for
            workflow: Workflow dictionary
            progress_callback: Optional progress callback
            
        Returns:
            History dictionary from ComfyUI
        """
        # Create progress tracker
        tracker = ProgressTracker()
        tracker.set_workflow_nodes(workflow)
        
        # Register with WebSocket for real-time progress
        ws_progress_data = await self.websocket.register_generation(prompt_id)
        
        start_time = time.time()
        max_wait_time = 1500  # 25 minutes (for concurrent operations)
        check_interval = 1.0
        last_progress_update = 0
        
        self.logger.info(f"Waiting for completion of prompt {prompt_id} (WebSocket: {self.websocket.connected}, Callback: {progress_callback is not None})")
        
        while time.time() - start_time < max_wait_time:
            # Check history for completion
            try:
                history_data = await self.client.get_history(prompt_id)
                
                if history_data and prompt_id in history_data:
                    prompt_data = history_data[prompt_id]
                    if isinstance(prompt_data, dict) and 'outputs' in prompt_data:
                        # Completed!
                        tracker.mark_completed()
                        
                        # Unregister from WebSocket tracking
                        await self.websocket.unregister_generation(prompt_id)
                        
                        self.logger.info(f"Generation completed: {prompt_id}")
                        return prompt_data
                        
            except ComfyUIError:
                # Not completed yet, continue waiting
                pass
            except Exception as e:
                self.logger.debug(f"History check error: {e}")
            
            # Update progress using WebSocket data or fallback to time-based
            try:
                # Get real-time progress from WebSocket
                ws_data = self.websocket.get_generation_data(prompt_id)
                current_time = time.time()
                
                if ws_data:
                    step_current = ws_data.get('step_current', 0)
                    step_total = ws_data.get('step_total', 0)
                    
                    # Update progress using real steps from WebSocket
                    if step_total > 0 and step_current > 0:
                        # Mark as running if not already
                        if tracker.state.status != ProgressStatus.RUNNING:
                            tracker.update_execution_start()
                        
                        # Update with real step progress
                        tracker.update_step_progress(step_current, step_total)
                        self.logger.info(f"📊 WebSocket progress: {step_current}/{step_total} ({tracker.state.metrics.percentage:.1f}%)")
                    else:
                        # No step data yet, use time-based
                        elapsed = current_time - start_time
                        tracker.state.metrics.percentage = min(30, (elapsed / 60) * 100)
                        tracker.state.phase = "Initializing..."
                else:
                    # No WebSocket data, fallback to time-based progress
                    elapsed = current_time - start_time
                    tracker.state.metrics.percentage = min(50, (elapsed / 60) * 100)
                    tracker.state.phase = "Generating..."
                
                # Call progress callback periodically (every 1 second for responsive updates)
                time_since_last = current_time - last_progress_update
                self.logger.debug(f"Check callback: callback={progress_callback is not None}, time_since={time_since_last:.2f}s")
                if progress_callback and (current_time - last_progress_update) >= 1.0:
                    try:
                        self.logger.info(f"📊 Calling progress callback: {tracker.state.metrics.percentage:.1f}% - {tracker.state.phase}")
                        await progress_callback(tracker)
                        last_progress_update = current_time
                    except Exception as cb_error:
                        self.logger.error(f"Progress callback error: {cb_error}", exc_info=True)
                        
            except Exception as e:
                self.logger.debug(f"Progress update error: {e}")
            
            await asyncio.sleep(check_interval)
        
        # Timeout
        raise GenerationError(f"Generation timeout after {max_wait_time} seconds")
    
    async def _download_images(self, history: Dict[str, Any]) -> List[bytes]:
        """
        Download generated images from ComfyUI.
        
        Args:
            history: History dictionary from ComfyUI
            
        Returns:
            List of image data as bytes
        """
        images = []
        
        outputs = history.get('outputs', {})
        if not outputs:
            raise GenerationError("No outputs found in generation result")
        
        for node_id, node_output in outputs.items():
            if not isinstance(node_output, dict):
                continue
                
            node_images = node_output.get('images', [])
            if not isinstance(node_images, list):
                continue
            
            for image_info in node_images:
                if not isinstance(image_info, dict):
                    continue
                
                filename = image_info.get('filename')
                if not filename:
                    continue
                
                subfolder = image_info.get('subfolder', '')
                image_type = image_info.get('type', 'output')
                
                try:
                    image_data = await self.client.download_output(
                        filename=filename,
                        subfolder=subfolder,
                        output_type=image_type
                    )
                    
                    if image_data:
                        images.append(image_data)
                        self.logger.debug(f"Downloaded image: {filename}")
                        
                except Exception as e:
                    self.logger.error(f"Error downloading image {filename}: {e}")
                    continue
        
        if not images:
            raise GenerationError("No images found in generation output")
        
        self.logger.info(f"Downloaded {len(images)} images")
        return images
    
    # Backward compatibility method
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
        dype_exponent: Optional[float] = None,
        progress_callback=None
    ) -> Tuple[List[bytes], Dict[str, Any]]:
        """
        Generate images (backward compatibility method).

        Maintains old interface for existing bot code.
        """
        # Use default workflow if none specified
        if not workflow_name:
            workflow_name = self.config.generation.default_workflow

        # Create new-style request
        request = ImageGenerationRequest(
            prompt=prompt,
            workflow_name=workflow_name,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            steps=steps,
            cfg=cfg,
            seed=seed,
            batch_size=batch_size,
            lora_name=lora_name,
            lora_strength=lora_strength,
            dype_exponent=dype_exponent,
            progress_callback=progress_callback
        )
        
        # Generate using new method
        result = await self.generate(request)
        
        # Convert to old format
        images = [result.output_data]
        if 'additional_images' in result.generation_info:
            images.extend(result.generation_info['additional_images'])
        
        return images, result.generation_info

