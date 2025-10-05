# User Guide 📖

Complete guide to using all DisComfy features for creating amazing AI art in Discord.

---

## 🎨 Quick Start

The fastest way to start:
```
/generate prompt:a beautiful sunset over mountains
```

That's it! DisComfy will generate an image and provide buttons for upscaling, editing, and animation.

---

## 📝 Available Commands

### Image Generation Commands

#### `/generate` - Create AI Images
Generate images using AI models with full customization.

**Basic Usage:**
```
/generate prompt:your description here
```

**Full Parameters:**
- `prompt` (required) - Description of what to generate
- `negative_prompt` (optional) - What to avoid in the image
- `model` (optional) - AI model to use: `flux`, `flux_krea`, `hidream`
- `width` (optional) - Image width (512-2048, default: 1024)
- `height` (optional) - Image height (512-2048, default: 1024)
- `steps` (optional) - Sampling steps (10-50, default: 30)
- `cfg` (optional) - CFG scale (1-20, default: 5.0)
- `batch_size` (optional) - Number of images (1-4, default: 1)
- `seed` (optional) - Random seed for reproducibility
- `lora` (optional) - LoRA model to use
- `lora_strength` (optional) - LoRA strength (0.0-2.0, default: 1.0)

**Examples:**
```
# Basic generation
/generate prompt:a dragon flying through clouds

# With negative prompt
/generate prompt:beautiful portrait negative_prompt:blurry, distorted

# With specific model
/generate prompt:anime character model:flux_krea

# Custom dimensions
/generate prompt:landscape scene width:1920 height:1080

# Batch generation
/generate prompt:cat photos batch_size:4

# With LoRA
/generate prompt:artistic portrait lora:anime_style lora_strength:0.8

# Reproducible with seed
/generate prompt:sunset scene seed:12345
```

### Image Editing Commands

#### `/editflux` - High-Quality Editing
Edit images using Flux Kontext for detailed, high-quality results.

**Parameters:**
- `image` (required) - Image to edit (attachment)
- `prompt` (required) - Description of desired changes
- `steps` (optional) - Sampling steps (10-50, default: 20)
- `cfg` (optional) - CFG scale (1-10, default: 2.5)
- `seed` (optional) - Random seed

**Examples:**
```
/editflux image:photo.jpg prompt:add sunglasses and a hat
/editflux image:portrait.png prompt:change background to beach scene steps:30
/editflux image:car.jpg prompt:make it red and add racing stripes
```

**Processing Time:** 1-3 minutes  
**Best For:** Detailed edits, complex changes, high quality

#### `/editqwen` - Ultra-Fast Editing
Edit images using Qwen 2.5 VL for quick results. Supports 1-3 images!

**Parameters:**
- `image` (required) - Primary image to edit
- `image2` (optional) - Second reference image  
- `image3` (optional) - Third reference image (requires image2)
- `prompt` (required) - Description of desired changes
- `steps` (optional) - Sampling steps (4-20, default: 8)

**Examples:**
```
# Single image (fast editing)
/editqwen image:photo.jpg prompt:add sunglasses steps:8

# Two images (style transfer/combination)
/editqwen image:content.jpg image2:style.jpg prompt:apply style from image2

# Three images (multi-reference)
/editqwen image:base.jpg image2:ref1.jpg image3:ref2.jpg prompt:combine elements
```

**Processing Time:** 30-60 seconds  
**Best For:** Quick iterations, testing ideas, style transfer

---

## 🔘 Interactive Buttons

After generating or uploading images, you'll see action buttons:

### 🔍 Upscale Button
Enhance image resolution with AI upscaling.

**Click to open settings modal:**
- **Upscale Ratio:** 2x, 4x, or 8x magnification
- **Denoise Strength:** 0.1-1.0 (higher = more changes)
- **Steps:** 10-50 (more = better quality)
- **Prompt/Negative:** Optional text guidance

**Examples:**
- 2x upscale, low denoise (0.2) - Slight enhancement
- 4x upscale, medium denoise (0.35) - Balanced quality
- 8x upscale, high denoise (0.5) - Major enhancement

**Tips:**
- Start with 2x to test settings
- Lower denoise preserves original better
- Higher steps improve quality but take longer

