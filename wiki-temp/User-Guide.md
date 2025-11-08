# User Guide

Complete guide to using DisComfy v2.0.

---

## 🎯 Overview

DisComfy is a powerful Discord bot that integrates ComfyUI for professional AI image and video generation directly in Discord.

---

## 🚀 Getting Started

### First Time Setup

1. Ensure bot is invited to your server
2. Type `/` in any channel to see commands
3. Run `/help` for quick overview
4. Try your first generation: `/generate prompt:a beautiful sunset`

### Basic Workflow

1. **Generate** - Create base image
2. **Refine** - Edit with Qwen (fast) or Flux (quality)
3. **Enhance** - Upscale for higher resolution
4. **Animate** - Convert to video (optional)

---

## 📝 Commands

### /generate

Generate AI images with interactive setup.

**Usage:**
```
/generate prompt:your description here
```

**Parameters:**
- `prompt` - Description of what to generate (required, 1-500 characters)

**Interactive Setup:**
After running the command, you'll see:

1. **Model Selection** - Choose between:
   - Flux - High-quality general purpose
   - Flux Krea - Enhanced Flux with improved quality
   - HiDream - Alternative model

2. **LoRA Selection** - Choose optional LoRA:
   - LoRAs organized by compatible model
   - Adjust strength with modal

3. **Settings Button** - Customize:
   - Width (256-2048, default: 1024)
   - Height (256-2048, default: 1024)
   - Steps (1-50, default: 30)
   - CFG Scale (1.0-20.0, default: 7.5)
   - Seed (-1 for random)
   - Batch Size (1-4, default: 1)

4. **Generate Button** - Start generation

**Example:**
```
/generate prompt:cyberpunk cityscape at night, neon lights, rain, detailed
```

---

### /editflux

High-quality image editing using Flux Kontext AI.

**Usage:**
```
/editflux image:<upload> prompt:edit description
```

**Parameters:**
- `image` - Image to edit (required, upload file)
- `prompt` - How to edit the image (required)
- `steps` - Sampling steps (optional, 10-50, default: 20)

**Best For:**
- Detailed, high-quality edits
- Complex changes
- Final polishing
- When you have time (1-3 minutes)

**Examples:**
```
/editflux image:photo.jpg prompt:add sunglasses and a hat
/editflux image:photo.jpg prompt:change background to mountains steps:30
/editflux image:photo.jpg prompt:make it nighttime instead of day
```

---

### /editqwen

Ultra-fast image editing using Qwen 2.5 VL AI.

**Usage:**
```
/editqwen image:<upload> prompt:edit description
```

**Parameters:**
- `image` - Image to edit (required, upload file)
- `prompt` - How to edit the image (required)
- `steps` - Sampling steps (optional, 4-20, default: 8)

**Best For:**
- Rapid iteration
- Testing ideas
- Quick changes
- Speed priority (30-60 seconds)

**Examples:**
```
/editqwen image:photo.jpg prompt:change shirt color to blue steps:8
/editqwen image:photo.jpg prompt:add flowers in background steps:12
/editqwen image:photo.jpg prompt:make the character smile
```

---

### /status

Check bot and ComfyUI status.

**Usage:**
```
/status
```

**Shows:**
- Bot version
- Discord connection status
- ComfyUI connection status
- System information

**Example Output:**
```
✅ Bot Status
Version: v2.0.0
Discord: Connected
ComfyUI: Connected (http://localhost:8188)
Uptime: 2 hours, 15 minutes
```

---

### /help

Get command help and information.

**Usage:**
```
/help
```

**Shows:**
- Command reference
- Parameter information
- Quick tips
- Links to documentation

---

### /loras

List available LoRA models.

**Usage:**
```
/loras
```

**Shows:**
- All available LoRAs
- Organized by model type
- How to use them in generations

**Example Output:**
```
📚 Available LoRAs

Flux LoRAs:
• anime_style_v2
• photorealistic_enhance
• art_deco

HiDream LoRAs:
• landscape_enhance
• portrait_v3
```

---

## 🔘 Interactive Buttons

Every generated image has action buttons that **anyone** can use:

### 🔍 Upscale Button

Upscale image using AI super-resolution.

**Options:**
- **Upscale Ratio** - Choose 2x, 4x, or 8x
- **Denoise Strength** - 0.1-1.0 (detail enhancement)
- **Sampling Steps** - 10-50 (quality control)

**When to Use:**
- Final images for high resolution
- Printing or large format
- Detail enhancement

**Tips:**
- 2x: Quick upscale for social media
- 4x: Standard printing quality
- 8x: Large format, maximum detail
- Denoise 0.5: Balanced
- Denoise 0.7-1.0: Strong enhancement

### ✏️ Flux Edit Button

High-quality editing using Flux Kontext.

**Opens Modal:**
- Edit prompt input
- Sampling steps (10-50)

**Best For:**
- Final quality edits
- Complex changes
- Professional results

**Example Prompts:**
- "add dramatic lighting"
- "change hair color to blue"
- "add magical effects"

### ⚡ Qwen Edit Button

Ultra-fast editing using Qwen 2.5 VL.

**Opens Modal:**
- Edit prompt input
- Sampling steps (4-20)

**Best For:**
- Quick iterations
- Testing ideas
- Rapid changes

**Example Prompts:**
- "make background darker"
- "add smile"
- "change shirt color"

### 🎬 Animate Button

Convert image to video animation.

**Options:**
- **Frame Count** - 81, 121, or 161 frames
- **Strength** - 0.1-1.0 (animation intensity)
- **Steps** - Quality control
- **Animation Prompt** - Customize motion

