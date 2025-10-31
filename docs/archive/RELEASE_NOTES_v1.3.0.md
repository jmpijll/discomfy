# Release Notes - DisComfy v1.3.0

**Release Date:** October 4, 2025  
**Type:** Feature Release

---

## 🎉 New Feature: Multi-Image Qwen Editing

DisComfy v1.3.0 introduces powerful multi-image editing capabilities to the `/editqwen` command, allowing you to combine and edit 1-3 images simultaneously using Qwen 2.5 VL!

---

## ✨ What's New

### Multi-Image Qwen Edit
- **1-3 Image Support**: The `/editqwen` command now accepts up to 3 input images
- **Automatic Workflow Selection**: The bot automatically chooses the correct workflow based on image count:
  - 1 image → Uses `qwen_image_edit.json`
  - 2 images → Uses `qwen_image_edit_2.json`
  - 3 images → Uses `qwen_image_edit_3.json`

### New Command Parameters
- `image` - Primary image (required)
- `image2` - Second image (optional)
- `image3` - Third image (optional)
- `prompt` - Edit instructions (required)
- `steps` - Sampling steps 4-20 (optional, default: 8)

### Usage Examples

**Single Image (Original Behavior):**
```
/editqwen image:photo.jpg prompt:enhance the lighting steps:8
```

**Two Images (NEW):**
```
/editqwen image:photo1.jpg image2:photo2.jpg prompt:combine both styles steps:8
```

**Three Images (NEW):**
```
/editqwen image:photo1.jpg image2:photo2.jpg image3:photo3.jpg prompt:merge all three steps:8
```

---

## 🔧 Technical Improvements

### Image Generator (`image_gen.py`)
- Enhanced `generate_edit()` method with new `additional_images: Optional[List[bytes]]` parameter
- Smart workflow selection based on total image count
- Sequential image uploads with unique timestamps
- Support for up to 3 concurrent image inputs

### Workflow Parameters
- Updated `_update_qwen_edit_workflow_parameters()` to handle multiple `LoadImage` nodes
- Intelligent node assignment based on node ID ordering
- Automatic validation of image count vs. workflow requirements

### Bot Command (`bot.py`)
- `/editqwen` command now accepts `image2` and `image3` optional parameters
- Enhanced validation ensures `image3` requires `image2`
- All images validated for type and size limits
- Progress display shows total image count
- Initial response lists all input images with their file sizes

---

## 📝 Known Issues

### Concurrent Queue Handling
**Status:** Known Issue (Deferred)  
**Impact:** Medium

When multiple users start generations simultaneously, the second generation may not show completion in Discord until a third generation is started. This issue has been documented in `KNOWN_ISSUES.md` and will be addressed in a future release.

**Workaround:** Users should wait for the current generation to complete before starting a new one.

**Note:** Single generation tracking works perfectly. Progress tracking and WebSocket updates function correctly.

---

## 🚀 Upgrade Instructions

### From v1.2.x

1. **Pull Latest Changes:**
   ```bash
   cd discomfy
   git pull origin main
   ```

2. **Verify Workflows:**
   Ensure you have all three Qwen workflows in your `workflows/` directory:
   - `qwen_image_edit.json` (1 image)
   - `qwen_image_edit_2.json` (2 images)
   - `qwen_image_edit_3.json` (3 images)

3. **Restart Bot:**
   ```bash
   python bot.py
   ```

4. **Test Multi-Image Editing:**
   Try the new multi-image feature with 2-3 images!

### No Configuration Changes Required
- No changes to `config.json` needed
- No new dependencies
- Backward compatible with existing workflows
- All previous features remain unchanged

---

## 💡 Use Cases

### Creative Applications

**Style Transfer:**
```
/editqwen image:content.jpg image2:style_reference.jpg prompt:apply the style from image 2 to image 1
```

**Image Merging:**
```
/editqwen image:portrait.jpg image2:background.jpg prompt:place the person in the new background
```

**Multi-Reference Editing:**
```
/editqwen image:base.jpg image2:ref1.jpg image3:ref2.jpg prompt:combine elements from all images
```

---

## 📊 Performance

- **Processing Time:** Similar to single-image Qwen edits (~30-60 seconds)
- **Image Upload:** Sequential with 100ms delay between uploads
- **Memory Usage:** Scales linearly with image count
- **Quality:** Maintained across all image count modes

---

## 🔮 Future Plans

- Fix concurrent queue handling issue
- Expand multi-image support to other models
- Add image blending modes
- Implement region-specific multi-image editing

---

## 🙏 Acknowledgments

Thank you to the ComfyUI team for the excellent Qwen 2.5 VL model and multi-image editing capabilities!

---

## 📚 Documentation

- Full documentation: [README.md](README.md)
- Changelog: [CHANGELOG.md](CHANGELOG.md)
- Known Issues: [KNOWN_ISSUES.md](KNOWN_ISSUES.md)

---

**DisComfy v1.3.0 - Multi-Image AI Editing for Discord**

*Questions or issues? Open an issue on [GitHub](https://github.com/jmpijll/discomfy/issues)*