### ✏️ Flux Edit Button
Opens Flux Kontext editing modal for high-quality edits.

**Settings:**
- **Edit Prompt:** What changes to make
- **Steps:** 10-50 (default: 20)
- **CFG:** 1-10 (default: 2.5)

**Best for:**
- Detailed modifications
- Adding/removing complex elements
- High-quality results

### ⚡ Qwen Edit Button
Opens Qwen editing modal for ultra-fast edits.

**Settings:**
- **Edit Prompt:** What changes to make
- **Steps:** 4-20 (default: 8)

**Best for:**
- Quick iterations
- Testing ideas
- Style changes
- Fast results

### 🎬 Animate Button
Convert image to smooth MP4 video.

**Settings:**
- **Animation Prompt:** How image should animate (optional)
- **Frame Count:** 81, 121, or 161 frames
  - 81 frames ≈ 2.7 seconds
  - 121 frames ≈ 4 seconds (recommended)
  - 161 frames ≈ 5.4 seconds
- **Strength:** 0.1-1.0 (animation intensity)
  - 0.3-0.5: Subtle movement
  - 0.6-0.8: Moderate animation (default: 0.7)
  - 0.9-1.0: Strong transformation
- **Steps:** Sampling steps (default: 4)

**Examples:**
```
Animation Prompt: "the camera slowly zooms in"
Animation Prompt: "gentle wind blowing through hair"
Animation Prompt: "flowing water and moving clouds"
Animation Prompt: (leave empty for automatic animation)
```

**Tips:**
- Descriptive prompts guide animation style
- Empty prompt = automatic animation
- Higher frame count = smoother but slower
- Default strength (0.7) works well for most

**Processing Time:** 2-10 minutes depending on settings

---

## 📊 Progress Tracking

DisComfy shows real-time progress with detailed information:

### Progress Display
```
🎨 Generating Image
📊 67.5% ████████████████░░░░
🔄 Sampling (27/40)
⏱️ Elapsed: 32s | ETA: 16s
Settings: 1024x1024 | Steps: 40 | CFG: 5.0
```

### Status Phases
1. **⏳ Queued** - Waiting in ComfyUI queue
   - Shows queue position
   - Appears when ComfyUI is busy

2. **🔄 Preparing** - Loading models and setup
   - Initial phase
   - Usually very quick

3. **🎨 Generating** - Active generation
   - Shows step progress (e.g., 27/40)
   - Percentage completion
   - Time estimates

4. **✅ Complete** - Generation finished
   - Image/video ready
   - Action buttons available

---

## 🎯 Advanced Usage

### Using LoRAs

LoRAs (Low-Rank Adaptations) customize the AI model's style.

**Find Available LoRAs:**
Use `/generate` and interactive setup will show available LoRAs for selected model.

**Using LoRAs:**
```
# In command
/generate prompt:portrait lora:anime_style lora_strength:0.8

# Or use interactive model/LoRA selector
/generate prompt:portrait
# Then choose model and LoRA from dropdown
```

**LoRA Strength Guide:**
- `0.3-0.5` - Subtle style influence
- `0.6-0.8` - Moderate style (recommended)
- `0.9-1.2` - Strong style
- `1.3-2.0` - Maximum style (may overpower)

### Batch Generation

Generate multiple variations at once:

```
/generate prompt:fantasy landscape batch_size:4
```

**Benefits:**
- Test different seeds automatically
- Compare variations
- Faster than generating individually

**Considerations:**
- Takes longer than single image
- Uses more memory
- All images use same parameters

### Seed Usage for Reproducibility

Seeds ensure reproducible generations:

```
# First generation
/generate prompt:dragon flying seed:12345
# Creates specific dragon image

# Reproduce exact image
/generate prompt:dragon flying seed:12345
# Creates identical image
```

**Tips:**
- No seed = random each time
- Same seed + parameters = identical result
- Use seeds to reproduce liked images
- Vary other parameters with same seed for variations

### Multi-Image Qwen Editing

Combine multiple images for complex edits:

**Style Transfer (2 images):**
```
/editqwen image:content.jpg image2:style_ref.jpg 
prompt:apply the artistic style from image 2 to image 1
```

**Background Replacement (2 images):**
```
/editqwen image:subject.jpg image2:background.jpg
prompt:place the subject in the new background
```

