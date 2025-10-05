# Custom Workflows Guide 🎨

Learn how to create and integrate custom ComfyUI workflows with DisComfy.

---

## 📋 Overview

DisComfy supports custom ComfyUI workflows, allowing you to:
- Use specialized AI models
- Create unique generation styles
- Implement custom processing pipelines
- Integrate community workflows

---

## ✅ Workflow Requirements

### Must-Have Properties

Every workflow node **MUST** have:
1. `class_type` - The ComfyUI node type
2. `inputs` - Dictionary of node inputs (can be empty)

### Valid Node Structure

```json
{
  "1": {
    "inputs": {
      "seed": 12345,
      "steps": 30
    },
    "class_type": "KSampler",
    "_meta": {
      "title": "KSampler"
    }
  }
}
```

**Common class_type values:**
- `KSampler` - Sampling node
- `CLIPTextEncode` - Text encoding
- `LoadImage` - Image loading
- `VAEDecode` - VAE decoding
- `SaveImage` - Image output
- And many more...

---

## 🚀 Creating Custom Workflows

### Step 1: Design in ComfyUI

1. **Open ComfyUI** in your browser
2. **Build your workflow** using nodes
3. **Test thoroughly** - ensure it works!
4. **Note important nodes:**
   - Where prompts go (CLIPTextEncode)
   - Sampling nodes (KSampler)
   - Dimension nodes (EmptyLatentImage)
   - Output nodes (SaveImage)

### Step 2: Export Workflow

**CRITICAL: Use API Format!**

❌ **WRONG:** Regular "Save"
```
File → Save
```

✅ **CORRECT:** API Format
```
File → Save (API Format)
```

**Why API Format?**
- Regular save includes UI positions and metadata
- API format includes only node structure
- DisComfy requires API format for validation

### Step 3: Validate Workflow

DisComfy v1.3.1+ automatically validates workflows and provides helpful error messages:

```
Workflow 'my_workflow' has 2 invalid node(s):
  - Node #1: Missing required 'class_type' property
  - Node #5: Missing required 'inputs' property

Common issues:
  1. Each node must have a 'class_type' property
  2. Each node must have an 'inputs' property
  3. Workflow must be exported as API format

To fix: In ComfyUI, use 'Save (API Format)'
```

**Manual Validation:**
```bash
# Check JSON syntax
python -m json.tool workflows/my_workflow.json

# Check for class_type
grep -o '"class_type"' workflows/my_workflow.json | wc -l
# Should match node count
```

### Step 4: Save to DisComfy

```bash
# Copy to workflows directory
cp my_workflow.json discomfy/workflows/
```

### Step 5: Configure in DisComfy

Edit `config.json`:

```json
"workflows": {
  "my_custom": {
    "file": "my_workflow.json",
    "name": "My Custom Workflow",
    "description": "Specialized workflow for X",
    "enabled": true
  }
}
```

---

## 🔧 Integrating Workflows

### Basic Integration

For workflows that work with standard parameters:

```json
"workflows": {
  "artistic_style": {
    "file": "artistic_style.json",
    "name": "Artistic Style",
    "description": "Creates artistic style images",
    "enabled": true
  }
}
```

DisComfy will automatically update:
- Prompts (CLIPTextEncode nodes)
- Seeds (RandomNoise, KSampler)
- Steps (BasicScheduler, KSampler)
- Dimensions (EmptyLatentImage, EmptySD3LatentImage)

### Advanced Integration

For custom parameters, add update logic to `image_gen.py`:

```python
def _update_custom_workflow_parameters(
    self,
    workflow: Dict[str, Any],
    prompt: str,
    custom_param: float,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """Update custom workflow parameters."""
    updated_workflow = json.loads(json.dumps(workflow))
    
    if seed is None:
        seed = random.randint(0, 2**32 - 1)
    
    for node_id, node_data in updated_workflow.items():
        class_type = node_data.get('class_type')
        
        # Standard updates
        if class_type == 'KSampler':
            node_data['inputs']['seed'] = seed
        
        # Custom node updates
        elif class_type == 'CustomNode':
            node_data['inputs']['custom_param'] = custom_param
    
    return updated_workflow
```

---

## 📝 Common Workflow Patterns

### Image Generation Workflow

**Required nodes:**
1. Model loading (CheckpointLoader, UNETLoader)
2. CLIP encoding (CLIPTextEncode) for positive/negative
3. Latent creation (EmptyLatentImage)
4. Sampling (KSampler)
5. VAE decode (VAEDecode)
6. Save (SaveImage)

**Example structure:**
```
CheckpointLoader → CLIPTextEncode (positive)
                → CLIPTextEncode (negative)
                → KSampler → VAEDecode → SaveImage
EmptyLatentImage →
```

### Image Editing Workflow

**Required nodes:**
1. Image loading (LoadImage)
2. Model loading
3. CLIP encoding for edit prompt
4. Image encoding (VAEEncode)
5. Sampling
6. VAE decode
7. Save

**Example structure:**
```
LoadImage → VAEEncode → KSampler → VAEDecode → SaveImage
                     ↑
CheckpointLoader → CLIPTextEncode
```

### Upscaling Workflow

**Required nodes:**
1. Image loading (LoadImage)
2. Upscale node (ImageUpscaleWithModel)
3. Optional: Refining with sampling
4. Save

**Example structure:**
```
LoadImage → ImageUpscaleWithModel → SaveImage
         Optional refinement:
         → VAEEncode → KSampler → VAEDecode →
```

---

## 🎯 Node Identification

DisComfy updates nodes by `class_type`. Here's how to identify them:

### Prompt Nodes (CLIPTextEncode)

