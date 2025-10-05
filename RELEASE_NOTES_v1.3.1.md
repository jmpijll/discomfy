# Release Notes - DisComfy v1.3.1

**Release Date:** October 5, 2025  
**Type:** Bug Fix Release

---

## 🐛 Critical Bug Fixes for Custom Workflows

DisComfy v1.3.1 addresses critical issues reported in [Issue #1](https://github.com/jmpijll/discomfy/issues/1) that prevented custom workflows from loading correctly and caused LoRA selector errors.

---

## 🔧 What's Fixed

### Fixed LoRA Selector Initialization Error
**Issue:** `'CompleteSetupView' object has no attribute 'insert_item'`

**Root Cause:** The code was calling a non-existent `insert_item()` method on Discord's `View` class.

**Fix:** Changed to use the correct `children.insert()` method for inserting UI elements at specific positions.

**Impact:** LoRA selector now loads properly without errors when initializing the generation setup view.

### Added Comprehensive Workflow Validation
**Issue:** `"Cannot execute because a node is missing the class_type property."`

**Root Cause:** Custom workflows exported in the wrong format or missing required properties that ComfyUI needs.

**Fix:** Added new `_validate_workflow()` method that performs comprehensive validation:
- Checks for missing `class_type` property on all nodes
- Validates overall workflow structure (must be a dictionary)
- Warns about missing `inputs` properties
- Provides detailed error messages with:
  - Specific nodes that have issues
  - What properties are missing
  - How to fix the problem

**Impact:** Users now get clear, actionable error messages when loading custom workflows, making debugging much easier.

---

## ✨ New Features

### Intelligent Workflow Validation
The new validation system checks custom workflows for:

1. **Required Properties:**
   - Each node must have a `class_type` property
   - Each node must have an `inputs` property
   - Workflow must be properly structured

2. **Helpful Error Messages:**
   - Lists up to 5 problematic nodes
   - Shows exactly what's wrong with each node
   - Provides common solutions

3. **Export Format Guidance:**
   - Explains the difference between UI and API format
   - Tells users to use "Save (API Format)" in ComfyUI
   - Includes example of correct node structure

### Example Error Output
```
Workflow 'custom_workflow' has 2 invalid node(s):
  - Node #1: Missing required 'class_type' property
  - Node #5: Node is not a dictionary (got str)

Common issues:
  1. Each node must have a 'class_type' property specifying the ComfyUI node type
  2. Each node must have an 'inputs' property (can be empty dict)
  3. Workflow must be exported from ComfyUI as API format (not the UI format)

To fix: In ComfyUI, use 'Save (API Format)' instead of regular 'Save' when exporting workflows.
```

---

## 📝 Technical Details

### Changes in `bot.py`
**Line 823:** Fixed LoRA selector initialization
```python
# Before:
self.insert_item(1, LoRASelectMenu(self.loras, self.selected_lora))

# After:
self.children.insert(1, LoRASelectMenu(self.loras, self.selected_lora))
```

### Changes in `image_gen.py`
**New Method:** `_validate_workflow()` (Lines 438-511)
- Validates workflow structure before loading
- Checks each node for required properties
- Provides detailed error messages with solutions

**Updated Method:** `_load_workflow()` (Line 429)
- Now calls `_validate_workflow()` after loading JSON
- Catches validation errors early before sending to ComfyUI

---

## 🚀 Upgrade Instructions

### From v1.3.0

1. **Pull Latest Changes:**
   ```bash
   cd discomfy
   git pull origin main
   git checkout v1.3.1
   ```

2. **Restart Bot:**
   ```bash
   python bot.py
   ```

### No Configuration Changes Required
- No changes to `config.json` needed
- No new dependencies
- Backward compatible with all existing workflows
- All previous features remain unchanged

---

## 📚 Custom Workflow Guide

### How to Create Custom Workflows

1. **Design Your Workflow in ComfyUI:**
   - Build your workflow as usual in ComfyUI
   - Test it to ensure it works correctly

2. **Export in API Format:**
   - Click the menu in ComfyUI
   - Choose **"Save (API Format)"** (NOT regular "Save")
   - Save to your `discomfy/workflows/` directory

3. **Verify Node Structure:**
   Each node should look like this:
   ```json
   {
     "1": {
       "inputs": {
         "image": "input.png"
       },
       "class_type": "LoadImage",
       "_meta": {
         "title": "Load Image"
       }
     }
   }
   ```

4. **Add to Config (Optional):**
   If you want to use it as a default workflow, add it to `config.json`:
   ```json
   {
     "workflows": {
       "my_custom_workflow": {
         "enabled": true,
         "name": "My Custom Workflow",
         "file": "my_custom_workflow.json",
         "description": "My custom workflow description"
       }
     }
   }
   ```

---

## 🎯 Impact

This release significantly improves the user experience for custom workflows:

- ✅ **Clear Error Messages:** Know exactly what's wrong and how to fix it
- ✅ **Early Validation:** Catch errors before sending to ComfyUI
- ✅ **Better Documentation:** Inline guidance for proper workflow format
- ✅ **Reduced Debugging Time:** Get actionable feedback immediately
- ✅ **More Reliable:** LoRA selector works consistently

---

## 🙏 Acknowledgments

Special thanks to [@AyoKeito](https://github.com/AyoKeito) for reporting these issues in [Issue #1](https://github.com/jmpijll/discomfy/issues/1) and providing helpful debug information!

---

## 📚 Documentation

- Full documentation: [README.md](README.md)
- Changelog: [CHANGELOG.md](CHANGELOG.md)
- Known Issues: [KNOWN_ISSUES.md](KNOWN_ISSUES.md)
- Report Issues: [GitHub Issues](https://github.com/jmpijll/discomfy/issues)

---

**DisComfy v1.3.1 - More Reliable Custom Workflow Support**

*Questions or issues? Open an issue on [GitHub](https://github.com/jmpijll/discomfy/issues)*