**Frame Counts:**
- 81 frames: ~2 seconds (quick loop)
- 121 frames: ~3 seconds (standard)
- 161 frames: ~5 seconds (longer, dramatic)

**Animation Prompt Examples:**
- "slowly pan across the scene"
- "camera zooms in on subject"
- "gentle rotation"
- "dynamic movement with parallax"

**Tips:**
- Test with 81 frames first
- Simple movements work best
- Videos take 2-10 minutes
- Original prompt pre-filled (editable)

---

## 📊 Progress Tracking

DisComfy provides real-time progress updates during generation:

### Progress Display

```
🎨 Generating Image
📊 65.0% █████████████░░░░░░░
🔄 Sampling (195/300)
⏱️ Elapsed: 1m 23s | ETA: 48s
🎯 Node: KSampler
Settings: 1024x1024 | Steps: 30 | CFG: 7.5
```

### Queue Status

When ComfyUI is busy:

```
⏳ Queued - Position #2 in queue
🔄 Other generations ahead: 1
⏱️ Elapsed: 15s
```

### Features

- **Real-time Updates** - Live percentage and ETA
- **Step Tracking** - Current step / total steps
- **Node Execution** - Which ComfyUI node is running
- **Queue Position** - Your place in line
- **Time Estimates** - Elapsed and remaining time
- **Settings Display** - Your generation parameters

---

## 💡 Tips & Best Practices

### Prompt Writing

**Be Specific:**
```
❌ "a dog"
✅ "a golden retriever puppy playing in a sunny garden, detailed fur, photorealistic"
```

**Use Style Descriptors:**
```
• "photorealistic"
• "anime style"
• "oil painting"
• "digital art"
• "8k, highly detailed"
```

**Separate Concepts:**
```
"subject, action, environment, lighting, style, quality"
"dragon, flying, mountains, sunset, fantasy art, detailed"
```

### Parameter Guidelines

**Steps:**
- 15-20: Fast, good quality
- 25-30: Balanced (recommended)
- 35-50: Maximum quality (slower)

**CFG Scale:**
- 3-5: More creative, less adherence
- 6-8: Balanced (recommended)
- 9-15: Strict adherence (can oversaturate)

**Batch Size:**
- 1: Single image
- 2-4: Variations (different seeds)

**Seed:**
- -1: Random (default)
- Specific number: Reproducible results
- Same seed + params = similar result

### Editing Workflow

**Quick Iteration:**
1. Generate base image
2. Edit with Qwen (steps: 8) - Test ideas quickly
3. Edit with Qwen again if needed
4. Final edit with Flux (steps: 25) - Polish
5. Upscale 4x - Final result

**Quality Priority:**
1. Generate with high steps (35-40)
2. Edit with Flux (steps: 30-40)
3. Upscale 8x with denoise 0.7
4. Animate if desired

### Upscaling Strategy

**When to Upscale:**
- Only upscale final images
- After all edits complete
- For printing or high-res needs

**Denoise Guide:**
- 0.1-0.3: Minimal change
- 0.4-0.6: Balanced (recommended)
- 0.7-1.0: Strong enhancement

### Video Generation

**Best Practices:**
- Start with 81 frames to test
- Use simple animation prompts
- Generate videos during off-peak
- Videos take 2-10 minutes
- Don't spam video generation

**Animation Prompts:**
- Keep it simple
- Describe camera movement
- Avoid scene changes
- Test before long renders

---

## 🎯 Use Cases

### Character Design

1. Generate base: `/generate prompt:character concept, detailed`
2. Refine features: Qwen edits for quick changes
3. Final details: Flux edit for quality
4. Upscale: 4x for portfolio

### Landscape Art

1. Generate: Wide aspect (1344x768)
2. Iterate: Qwen for composition changes
3. Polish: Flux for detail enhancement
4. Animate: Slow pan across scene

### Logo/Design

1. Generate: Simple, clear prompt
2. Iterate: Multiple Qwen edits
3. Final: Flux edit for perfection
4. Upscale: 4x for print

### Concept Art

1. Generate: Multiple variations (batch_size:4)
2. Pick best: Choose favorite
3. Refine: Edit to add details
4. Upscale: 8x for presentation

---

## ⚠️ Limitations

### Rate Limiting

- Configurable per-user limits
- Prevents spam and abuse
- Contact admin if blocked
- Check `/status` for limits

### File Sizes

- Images: Up to 25MB upload
- Generated: Varies by resolution
- Videos: Can be large (50-200MB)
- Auto-cleanup after 100 files

### Generation Times

- Images: ~30 seconds
- Edits (Qwen): 30-60 seconds
- Edits (Flux): 1-3 minutes
- Upscale: ~45 seconds
- Video: 2-10 minutes
- Queue times: Varies

### ComfyUI Requirements

- Must have required models
- Custom nodes needed for some workflows
- Enough VRAM for generation
- Stable network connection

---

## 🆘 Common Issues

### "Generation timed out"

**Solution:** Increase timeout in config or reduce complexity

### "Commands not appearing"

**Solution:** Wait 1-2 minutes or restart bot

### "Rate limited"

**Solution:** Wait for window to reset or contact admin

### "Workflow failed"

**Solution:** Check ComfyUI has required models

### Progress stuck

**Solution:** Normal if queued, otherwise check ComfyUI

See **[[Troubleshooting]]** for detailed solutions.

---

## 📚 Next Steps

- **[[Usage Examples]]** - Practical examples and workflows
- **[[Features]]** - Detailed feature documentation
- **[[Troubleshooting]]** - Common issues and solutions
- **[[Configuration Guide]]** - Customize bot settings
- **[[Custom Workflows]]** - Create your own workflows

---

**🎨 Ready to create amazing art? Start with `/generate` and explore!**
