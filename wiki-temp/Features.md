# DisComfy Features

Complete guide to all features in DisComfy v2.0.

---

## 🎨 AI Image Generation

### Overview
Generate stunning AI images using advanced ComfyUI workflows directly from Discord.

### Supported Models
- **Flux** - High-quality general purpose model
- **Flux Krea** - Enhanced Flux model with improved quality
- **HiDream** - Alternative generation model

### Parameters

| Parameter | Description | Range | Default |
|-----------|-------------|-------|---------|
| `prompt` | Your text description | 1-500 chars | Required |
| `width` | Image width | 256-2048 | 1024 |
| `height` | Image height | 256-2048 | 1024 |
| `steps` | Sampling steps | 1-50 | 30 |
| `cfg` | CFG scale | 1.0-20.0 | 7.5 |
| `seed` | Random seed | -1 or 0+ | -1 (random) |
| `batch_size` | Number of images | 1-4 | 1 |
| `lora` | LoRA model name | - | None |
| `lora_strength` | LoRA strength | 0.0-2.0 | 1.0 |

### Usage

**Basic:**
```
/generate prompt:a majestic dragon soaring through clouds
```

**With Parameters:**
```
/generate prompt:cyberpunk cityscape at night width:1024 height:768 steps:30 cfg:7.5 batch_size:2
```

**With LoRA:**
```
/generate prompt:anime character in magical forest lora:anime_style_v2 lora_strength:0.8
```

### Interactive Setup
When you run `/generate`, you'll see an interactive setup view:
1. **Select Model** - Choose between Flux, Flux Krea, or HiDream
2. **Select LoRA** - Pick from available LoRAs (organized by model)
3. **Adjust Settings** - Fine-tune parameters via modal
4. **Generate** - Click to start generation

---

## ✏️ Image Editing

DisComfy supports two AI editing models with different strengths.

### Flux Kontext Editing

**Use Case:** High-quality detailed editing  
**Speed:** 1-3 minutes  
**Command:** `/editflux`

**Features:**
- High-quality results
- Detailed edits
- Better for complex changes
- 10-50 sampling steps

**Usage:**
```
/editflux image:<upload> prompt:add sunglasses and a hat steps:25
```

### Qwen 2.5 VL Editing

**Use Case:** Ultra-fast editing and iteration  
**Speed:** 30-60 seconds  
**Command:** `/editqwen`

**Features:**
- Lightning-fast results
- Good quality
- Perfect for rapid iteration
- 4-20 sampling steps

**Usage:**
```
/editqwen image:<upload> prompt:change the background to mountains steps:8
```

### Parameters

| Parameter | Description | Range |
|-----------|-------------|-------|
| `image` | Image to edit | Required (upload) |
| `prompt` | Edit description | Required |
| `steps` | Sampling steps | 4-20 (Qwen), 10-50 (Flux) |

### Post-Generation Editing

Every generated image has two edit buttons:
- **✏️ Flux Edit** - High-quality editing
- **⚡ Qwen Edit** - Ultra-fast editing

Anyone can click these buttons to edit any image!

---

## 🔍 Image Upscaling

### Overview
Upscale images using AI super-resolution for incredible detail enhancement.

### Upscale Ratios
- **2x** - Quick upscale (512→1024)
- **4x** - Standard upscale (512→2048)
- **8x** - Maximum upscale (512→4096)

### Parameters

| Parameter | Description | Range | Default |
|-----------|-------------|-------|---------|
| Upscale Ratio | Magnification | 2x, 4x, 8x | 4x |
| Denoise Strength | Detail enhancement | 0.1-1.0 | 0.5 |
| Sampling Steps | Quality control | 10-50 | 20 |

### Usage

**Via Button:**
1. Generate or upload an image
2. Click **🔍 Upscale** button
3. Select parameters in modal
4. Confirm to start upscaling

**Automatic Features:**
- Original prompt automatically preserved
- Smart parameter defaults
- Real-time progress tracking

---

## 🎬 Video Generation

### Overview
Convert images to smooth, high-quality MP4 animations.

### Frame Counts
- **81 frames** - ~2 seconds (quick animation)
- **121 frames** - ~3 seconds (standard)
- **161 frames** - ~5 seconds (longer animation)

### Parameters

| Parameter | Description | Range | Default |
|-----------|-------------|-------|---------|
| Frame Count | Video length | 81, 121, 161 | 121 |
| Strength | Animation intensity | 0.1-1.0 | 0.7 |
| Steps | Quality | 10-50 | 25 |
| Animation Prompt | Motion description | - | Original prompt |

### Usage

**Via Button:**
1. Generate or upload an image
2. Click **🎬 Animate** button
3. Customize animation settings
4. Confirm to start video generation

**Custom Animation Prompts:**
Modify how your image animates with natural language:
- "slowly pan across the scene"
- "camera zooms in dramatically"
- "gentle rotation and zoom"
- "dynamic movement with parallax"

### Features
- Original prompt pre-filled (editable)
- Extended 15-minute timeout
- Real-time progress tracking
- High-quality MP4 output

---

## 📊 Real-Time Progress Tracking

### Overview
DisComfy provides detailed, accurate progress information using WebSocket integration with ComfyUI.

### Progress Display

```
🎬 Generating Video
📊 87.5% ████████████████████░░░
🔄 Sampling (315/321)
⏱️ Elapsed: 4m 32s | ETA: 42s
🎯 Node: WanVaceToVideo
Settings: 720x720 | 161 frames | Strength: 0.7
```

