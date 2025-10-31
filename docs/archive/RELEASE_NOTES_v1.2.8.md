# DisComfy v1.2.8 Release Notes

## 🎉 Dual Image Editing Models - Choose Your Speed!

**Release Date:** October 3, 2025

DisComfy v1.2.8 introduces a revolutionary dual-editing system that lets you choose between high-quality detailed editing or ultra-fast editing, depending on your needs!

---

## ✨ What's New

### 🚀 **Qwen 2.5 VL Ultra-Fast Editing**
- **Lightning Fast**: Edit images in just 30-60 seconds with 4-20 steps
- **High Quality**: Qwen 2.5 VL model delivers excellent results with fewer steps
- **Optimized Workflow**: Designed for speed without sacrificing quality
- **Perfect For**: Quick edits, iterative testing, and rapid prototyping

### ✏️ **Flux Kontext High-Quality Editing**
- **Superior Detail**: 10-50 steps for maximum quality and precision
- **Fine Control**: More steps = more detailed and accurate edits
- **Professional Grade**: Best for final outputs and complex edits
- **Perfect For**: Final renders, complex changes, and detailed work

### 🔄 **Improved Command Structure**
- **`/editflux`**: Use Flux Kontext for high-quality editing (formerly `/edit`)
- **`/editqwen`**: NEW! Use Qwen 2.5 VL for ultra-fast editing
- **Both Available**: Choose the right tool for your workflow
- **Backward Compatible**: Old edit functionality preserved as Flux Edit

### 🎨 **Dual Post-Generation Buttons**
- **✏️ Flux Edit**: High-quality editing with Flux Kontext
- **⚡ Qwen Edit**: Ultra-fast editing with Qwen 2.5 VL
- **Universal Access**: Both buttons available on all generated images
- **Flexible Workflow**: Try both models and compare results!

---

## 🔧 Technical Improvements

### **Enhanced Image Generation Engine**
- Added `workflow_type` parameter to `generate_edit()` method
- Supports both "flux" and "qwen" editing workflows
- Automatic CFG adjustment based on workflow type
- Optimized parameter validation for each model

### **Smart Parameter Handling**
- Flux: 10-50 steps (default: 20) | CFG: 2.5
- Qwen: 4-20 steps (default: 8) | CFG: 1.0
- Context-aware validation and error messages
- Model-specific defaults for optimal results

### **Workflow Integration**
- Added Qwen image edit workflow (`qwen_image_edit.json`)
- Automatic workflow selection based on edit type
- Seamless integration with existing ComfyUI setup
- Full progress tracking for both workflows

---

## 📖 Usage Examples

### Using Slash Commands

**Flux Kontext (High Quality):**
```
/editflux image:photo.jpg prompt:add sunglasses and a hat steps:25
```
- Best for: Final outputs, complex edits
- Time: 1-3 minutes
- Steps: 10-50 (default: 20)

**Qwen 2.5 VL (Ultra Fast):**
```
/editqwen image:photo.jpg prompt:add sunglasses and a hat steps:8
```
- Best for: Quick edits, testing
- Time: 30-60 seconds
- Steps: 4-20 (default: 8)

### Using Post-Generation Buttons

1. Generate an image with `/generate`
2. Click **✏️ Flux Edit** for high-quality editing
   - Or click **⚡ Qwen Edit** for ultra-fast editing
3. Enter your edit prompt and configure steps
4. Watch real-time progress as your edit is generated!

---

## 🎯 When to Use Each Model

### Use **Flux Edit** When:
- ✅ You need maximum quality and detail
- ✅ Working on final outputs or deliverables
- ✅ Complex edits requiring precision
- ✅ You have time to wait (1-3 minutes)
- ✅ Professional-grade results matter

### Use **Qwen Edit** When:
- ⚡ You need results fast (30-60 seconds)
- ⚡ Iterating quickly through ideas
- ⚡ Testing different edits
- ⚡ Simple to moderate changes
- ⚡ Speed is more important than perfection

---

## 🔄 Migration Guide

### For Existing Users

The `/edit` command has been renamed to `/editflux` to accommodate the new Qwen editing model:

**Old:**
```
/edit image:photo.jpg prompt:make the sky blue
```

**New (same functionality):**
```
/editflux image:photo.jpg prompt:make the sky blue
```

**Or try the new ultra-fast option:**
```
/editqwen image:photo.jpg prompt:make the sky blue
```

All existing workflows continue to work exactly as before. The edit button on generated images now shows both options!

---

## 📦 Installation & Setup

### New Workflow File

Make sure to add the Qwen workflow to your `workflows/` directory:
- Download `qwen_image_edit.json` from the repository
- Place it in your `workflows/` folder
- Restart DisComfy to load the new workflow

### Required Models

For Qwen editing to work, you'll need:
- **Qwen Image Edit Model** (`qwen_image_edit_2509_fp8_e4m3fn.safetensors`)
- **Qwen CLIP** (`qwen_2.5_vl_7b_fp8_scaled.safetensors`)
- **Qwen VAE** (`qwen_image_vae.safetensors`)
- **Lightning LoRA** (`Qwen-Image-Edit-Lightning-4steps-V1.0.safetensors`)

Place these in your ComfyUI models directories as specified in the workflow.

---

## 🐛 Bug Fixes & Improvements

### Code Quality
- ✅ No linting errors
- ✅ Comprehensive type hints
- ✅ Consistent error handling
- ✅ Improved code documentation

### User Experience
- ✅ Clear model differentiation with emojis
- ✅ Context-aware help messages
- ✅ Better parameter validation
- ✅ Improved progress tracking

---

## 🔜 What's Next

We're constantly improving DisComfy! Future releases may include:
- 🎬 Multiple video generation models
- 🎨 More image generation models
- 🖼️ Additional upscaling workflows
- 🌈 Style transfer capabilities
- 🤖 Advanced automation features

---

## 🙏 Acknowledgments

Special thanks to:
- **Alibaba Qwen Team** - For the amazing Qwen 2.5 VL model
- **ComfyUI Community** - For workflow development and support
- **DisComfy Users** - For feedback and feature requests
- **Discord.py Developers** - For the excellent framework

---

## 📞 Support & Feedback

Need help or have suggestions?
- 📖 Check the updated [README.md](README.md)
- 🐛 Report issues on GitHub
- 💬 Join our Discord community
- 📧 Contact the maintainers

---

**Enjoy lightning-fast editing with DisComfy v1.2.8! ⚡**

*Released with ❤️ by the DisComfy team*

