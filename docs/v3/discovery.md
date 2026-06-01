# DisComfy v3 - ComfyUI Discovery Report

- **Probed:** 2026-06-01T17:59:54+00:00
- **URL:** `http://172.27.1.165:8188`
- **Reachable:** True

## System

```json
{
  "system": {
    "os": "win32",
    "ram_total": 137191702528,
    "ram_free": 90377162752,
    "comfyui_version": "0.21.0",
    "required_frontend_version": "1.43.18",
    "installed_templates_version": "0.9.73",
    "required_templates_version": "0.9.73",
    "python_version": "3.13.9 | packaged by Anaconda, Inc. | (main, Oct 21 2025, 19:09:58) [MSC v.1929 64 bit (AMD64)]",
    "pytorch_version": "2.12.0+cu132",
    "embedded_python": false,
    "argv": [
      "main.py",
      "--listen",
      "0.0.0.0",
      "--port",
      "8188"
    ]
  },
  "devices": [
    {
      "name": "cuda:0 NVIDIA GeForce RTX 5090 : cudaMallocAsync",
      "type": "cuda",
      "index": 0,
      "vram_total": 34190458880,
      "vram_free": 8903017436,
      "torch_vram_total": 100663296,
      "torch_vram_free": 33113052
    }
  ]
}
```

## Nodes registered: 2471

### By modality bucket (heuristic)

| Bucket | Count |
| --- | ---: |
| `other` | 1974 |
| `video` | 348 |
| `image_t2i` | 44 |
| `image_upscale` | 39 |
| `lora` | 35 |
| `image_edit` | 12 |
| `audio_tts` | 7 |
| `vision` | 7 |
| `audio_music` | 5 |

### Sample nodes per bucket (up to 25)

**`image_t2i`** (25 shown):

- `CLIPTextEncodeHiDream`
- `CRT_KSamplerBatch`
- `CRT_KSamplerBatchAdvanced`
- `ClownGuide_StyleNorm_Advanced_HiDream`
- `ClownsharKSampler`
- `ClownsharKSamplerAutomation`
- `ClownsharKSamplerAutomation_Advanced`
- `ClownsharKSamplerGuide`
- `ClownsharKSamplerGuides`
- `ClownsharKSamplerOptions`
- `ClownsharKSampler_Beta`
- `CrossAttn_EraseReplace_HiDream`
- `EmptyHiDreamO1LatentImage`
- `EmptyLatentImage`
- `EmptyLatentImage64`
- `EmptyLatentImageCustom`
- `EmptyLatentImageCustomPresets`
- `EmptyLatentImagePresets`
- `FluxGuidance`
- `FluxGuidanceDisable`
- `HiDreamO1PatchSeamSmoothing`
- `HiDreamO1ReferenceImages`
- `ImpactKSamplerAdvancedBasicPipe`
- `ImpactKSamplerBasicPipe`
- `KSampler`

**`other`** (25 shown):

- `AMT VFI`
- `APG`
- `APGGuider`
- `ARVideoI2V`
- `ATM VFI`
- `Add Subtitles To Background`
- `Add Subtitles To Frames`
- `AddLabel`
- `AddLatentGuide`
- `AddMask`
- `AddNoise`
- `AddNoiseToTrackPath`
- `AddTextPrefix`
- `AddTextSuffix`
- `AdjustBrightness`
- `AdjustContrast`
- `AdvancedBloomFX`
- `AdvancedNoise`
- `AdvancedStringReplace`
- `AlignYourStepsScheduler`
- `Any Switch (rgthree)`
- `AnyPipeToBasic`
- `AnyTrigger`
- `Anything Everywhere`
- `Anything Everywhere3`

**`image_upscale`** (25 shown):