### Features

- **Step-Based Accuracy** - Progress calculated from actual sampling steps
- **WebSocket Integration** - Real-time updates directly from ComfyUI
- **Queue Monitoring** - Live updates when waiting in queue
- **Node Tracking** - See which ComfyUI node is executing
- **Time Estimates** - Elapsed time and ETA
- **Multi-Phase Support** - Handles complex workflows
- **Automatic Fallback** - HTTP polling when WebSocket unavailable

### Queue Status

When ComfyUI is busy:
```
⏳ Queued - Position #2 in queue
🔄 Other generations ahead: 1
⏱️ Elapsed: 15s
```

---

## ⚙️ Interactive User Experience

### Universal Button Access

**Key Feature:** Anyone can use action buttons on ANY generation!

Available buttons on every generated image:
- **🔍 Upscale** - AI upscaling
- **✏️ Flux Edit** - High-quality editing
- **⚡ Qwen Edit** - Ultra-fast editing
- **🎬 Animate** - Video generation
- **🔄 Variations** - Generate variations (if available)

### Parameter Selection Modals

Interactive Discord modals for parameter customization:

**Upscale Modal:**
- Upscale ratio dropdown
- Denoise strength input
- Sampling steps input
- Pre-filled defaults

**Video Modal:**
- Frame count selection
- Animation strength
- Quality settings
- Animation prompt editing

**Edit Modal:**
- Edit prompt input
- Sampling steps
- Model-specific ranges
- Validation

### Features

- **Infinite Usage** - Buttons never expire
- **Pre-filled Defaults** - Sensible starting values
- **Input Validation** - Prevents errors
- **Smart Descriptions** - Parameter help text
- **Prompt Preservation** - Original prompts auto-filled

---

## 🛡️ Production-Ready Features

### Rate Limiting

Smart rate limiting prevents abuse while allowing normal usage:

- **Per-User Limits** - Configurable requests per minute
- **Global Limits** - Server-wide protection
- **Sliding Window** - Fair distribution
- **Informative Messages** - Clear rate limit feedback

### File Management

Automatic cleanup and organization:

- **Auto-Cleanup** - Old files removed after limit
- **Unique Filenames** - Timestamp-based naming
- **Organized Storage** - Structured output directory
- **Size Management** - Configurable file retention

### Error Handling

Robust error recovery:

- **Graceful Degradation** - Fallback to HTTP polling
- **User-Friendly Messages** - Clear error descriptions
- **Detailed Logging** - Debug information
- **Recovery Options** - Automatic retries
- **Validation** - Input checking before processing

### Concurrent Handling

Multiple users can generate simultaneously:

- **Session Management** - Proper HTTP connection pooling
- **WebSocket Multiplexing** - Single persistent connection
- **Queue Management** - Fair processing order
- **Resource Cleanup** - Proper session disposal

---

## 🔧 LoRA Support

### Overview

Dynamic LoRA loading with flexible strength control.

### Features

- **Auto-Discovery** - Automatically finds LoRAs in ComfyUI
- **Model Organization** - LoRAs grouped by compatible model
- **Strength Control** - Adjust LoRA influence (0.0-2.0)
- **Interactive Selection** - Choose LoRAs from dropdown
- **Multiple LoRAs** - Support for workflow-specific LoRA combinations

### Usage

**List Available LoRAs:**
```
/loras
```

**Use in Generation:**
```
/generate prompt:your prompt lora:lora_name lora_strength:0.8
```

**Via Interactive Setup:**
1. Run `/generate`
2. Select LoRA from dropdown
3. Adjust strength if needed
4. Generate

---

## 📱 Command Reference

### Generation Commands

| Command | Description |
|---------|-------------|
| `/generate` | Generate AI images |
| `/editflux` | High-quality image editing |
| `/editqwen` | Ultra-fast image editing |

### Utility Commands

| Command | Description |
|---------|-------------|
| `/status` | Check bot and ComfyUI status |
| `/help` | Get help and command info |
| `/loras` | List available LoRA models |

---

## 🎯 Best Practices

### For Best Results

1. **Be Specific** - Detailed prompts yield better results
2. **Use Appropriate Steps** - 20-30 steps for most generations
3. **Start Simple** - Test with basic parameters first
4. **Choose Right Tool** - Qwen for speed, Flux for quality
5. **Experiment with LoRAs** - Find styles that work for you

### Performance Tips

1. **Batch Wisely** - Use batch_size for variations
2. **Optimize Steps** - More steps ≠ always better
3. **Use Seed Control** - Reproduce good results with same seed
4. **Monitor Queue** - Generate during off-peak times
5. **Clean Outputs** - Regularly clear old files

### Workflow Efficiency

1. **Generate First** - Start with basic generation
2. **Iterate with Qwen** - Fast edits for refinement
3. **Final Polish with Flux** - High-quality final edits
4. **Upscale Last** - Upscale only final results
5. **Animate Select Results** - Videos take time, be selective

---

## 🆕 New in v2.0.0

- ✅ Refactored command handlers
- ✅ Improved progress tracking accuracy
- ✅ Better error messages
- ✅ Enhanced validation
- ✅ Optimized performance
- ✅ Cleaner architecture
- ✅ 99% test coverage

See **[[Changelog]]** for complete release history.

---

**🎨 Ready to explore all features? Check out [[Usage Examples]] for practical demonstrations!**

