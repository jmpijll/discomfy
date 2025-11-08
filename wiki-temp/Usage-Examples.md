# Usage Examples

Practical examples for using DisComfy commands and features.

---

## 🎨 Basic Image Generation

### Simple Generation

```
/generate prompt:a beautiful sunset over the ocean
```

**What happens:**
1. Interactive setup view appears
2. Choose model (Flux, Flux Krea, or HiDream)
3. Optionally select a LoRA
4. Click "Generate"
5. Watch real-time progress
6. Image appears with action buttons

### Generation with Parameters

```
/generate prompt:cyberpunk cityscape at night width:1024 height:768 steps:30 cfg:7.5 batch_size:2
```

**Parameters explained:**
- `width:1024` - Image width in pixels
- `height:768` - Image height in pixels
- `steps:30` - 30 sampling steps for quality
- `cfg:7.5` - Guidance scale
- `batch_size:2` - Generate 2 variations

### Using LoRAs

```
/generate prompt:anime character in magical forest lora:anime_style_v2 lora_strength:0.8
```

**LoRA features:**
- `lora:anime_style_v2` - Name of LoRA to use
- `lora_strength:0.8` - 80% strength (0.0-2.0 range)

---

## ✏️ Image Editing

### High-Quality Editing (Flux Kontext)

**For detailed, high-quality edits:**

```
/editflux image:<upload_photo> prompt:add sunglasses and a hat steps:25
```

**Best for:**
- Detailed edits
- Complex changes
- Final quality edits
- When you have time (1-3 minutes)

**Tips:**
- Use 20-30 steps for best quality
- Be specific in prompts
- More steps = better detail

### Ultra-Fast Editing (Qwen 2.5 VL)

**For quick iterations:**

```
/editqwen image:<upload_photo> prompt:change the sky to sunset steps:8
```

**Best for:**
- Rapid iteration
- Testing ideas
- Quick changes
- When speed matters (30-60 seconds)

**Tips:**
- Use 4-8 steps for fastest results
- 8-12 steps for better quality
- Perfect for experimentation

### Editing Generated Images

**Post-generation editing:**
1. Generate an image with `/generate`
2. Click **✏️ Flux Edit** button for high quality
3. OR click **⚡ Qwen Edit** button for speed
4. Enter edit prompt in modal
5. Adjust steps if needed
6. Submit and watch progress

**Example prompts:**
- "make the character smile"
- "add a dramatic storm in the background"
- "change hair color to blue"
- "add magical sparkles around the subject"
- "make it nighttime instead of day"

---

## 🔍 Image Upscaling

### Basic Upscaling

**From generated image:**
1. Generate or upload image
2. Click **🔍 Upscale** button
3. Modal appears with options:
   - Upscale Ratio: Choose 2x, 4x, or 8x
   - Denoise Strength: 0.5 (default)
   - Sampling Steps: 20 (default)
4. Click Submit

### Upscaling Scenarios

**Quick 2x Upscale:**
- Ratio: 2x
- Denoise: 0.3
- Steps: 15
- Use: Fast upscale, minimal changes

**Standard 4x Upscale:**
- Ratio: 4x
- Denoise: 0.5
- Steps: 20
- Use: Balanced quality and speed

**Maximum 8x Detail Enhancement:**
- Ratio: 8x
- Denoise: 0.7
- Steps: 30
- Use: Maximum detail, poster quality

**Denoise Strength Guide:**
- `0.1-0.3` - Minimal change, preserve original
- `0.4-0.6` - Balanced enhancement
- `0.7-1.0` - Strong detail enhancement

---

## 🎬 Video Generation

### Basic Animation

**From generated image:**
1. Generate an image with `/generate`
2. Click **🎬 Animate** button
3. Modal shows options:
   - Frame Count: 121 frames (default)
   - Strength: 0.7
   - Steps: 25
   - Animation Prompt: (original prompt pre-filled)
4. Click Submit
5. Wait 2-10 minutes depending on settings

### Custom Animation Prompts

**Change how the image animates:**

**Slow Pan:**
```
Animation Prompt: slowly pan across the scene from left to right
```

**Zoom Effect:**
```
Animation Prompt: camera slowly zooms in on the subject
```

**Rotation:**
```
Animation Prompt: gentle 360 degree rotation around the subject
```

**Dynamic Movement:**
```
Animation Prompt: dynamic movement with parallax effect and depth
```

**Dramatic Effect:**
```
Animation Prompt: dramatic camera movement with zoom and rotation
```

### Frame Count Selection

**81 frames (~2 seconds):**
- Fastest generation
- Short loops
- Quick previews

**121 frames (~3 seconds):**
- Standard animation
- Good balance
- Most common choice

**161 frames (~5 seconds):**
- Longer animation
- More dramatic
- Better for complex motion
- Takes longer to generate

---

## 🎯 Advanced Generation

### Seed Control

**Reproduce a good result:**
1. Generate image with random seed
2. Note the seed from image info
3. Reuse seed for similar results:

```
/generate prompt:your prompt seed:123456789 steps:30
```

**Using seeds:**
- `-1` = Random seed (default)
- `Same seed + same params` = Similar result
- `Same seed + different prompt` = Similar composition

### Batch Generation

**Generate multiple variations:**

```
/generate prompt:fantasy castle on a hill batch_size:4
```

**What happens:**
- Generates 4 different images
- All with same parameters
- Different seeds automatically
- Posted as multiple messages

**Best practices:**
- Use batch_size 2-4 for variations
- More images = longer wait
- Good for exploring ideas