- `CR Apply Multi Upscale`
- `CR Multi Upscale Stack`
- `CR Upscale Image`
- `CRTAutoDLLTX23LatentUpscaler`
- `CRT_UpscaleModelAdv`
- `HunyuanVideo15LatentUpscaleWithModel`
- `ImageUpscaleWithModel`
- `ImageUpscaleWithModelBatched`
- `IterativeImageUpscale`
- `IterativeLatentUpscale`
- `LatentUpscale`
- `LatentUpscaleBy`
- `LatentUpscaleModelLoader`
- `LatentUpscaleWithVAE`
- `LowVRAMLatentUpscaleModelLoader`
- `MagnificImageUpscalerCreativeNode`
- `MagnificImageUpscalerPreciseV2Node`
- `PixelKSampleUpscalerProvider`
- `PixelKSampleUpscalerProviderPipe`
- `PixelTiledKSampleUpscalerProvider`
- `PixelTiledKSampleUpscalerProviderPipe`
- `PonyUpscaleSamplerWithInjection`
- `RecraftCreativeUpscaleNode`
- `RecraftCrispUpscaleNode`
- `SD_4XUpscale_Conditioning`

**`lora`** (25 shown):

- `AdaptiveLoraScheduler`
- `CR Apply LoRA Stack`
- `CR Cycle LoRAs`
- `CR LoRA List`
- `CR LoRA Stack`
- `CR Load LoRA`
- `CR Load Scheduled LoRAs`
- `CR Random LoRA Stack`
- `CR Random Weight LoRA`
- `CRTAutoDLFlux2KleinHDRILoRA`
- `CreateHookLora`
- `CreateHookLoraModelOnly`
- `CreateHookModelAsLora`
- `CreateHookModelAsLoraModelOnly`
- `DiTBlockLoraLoader`
- `FluxBlockLoraSelect`
- `FluxLoraBlocksPatcher`
- `ImagePrepForICLora`
- `Intrinsic_lora_sampling`
- `LayerColor: ColorAdapter`
- `Lora Loader Stack (rgthree)`
- `LoraExtractKJ`
- `LoraLoader`
- `LoraLoaderBypass`
- `LoraLoaderBypassModelOnly`

**`video`** (25 shown):

- `ApplyRifleXRoPE_WanVideo`
- `CLIPTextEncodeHunyuanDiT`
- `CRTAutoDLLTX23AudioVAE`
- `CRTAutoDLLTX23CLIP`
- `CRTAutoDLLTX23ICLoRA`
- `CRTAutoDLLTX23ICOutpaintLoRA`
- `CRTAutoDLLTX23Model`
- `CRTAutoDLLTX23ModelGGUFQ4`
- `CRTAutoDLLTX23ModelGGUFQ5`
- `CRTAutoDLLTX23ModelNVFP4`
- `CRTAutoDLLTX23VideoVAE`
- `CRT_LTX23AutoDownload`
- `CRT_LTX23USConfig`
- `CRT_LTX23USModelsPipe`
- `CRT_LTX23UnifiedSampler`
- `CRT_WAN_BatchSampler`
- `ClownpileModelWanVideo`
- `CosmosImageToVideoLatent`
- `CosmosPredict2ImageToVideoLatent`
- `DetailerForEachPipeForAnimateDiff`
- `DummyComfyWanModelObject`
- `EmptyCosmosLatentVideo`
- `EmptyHunyuanImageLatent`
- `EmptyHunyuanLatentVideo`
- `EmptyHunyuanVideo15Latent`

**`audio_music`** (5 shown):

- `ConditioningStableAudio`
- `EmptyAceStep1.5LatentAudio`
- `EmptyAceStepLatentAudio`
- `TextEncodeAceStepAudio`
- `TextEncodeAceStepAudio1.5`

**`image_edit`** (12 shown):

- `FluxKontextImageScale`
- `FluxKontextMaxImageNode`
- `FluxKontextMultiReferenceLatentMethod`
- `FluxKontextProImageNode`
- `LayerUtility: FluxKontextImageScale`
- `QwenImageEditScale`
- `QwenImageEditSimpleScale`
- `TextEncodeQwenImageEdit`
- `TextEncodeQwenImageEditAdv`
- `TextEncodeQwenImageEditInfAdv`
- `TextEncodeQwenImageEditPlus`
- `TextEncodeQwenImageEditPlusAdv`