**Complex Composition (3 images):**
```
/editqwen image:base.jpg image2:element1.jpg image3:element2.jpg
prompt:combine all three images harmoniously
```

**Tips:**
- First image is the primary base
- Additional images provide reference/style
- Clear prompts describing desired combination work best
- Works with Qwen only (not Flux)

---

## 🌟 Creative Workflows

### Quick Iteration Workflow
1. Generate base image: `/generate prompt:your idea`
2. Quick edit: Click **⚡ Qwen Edit** → refine
3. Repeat step 2 until satisfied
4. Final quality: Click **✏️ Flux Edit** → polish
5. Upscale: Click **🔍 Upscale** → 4x enhancement

### High-Quality Workflow
1. Generate with high steps: `/generate prompt:your idea steps:50`
2. Edit with Flux: Click **✏️ Flux Edit** → detailed changes
3. Upscale high quality: Click **🔍 Upscale** → 4x, steps:50
4. Animate: Click **🎬 Animate** → 161 frames

### Batch Comparison Workflow
1. Generate variations: `/generate prompt:your idea batch_size:4`
2. Choose best result
3. Click **🔍 Upscale** on best image
4. Use upscaled as base for further work

### Style Exploration Workflow
1. Generate base: `/generate prompt:portrait`
2. Try different LoRAs with same seed:
   ```
   /generate prompt:portrait lora:style1 seed:12345
   /generate prompt:portrait lora:style2 seed:12345
   /generate prompt:portrait lora:style3 seed:12345
   ```
3. Compare results, choose favorite style
4. Create final with chosen LoRA + high settings

---

## 💡 Pro Tips

### Getting Better Results

**Prompt Writing:**
- Be specific and descriptive
- Include style keywords (e.g., "digital art", "photorealistic")
- Mention lighting, mood, perspective
- Use negative prompts to avoid unwanted elements

**Quality Settings:**
- More steps = better quality but slower
- CFG 5-7 for most cases
- Try lower CFG (2-4) if output is oversaturated
- Try higher CFG (8-10) if output lacks detail

**Model Selection:**
- **Flux** - General purpose, reliable
- **Flux Krea** - Enhanced quality, creative
- **HiDream** - Specific artistic styles

### Troubleshooting Generations

**Prompt Ignored:**
- Increase CFG scale
- Add more descriptive words
- Try negative prompt to exclude unwanted elements

**Low Quality Output:**
- Increase steps (30-50)
- Check if correct model selected
- Ensure ComfyUI has proper models installed

**Generation Fails:**
- Check prompt length (<1000 characters)
- Verify dimensions are valid (512-2048)
- Check ComfyUI is running
- Review bot logs for errors

**Slow Generation:**
- Reduce batch size
- Lower steps temporarily
- Check ComfyUI system resources
- Verify no other heavy tasks running

---

## 🤝 Sharing and Collaboration

### Universal Button Access
**Anyone can use buttons on any generation!**

Benefits:
- Team members can upscale each other's work
- Collaborative editing workflows
- Share generations and let others enhance

Example collaboration:
1. User A generates base image
2. User B clicks **⚡ Qwen Edit** to add elements
3. User C clicks **🔍 Upscale** for final quality
4. User D clicks **🎬 Animate** to create video

### Buttons Never Expire
Unlike typical Discord bots:
- Buttons work forever (until bot restarts)
- Can return to old generations
- Build on previous work anytime

---

## 📚 Command Reference Quick Table

| Command | Purpose | Speed | Best For |
|---------|---------|-------|----------|
| `/generate` | Create images | 30s-2m | New images |
| `/editflux` | High-quality edit | 1-3m | Detailed changes |
| `/editqwen` | Fast edit | 30-60s | Quick iterations |
| 🔍 Upscale | Enhance resolution | 45s-2m | Final quality |
| 🎬 Animate | Create video | 2-10m | Bring images to life |

---

## 🎯 Next Steps

- **[[Custom Workflows]]** - Create specialized workflows
- **[[Troubleshooting]]** - Solve common issues
- **[[FAQ]]** - Frequently asked questions
- **[[Developer Guide]]** - Integrate new features

---

**🎨 Ready to create? Start experimenting with `/generate`!**