### CFG Scale Experiments

**Low CFG (3-5):**
```
/generate prompt:abstract art painting cfg:4
```
- More creative interpretation
- Less adherence to prompt
- More artistic freedom

**Medium CFG (6-8):**
```
/generate prompt:realistic portrait cfg:7.5
```
- Balanced results
- Good prompt adherence
- Recommended default

**High CFG (9-15):**
```
/generate prompt:photorealistic cityscape cfg:12
```
- Very strict prompt following
- Can be over-saturated
- Use carefully

---

## 🔄 Complete Workflow Examples

### Workflow 1: Character Creation

1. **Initial Generation:**
```
/generate prompt:anime character, female warrior, fantasy armor, detailed
```

2. **Quick Refinement (Qwen):**
- Click **⚡ Qwen Edit**
- Prompt: "add magical sword in hand"
- Steps: 8

3. **Polish (Flux):**
- Click **✏️ Flux Edit**
- Prompt: "enhance details, add glowing blue eyes"
- Steps: 25

4. **Upscale:**
- Click **🔍 Upscale**
- Ratio: 4x
- Denoise: 0.5
- Steps: 20

### Workflow 2: Landscape Art

1. **Generate Base:**
```
/generate prompt:fantasy landscape, mountains, sunset, ethereal lighting width:1344 height:768
```

2. **Iterate Quickly:**
- Click **⚡ Qwen Edit**
- Try: "add castle on mountain peak"
- Steps: 8
- If not perfect, click again with variations

3. **Final Quality:**
- Click **✏️ Flux Edit**
- Prompt: "enhance details, add dramatic clouds"
- Steps: 30

4. **Animate:**
- Click **🎬 Animate**
- Frames: 161
- Prompt: "slow pan across the landscape"

### Workflow 3: Quick Concept Iteration

1. **Start Simple:**
```
/generate prompt:modern logo design, minimalist
```

2. **Rapid Iterations with Qwen:**
- Click **⚡ Qwen Edit**: "make it blue instead of red" (8 steps)
- Click **⚡ Qwen Edit**: "add geometric shapes" (8 steps)
- Click **⚡ Qwen Edit**: "simplify the design" (8 steps)
- Each edit: 30-60 seconds

3. **Final Version:**
- Once happy, use **✏️ Flux Edit** for final quality
- Then **🔍 Upscale** to 4x

---

## 📊 Status and Information

### Check Bot Status

```
/status
```

**Shows:**
- Bot version
- Discord connection status
- ComfyUI connection status
- System information

### List Available LoRAs

```
/loras
```

**Shows:**
- All available LoRAs
- Organized by model type
- How to use them

### Get Help

```
/help
```

**Shows:**
- Command reference
- Parameter information
- Quick tips
- Links to documentation

---

## 💡 Pro Tips

### Generation Tips

1. **Prompt Engineering:**
   - Be specific and descriptive
   - Use style descriptors (photorealistic, anime, oil painting)
   - Add quality keywords (detailed, high quality, 8k)
   - Separate concepts with commas

2. **Parameter Optimization:**
   - Start with defaults
   - Adjust one parameter at a time
   - Save seeds for good results
   - More steps isn't always better (20-30 is usually enough)

3. **LoRA Usage:**
   - Start with strength 0.7-1.0
   - Lower strength (0.3-0.5) for subtle effects
   - Higher strength (1.2-2.0) for stronger influence
   - Check which model the LoRA is for

### Editing Tips

1. **Choose Right Tool:**
   - Testing ideas? → Qwen (fast)
   - Final result? → Flux (quality)
   - Multiple iterations? → Qwen first, Flux last

2. **Edit Prompts:**
   - Be specific about the change
   - Mention what to keep: "keep everything else the same, just add..."
   - Describe desired result, not the process

3. **Steps vs Speed:**
   - Qwen 4-8 steps: Maximum speed
   - Qwen 8-12 steps: Balanced
   - Flux 15-25 steps: Good quality
   - Flux 30-50 steps: Maximum quality

### Upscaling Tips

1. **When to Upscale:**
   - Only upscale finals (saves time)
   - Upscale after all edits
   - Good for prints and high-res needs

2. **Denoise Sweet Spots:**
   - Photos: 0.3-0.5
   - Art: 0.5-0.7
   - Heavy enhancement: 0.7-1.0

3. **Ratio Selection:**
   - 2x: Quick social media
   - 4x: Standard printing
   - 8x: Large format, posters

### Video Tips

1. **Frame Selection:**
   - 81: Social media loops
   - 121: Standard animations
   - 161: Presentations, dramatic effect

2. **Animation Prompts:**
   - Simple movements work best
   - Mention camera movement
   - Avoid complex scene changes
   - Test with 81 frames first

3. **Performance:**
   - Videos take 2-10 minutes
   - Don't spam video generation
   - Generate videos during off-peak

---

## 🚀 Quick Reference

### Fast Iteration Loop
1. Generate → Qwen Edit → Qwen Edit → Flux Edit → Upscale

### Quality Priority
1. Generate with high steps → Flux Edit → Upscale 4x → Done

### Speed Priority
1. Generate → Qwen Edit → Done (Total: 1-2 minutes)

### Full Production
1. Generate → Test with Qwen → Final Flux Edit → Upscale 8x → Animate

---

**🎨 Ready to create? Try these examples in your Discord server!**

See **[[Features]]** for detailed parameter information and **[[User Guide]]** for complete documentation.

