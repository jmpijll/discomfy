# 🎨 DisComfy v1.2.2: New Flux Krea Model & Dropdown Fixes

**Release Date:** January 29, 2025  
**Type:** Minor Release (New Model + Bug Fixes)

---

## 🌟 **What's New**

This release introduces the highly anticipated **Flux Krea** model and resolves critical dropdown selection issues, significantly enhancing the user experience with better model choices and improved interface reliability.

---

## ✨ **Major Features**

### 🚀 **New Flux Krea Model**
- **✨ Enhanced Creative Model**: "Flux Krea ✨ NEW" now available in model selection
- **Same LoRA Compatibility**: Uses identical LoRAs as the standard Flux model
- **Optimized Settings**: 1024x1024 resolution, 30 steps, CFG 5.0 for best results
- **Professional Quality**: Enhanced creative generation capabilities while maintaining speed
- **Seamless Integration**: Works with all existing features (upscale, animate, edit)

### 🐛 **Critical Dropdown Fixes**
- **Default Selection**: Model dropdown now shows "🤖 Flux (Default)" instead of appearing empty
- **Visual Feedback**: All model selections (including HiDream) now properly display when chosen
- **Persistent Display**: Selected model remains visible in dropdown placeholder
- **Improved UX**: No more confusion about which model is currently selected

---

## 🎯 **Model Selection Options**

Users can now choose from **3 powerful models**:

1. **🚀 Flux (Default)** - High-quality, fast generation
2. **✨ Flux Krea ✨ NEW** - Enhanced creative model with improved artistic output
3. **🎨 HiDream** - Detailed, artistic images with maximum quality

---

## 🔧 **Technical Improvements**

### **Model Integration**
- Added `flux_krea_lora.json` workflow with enhanced Flux Krea model
- Updated configuration system to support new model type
- Seamless workflow mapping: `flux_krea` → `flux_krea_lora.json`

### **LoRA System Enhancement**
- Both Flux variants share the same LoRA pool for maximum compatibility
- Updated filtering logic to recognize `flux_krea` as Flux-compatible
- Enhanced `/loras` command with "Flux Krea ✨ NEW" option
- Clear indication that LoRAs work with both Flux models

### **UI/UX Improvements**
- Fixed dropdown initialization with proper default selection
- Enhanced model display names throughout the interface
- Improved generation progress display with correct model names
- Better visual distinction between model options

---

## 📚 **Usage Examples**

### **Using the New Flux Krea Model**
1. Run `/generate prompt:mystical forest landscape`
2. Model dropdown shows: **🤖 Flux (Default)** (not empty!)
3. Click dropdown and select: **✨ Flux Krea ✨ NEW**
4. Model selection is clearly displayed and retained
5. Generate with enhanced creative capabilities

### **LoRA Compatibility**
```
/generate prompt:anime character in magical forest
# Select Flux Krea model, choose any Flux-compatible LoRA
# Same LoRAs work perfectly with both Flux variants
```

---

## 🛡️ **Compatibility & Migration**

### **Fully Backward Compatible**
- All existing workflows continue to work unchanged
- Previous model selections remain functional
- Configuration files require no updates
- Existing LoRAs work seamlessly with new model

### **Automatic Benefits**
- Users immediately see improved dropdown behavior
- New model becomes available without any setup
- Enhanced visual feedback works across all interactions

---

## 🚀 **Installation & Upgrade**

### **For New Installations**
```bash
git clone https://github.com/jmpijll/discomfy.git
cd discomfy
pip install -r requirements.txt
cp config.example.json config.json
# Edit config.json with your settings
python bot.py
```

### **For Existing Users**
```bash
git pull origin main
# No additional setup required - new model and fixes are ready!
python bot.py
```

### **No Configuration Changes Needed**
This release is fully plug-and-play. Simply update your code and enjoy the new features!

---

## 📊 **Verification Steps**

After updating, verify everything works:

1. **Dropdown Display**: `/generate` should show "🤖 Flux (Default)" immediately
2. **Model Selection**: All three models should display properly when selected
3. **New Model Access**: "✨ Flux Krea ✨ NEW" should be available and functional
4. **LoRA Compatibility**: Same LoRAs should work with both Flux variants
5. **Visual Feedback**: No more empty or confusing dropdown states

---

## 🎯 **What's Next**

This release completes the model selection enhancement roadmap. Future updates will focus on:

- Additional creative models and workflows
- Enhanced LoRA discovery and management
- Performance optimizations
- Community-requested features

---

## 🐛 **Bug Fixes**

- **Fixed**: Model dropdown no longer appears empty on initial load
- **Fixed**: HiDream selection now properly displays when chosen
- **Fixed**: Model placeholder text updates correctly with selection
- **Fixed**: Visual consistency across all model selection interfaces

---

## ⚡ **Performance**

- **Model Loading**: Flux Krea initializes as quickly as standard Flux
- **Generation Speed**: ~30 seconds average (same as Flux)
- **Memory Usage**: No additional overhead
- **Compatibility**: Works with all existing hardware setups

---

## 🙏 **Acknowledgments**

Special thanks to users who reported the dropdown selection issues and requested enhanced creative models. Your feedback drives DisComfy's continuous improvement!

---

**🎨 Experience enhanced creativity with Flux Krea and enjoy seamless model selection! ✨**

---

**Full Changelog**: [v1.2.1...v1.2.2](https://github.com/jmpijll/discomfy/compare/v1.2.1...v1.2.2)

**Download**: [Source Code (zip)](https://github.com/jmpijll/discomfy/archive/refs/tags/v1.2.2.zip) | [Source Code (tar.gz)](https://github.com/jmpijll/discomfy/archive/refs/tags/v1.2.2.tar.gz)