**`audio_tts`** (7 shown):

- `ElevenLabsInstantVoiceClone`
- `FishS2MultiSpeakerSplitTTS`
- `FishS2MultiSpeakerTTS`
- `FishS2TTS`
- `FishS2VoiceCloneTTS`
- `KugelAudioTTSNode`
- `KugelAudioVoiceCloneNode`

**`vision`** (7 shown):

- `AILab_QwenVL`
- `AILab_QwenVL_Advanced`
- `AILab_QwenVL_GGUF`
- `AILab_QwenVL_GGUF_Advanced`
- `AILab_QwenVL_GGUF_PromptEnhancer`
- `AILab_QwenVL_PromptEnhancer`
- `TextImageEncodeQwenVL`

### Top python_modules (custom node packs)

| python_module | nodes |
| --- | ---: |
| `custom_nodes.RES4LYF` | 294 |
| `custom_nodes.comfyui-kjnodes` | 235 |
| `custom_nodes.ComfyUI_Comfyroll_CustomNodes` | 199 |
| `custom_nodes.ComfyUI-Impact-Pack` | 197 |
| `custom_nodes.comfyui_layerstyle` | 169 |
| `custom_nodes.ComfyUI-WanVideoWrapper` | 146 |
| `custom_nodes.crt-nodes` | 135 |
| `custom_nodes.ComfyUI-LTXVideo` | 76 |
| `nodes` | 64 |
| `custom_nodes.comfyui_essentials` | 62 |
| `custom_nodes.ComfyMath` | 53 |
| `custom_nodes.comfyui-videohelpersuite` | 40 |
| `comfy_extras.nodes_custom_sampler` | 35 |
| `comfy_extras.nodes_dataset` | 28 |
| `comfy_api_nodes.nodes_kling` | 25 |
| `custom_nodes.rgthree-comfy` | 24 |
| `custom_nodes.comfyui-post-processing-nodes` | 23 |
| `comfy_extras.nodes_hooks` | 20 |
| `comfy_extras.nodes_audio` | 19 |
| `comfy_api_nodes.nodes_recraft` | 18 |
| `custom_nodes.ComfyUI-Chibi-Nodes` | 18 |
| `comfy_extras.nodes_images` | 17 |
| `comfy_extras.nodes_wan` | 17 |
| `custom_nodes.comfyui-frame-interpolation` | 16 |
| `comfy_extras.nodes_model_merging_model_specific` | 15 |
| `comfy_extras.nodes_latent` | 14 |
| `comfy_api_nodes.nodes_wan` | 14 |
| `comfy_extras.nodes_mask` | 13 |
| `comfy_api_nodes.nodes_vidu` | 13 |
| `custom_nodes.comfyui-custom-scripts` | 13 |
| `custom_nodes.gguf` | 13 |
| `comfy_extras.nodes_lt` | 12 |
| `comfy_extras.nodes_string` | 12 |
| `comfy_api_nodes.nodes_bytedance` | 12 |
| `comfy_extras.nodes_model_merging` | 11 |
| `comfy_extras.nodes_hunyuan` | 11 |
| `comfy_extras.nodes_post_processing` | 10 |
| `comfy_extras.nodes_model_advanced` | 10 |
| `comfy_extras.nodes_flux` | 8 |
| `comfy_api_nodes.nodes_bfl` | 8 |

### Samplers / schedulers (KSampler)