DisComfy looks for nodes with title metadata:
```json
{
  "6": {
    "inputs": {
      "text": "prompt here"
    },
    "class_type": "CLIPTextEncode",
    "_meta": {
      "title": "CLIP Text Encode (Prompt) - Positive"
    }
  }
}
```

**Title keywords:**
- "Positive" → Updated with user prompt
- "Negative" → Updated with negative prompt

### Sampling Nodes

**KSampler:**
```json
{
  "inputs": {
    "seed": 12345,      // ← Updated
    "steps": 30,        // ← Updated
    "cfg": 7.0          // ← Updated
  },
  "class_type": "KSampler"
}
```

**RandomNoise (Flux):**
```json
{
  "inputs": {
    "noise_seed": 12345  // ← Updated
  },
  "class_type": "RandomNoise"
}
```

### Dimension Nodes

**EmptyLatentImage:**
```json
{
  "inputs": {
    "width": 1024,      // ← Updated
    "height": 1024,     // ← Updated
    "batch_size": 1     // ← Updated
  },
  "class_type": "EmptyLatentImage"
}
```

### LoRA Nodes

**LoraLoaderModelOnly:**
```json
{
  "inputs": {
    "lora_name": "style.safetensors",  // ← Updated
    "strength_model": 1.0               // ← Updated
  },
  "class_type": "LoraLoaderModelOnly"
}
```

---

## 🔍 Debugging Workflows

### Common Issues

**Issue 1: Workflow validation fails**
```
Error: Node #1: Missing required 'class_type' property
```
**Solution:** Re-export using "Save (API Format)"

**Issue 2: Prompts not applied**
```
Generated image doesn't match prompt
```
**Solution:** Check CLIPTextEncode nodes have title metadata

**Issue 3: Wrong dimensions**
```
Generated image has wrong size
```
**Solution:** Verify EmptyLatentImage nodes exist

**Issue 4: LoRAs not working**
```
LoRA not applied to generation
```
**Solution:** Check LoraLoaderModelOnly node exists

### Debug Logging

Enable debug logging to see workflow processing:

```json
// config.json
"logging": {
  "level": "DEBUG"
}
```

Check logs for:
```
DEBUG - Loaded workflow: my_custom
DEBUG - Updated workflow parameters: prompt='...', size=1024x1024
DEBUG - Found 5 KSampler nodes
DEBUG - Updated node 3: seed=12345
```

### Testing Workflow

1. **Test in ComfyUI first** - Ensure it works standalone
2. **Start with simple parameters** - Don't use LoRAs initially
3. **Check logs** - Look for errors or warnings
4. **Test incrementally** - Add features one at a time

---

## 📚 Example Workflows

### Simple Flux Workflow

```json
{
  "10": {
    "inputs": {
      "vae_name": "FLUX1/ae.safetensors"
    },
    "class_type": "VAELoader"
  },
  "11": {
    "inputs": {
      "clip_name1": "ViT-L-14.safetensors",
      "clip_name2": "t5-xxl.safetensors",
      "type": "flux"
    },
    "class_type": "DualCLIPLoader"
  },
  "6": {
    "inputs": {
      "text": "prompt here",
      "clip": ["11", 0]
    },
    "class_type": "CLIPTextEncode",
    "_meta": {
      "title": "Positive Prompt"
    }
  },
  "25": {
    "inputs": {
      "noise_seed": 12345
    },
    "class_type": "RandomNoise"
  },
  "13": {
    "inputs": {
      "noise": ["25", 0],
      "sampler": ["16", 0],
      "sigmas": ["17", 0]
    },
    "class_type": "SamplerCustomAdvanced"
  }
}
```

### Image Edit Workflow

```json
{
  "41": {
    "inputs": {
      "image": "input.png"
    },
    "class_type": "LoadImage"
  },
  "6": {
    "inputs": {
      "text": "edit instructions",
      "clip": ["11", 0]
    },
    "class_type": "CLIPTextEncode",
    "_meta": {
      "title": "Positive"
    }
  },
  "3": {
    "inputs": {
      "seed": 12345,
      "steps": 20,
      "cfg": 2.5,
      "positive": ["6", 0],
      "latent_image": ["47", 0]
    },
    "class_type": "KSampler"
  }
}
```

---

## 💡 Best Practices

### Workflow Design

1. **Keep it simple** - Complex workflows are harder to debug
2. **Use clear titles** - Add descriptive _meta.title to nodes
3. **Test thoroughly** - Ensure it works in ComfyUI first
4. **Document nodes** - Comment which nodes do what
5. **Version control** - Keep old versions for reference

### Node Organization

1. **Group related nodes** - Use similar node IDs
2. **Name consistently** - Use clear, descriptive titles
3. **Avoid hardcoded values** - Use nodes for configurable values
4. **Test edge cases** - Try extreme values

### Integration

1. **Start simple** - Basic parameters first
2. **Add features incrementally** - One at a time
3. **Validate input** - Check parameters make sense
4. **Handle errors gracefully** - Don't crash on bad input
5. **Document usage** - Add examples and notes

---

## 🔗 Resources

### ComfyUI Documentation
- [ComfyUI GitHub](https://github.com/comfyanonymous/ComfyUI)
- [ComfyUI Examples](https://comfyanonymous.github.io/ComfyUI_examples/)
- [Custom Nodes](https://github.com/ltdrdata/ComfyUI-Manager)

### DisComfy Examples
- Check `workflows/` directory for working examples
- See `image_gen.py` for parameter update logic
- Review `CHANGELOG.md` for workflow updates

---

## 🎯 Next Steps

- **[[Developer Guide]]** - Integrate workflows programmatically
- **[[User Guide]]** - Learn to use custom workflows
- **[[Troubleshooting]]** - Fix workflow issues
- **[[FAQ]]** - Common workflow questions

---

**🎨 Ready to create? Export your ComfyUI workflow and integrate it!**