- samplers: ['euler', 'euler_cfg_pp', 'euler_ancestral', 'euler_ancestral_cfg_pp', 'heun', 'heunpp2', 'exp_heun_2_x0', 'exp_heun_2_x0_sde', 'dpm_2', 'dpm_2_ancestral', 'lms', 'dpm_fast', 'dpm_adaptive', 'dpmpp_2s_ancestral', 'dpmpp_2s_ancestral_cfg_pp', 'dpmpp_sde', 'dpmpp_sde_gpu', 'dpmpp_2m', 'dpmpp_2m_cfg_pp', 'dpmpp_2m_sde', 'dpmpp_2m_sde_gpu', 'dpmpp_2m_sde_heun', 'dpmpp_2m_sde_heun_gpu', 'dpmpp_3m_sde', 'dpmpp_3m_sde_gpu', 'ddpm', 'lcm', 'ipndm', 'ipndm_v', 'deis', 'res_multistep', 'res_multistep_cfg_pp', 'res_multistep_ancestral', 'res_multistep_ancestral_cfg_pp', 'gradient_estimation', 'gradient_estimation_cfg_pp', 'er_sde', 'seeds_2', 'seeds_3', 'sa_solver', 'sa_solver_pece', 'ddim', 'uni_pc', 'uni_pc_bh2', 'legacy_rk', 'rk', 'rk_beta', 'deis_3m_ode', 'deis_2m_ode', 'deis_3m', 'deis_2m', 'res_6s_ode', 'res_5s_ode', 'res_3s_ode', 'res_2s_ode', 'res_3m_ode', 'res_2m_ode', 'res_6s', 'res_5s', 'res_3s', 'res_2s', 'res_3m', 'res_2m']
- schedulers: ['simple', 'sgm_uniform', 'karras', 'exponential', 'ddim_uniform', 'beta', 'normal', 'linear_quadratic', 'kl_optimal', 'bong_tangent', 'beta57']

### Checkpoints (1)

- `ltx-2.3-22b-dev-fp8.safetensors`

### LoRAs (16)

- `Klein-consistency.safetensors`
- `QWEN_EDIT_ACTION_V1.safetensors`
- `Qwen-Image-2512-Lightning-4steps-V1.0-fp32.safetensors`
- `Qwen-Image-Edit-2511-Lightning-4steps-V1.0-bf16.safetensors`
- `SVI_v2_PRO_Wan2.2-I2V-A14B_HIGH_lora_rank_128_fp16.safetensors`
- `SVI_v2_PRO_Wan2.2-I2V-A14B_LOW_lora_rank_128_fp16.safetensors`
- `f2k_consist_20260225.safetensors`
- `gemma-3-12b-it-abliterated_lora_rank64_bf16.safetensors`
- `ltx-2.3-22b-distilled-lora-384.safetensors`
- `qwen_image_2512_4l3x_lora_v1.safetensors`
- `qwen_image_2512_ch4nt4l_lora_v1.safetensors`
- `qwen_image_2512_j0k3_lora_v1.safetensors`
- `qwen_image_2512_j4m13_lora_v1.safetensors`
- `qwen_image_2512_r4mj4d_lora_v1.safetensors`
- `qwen_image_2512_rutg3r_lora_v1.safetensors`
- `qwen_image_2512_wypk3_lora_v1.safetensors`

## v3 viability per modality (preliminary)

Read the bucket counts above. Heuristics:

- **image_t2i** present if `KSampler` + a Flux/HiDream/Qwen sampler/loader exist.
- **image_edit** present if `Kontext` or `QwenImageEdit` nodes exist.
- **image_upscale** present if any `Upscale`/`RealESRGAN`/`UltimateSDUpscale` exist.
- **video** present if `VHS_` (Video Helper Suite) or `Wan/Hunyuan/LTX/VACE/Mochi` exist.
- **audio_tts** present if `F5TTS`/`ChatterboxTTS`/`TTS` nodes exist.
- **audio_music** present if `ACE_Step`/`StableAudio`/`MusicGen` nodes exist.

If a target modality is missing, ADR-007 must propose either
a) installing the required custom node pack on the ComfyUI server, or
b) deferring that modality to a later v3.x.

_Generated by `scripts/discover_comfyui.py` at 2026-06-01T17:59:54+00:00._
