# 🎨 DisComfy - Professional Discord ComfyUI Bot

**The most advanced Discord bot for AI image and video generation!** DisComfy seamlessly integrates with ComfyUI to bring professional-grade AI art generation directly to your Discord server. Create stunning visuals, upscale images, and generate videos with real-time progress tracking and interactive parameter selection.

**🚀 Current Version**: v1.2.0  
**📂 Repository**: [https://github.com/jmpijll/discomfy.git](https://github.com/jmpijll/discomfy.git)  
**🎯 Status**: Production Ready

---

## 🌟 Why Choose DisComfy?

DisComfy isn't just another AI bot - it's a complete creative powerhouse that brings the full capabilities of ComfyUI to Discord with an intuitive, user-friendly interface. Whether you're an artist, content creator, or AI enthusiast, DisComfy makes it incredibly easy to create stunning visuals right in your Discord server.

### 🔥 **Key Highlights:**
- **Real-time Progress Tracking** with step-by-step updates
- **Interactive Parameter Selection** for complete customization
- **Custom Animation Prompts** - modify how your images animate
- **Advanced Image Editing** with natural language prompts
- **Extended Video Generation** with 15-minute timeout support
- **Professional-grade Quality** using ComfyUI workflows
- **Community Friendly** - anyone can use any generation's buttons
- **Zero Downtime** - buttons never expire, unlimited usage

---

## ✨ Core Features

### 🎨 **AI Image Generation**
- **High-Quality Output**: Generate stunning images using advanced ComfyUI workflows
- **Multiple Models**: Support for Flux, HiDream, and custom workflows
- **LoRA Integration**: Dynamic LoRA loading with customizable strength
- **Flexible Parameters**: Control width, height, steps, CFG, batch size, and seed
- **Batch Generation**: Create multiple images in a single request

### 🔍 **Advanced Image Upscaling**
- **Multiple Ratios**: Choose between 2x, 4x, or 8x magnification
- **AI Super-Resolution**: Professional-grade upscaling using ComfyUI
- **Customizable Parameters**: Adjust denoise strength and sampling steps
- **Interactive Selection**: Discord modals for parameter customization
- **Original Prompt Preservation**: Automatically uses original image prompts

### 🎬 **Professional Video Generation**
- **High-Quality Animation**: Convert images to smooth MP4 videos
- **Custom Animation Prompts**: Modify how your images animate with natural language
- **Pre-filled Defaults**: Original prompts auto-filled, edit as needed
- **Multiple Frame Counts**: Choose 81, 121, or 161 frames for different lengths
- **Extended Timeout**: 15-minute timeout supports complex video workflows
- **Interactive Settings**: Customize strength, steps, and frame count via modal
- **Real-time Progress**: Track every step of video generation

### ✏️ **Advanced Image Editing**
- **Natural Language Editing**: Describe changes in plain English
- **Flux Kontext Integration**: Powered by advanced editing workflows
- **Direct Upload Support**: Edit any image with `/edit` command
- **Post-Generation Editing**: Edit button available on all generated images
- **Customizable Parameters**: Adjust sampling steps for quality control

### 📊 **Real-Time Progress Tracking**
- **Step-Based Accuracy**: Progress calculated from actual sampling steps, not time estimates
- **WebSocket Integration**: Real-time updates directly from ComfyUI
- **Detailed Information**: See current node, step progress, and time estimates
- **Queue Monitoring**: Live updates when waiting in ComfyUI's queue
- **Fallback Support**: Graceful degradation to HTTP polling when needed

### ⚙️ **Interactive User Experience**
- **Parameter Selection Modals**: Customize settings before generation starts
- **Universal Button Access**: Anyone can use action buttons on any generation
- **Infinite Usage**: Buttons never expire and can be used multiple times
- **Smart Rate Limiting**: Prevents abuse while allowing normal usage
- **Error Handling**: Robust error recovery and user-friendly messages

### 🛡️ **Production-Ready Features**
- **Automatic File Management**: Intelligent cleanup of old outputs
- **Concurrent Request Handling**: Multiple users can generate simultaneously
- **Session Management**: Proper HTTP session handling with connection pooling
- **Security**: Input validation, rate limiting, and secure file handling
- **Comprehensive Logging**: Detailed logs for debugging and monitoring

---

## 🚀 Real-Time Progress Tracking

DisComfy features advanced progress tracking that provides detailed information about your generation:

### 📈 **Progress Display:**
```
🎬 Generating Video
📊 87.5% ████████████████████░░░
🔄 Sampling (315/321)
⏱️ Elapsed: 4m 32s | ETA: 42s
🎯 Node: WanVaceToVideo
Settings: 720x720 | 161 frames | Strength: 0.7
```

### 🔧 **Technical Features:**
- **WebSocket Integration**: Direct connection to ComfyUI for real-time updates
- **Step-Based Calculation**: Accurate progress based on actual sampling steps
- **Node Execution Tracking**: See which ComfyUI nodes are currently running
- **Cached Node Detection**: Automatically accounts for skipped nodes
- **Multi-Phase Support**: Handles complex workflows with multiple sampling stages
- **Automatic Fallback**: HTTP polling when WebSocket unavailable

---

## ⚙️ Interactive Parameter Selection

Take full control of your generations with interactive Discord modals:

### 🔍 **Upscale Customization:**
- **Upscale Ratio**: 2x, 4x, or 8x magnification
- **Denoise Strength**: 0.1 - 1.0 for detail enhancement
- **Sampling Steps**: 10-50 steps for quality control

### 🎬 **Video Customization:**
- **Frame Count**: 81, 121, or 161 frames (2-5 second videos)
- **Animation Strength**: 0.1 - 1.0 for intensity control
- **Quality Settings**: Fine-tune your video output

### 🎯 **Smart Defaults:**
- Pre-filled with sensible defaults
- Input validation prevents errors
- Real-time parameter descriptions
- Original prompts automatically preserved

---

## 🚀 Quick Start Guide

### **Prerequisites:**
- Python 3.8+ installed
- ComfyUI running locally or remotely
- Discord Bot Token
- Basic command line knowledge

### **1. Clone & Setup:**
```bash
git clone https://github.com/jmpijll/discomfy.git
cd discomfy
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

pip install -r requirements.txt
```

### **2. Configure Bot:**
```bash
cp config.example.json config.json
# Edit config.json with your Discord token and ComfyUI URL
```

**Example config.json:**
```json
{
  "discord": {
    "token": "YOUR_DISCORD_BOT_TOKEN",
    "guild_id": "YOUR_SERVER_ID"
  },
  "comfyui": {
    "url": "http://localhost:8188",
    "timeout": 300
  },
  "generation": {
    "default_workflow": "flux_lora",
    "max_batch_size": 4,
    "output_limit": 100
  }
}
```

### **3. Discord Bot Setup:**
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create new application → Bot
3. Copy bot token to config.json
4. Invite bot with permissions: `Send Messages`, `Use Slash Commands`, `Attach Files`, `Embed Links`

### **4. Prepare ComfyUI:**
- Ensure ComfyUI is running: `http://your-comfyui-url/system_stats`
- Place workflow JSON files in `workflows/` folder
- Install required models and LoRAs

### **5. Launch Bot:**
```bash
python bot.py
```

**Success Output:**
```
🤖 Bot is starting up...
✅ Connected to Discord as DisComfy#0430
🎨 ComfyUI connection verified
🚀 Bot is ready! Use /generate to start creating!
```

---

## 📖 Usage Examples

### **Basic Image Generation:**
```
/generate prompt:a majestic dragon soaring through clouds
```

### **Image Editing:**
```
/edit image:photo.jpg prompt:add sunglasses and a hat steps:25
```

### **Advanced Parameters:**
```
/generate prompt:cyberpunk cityscape at night width:1024 height:768 steps:30 cfg:7.5 batch_size:2
```

### **Using LoRAs:**
```
/generate prompt:anime character in magical forest lora:anime_style_v2 lora_strength:0.8
```

### **Post-Generation Actions:**
1. Generate an image with `/generate`
2. Click 🔍 **Upscale** → Choose 4x ratio, adjust settings
3. Click 🎬 **Animate** → Select 161 frames, set strength
4. Anyone can use these buttons on any generation!

---

## 🔧 Advanced Configuration

### **Custom Workflows:**
Add your ComfyUI workflows to the `workflows/` folder and configure them in `config.json`:

```json
"workflows": {
  "my_custom_workflow": {
    "file": "my_workflow.json",
    "name": "Custom Style",
    "description": "My custom ComfyUI workflow",
    "enabled": true
  }
}
```

### **Performance Tuning:**
- **Image Generation**: ~30 seconds average
- **Video Generation**: 2-10 minutes (15-minute timeout)
- **Upscaling**: ~45 seconds average
- **Concurrent Users**: Fully supported
- **Memory Usage**: Auto-cleanup after 100 files

---

## 🛠️ Troubleshooting

### **Common Issues:**

**Bot won't start:**
- Verify Discord token in config.json
- Check bot permissions in Discord server
- Ensure Python 3.8+ is installed

**ComfyUI connection failed:**
- Verify ComfyUI is running: visit URL in browser
- Check firewall settings
- Ensure correct URL in config.json

**Generation fails:**
- Check ComfyUI logs for errors
- Verify required models are installed
- Try simpler parameters first

**Timeout errors:**
- Video generation can take up to 15 minutes
- Check ComfyUI system resources
- Consider reducing batch sizes

### **Getting Help:**
1. Check logs in `logs/bot.log`
2. Verify ComfyUI system stats
3. Test with simple generations first
4. Join our Discord community for support

---

## 📁 Project Structure

```
discomfy/
├── bot.py                 # Main Discord bot
├── image_gen.py          # Image generation engine  
├── video_gen.py          # Video generation engine
├── config.py             # Configuration management
├── requirements.txt      # Python dependencies
├── config.json          # Bot configuration
├── workflows/           # ComfyUI workflow files
│   ├── flux_lora.json
│   ├── hidream_lora.json
│   ├── upscale_config-1.json
│   └── video_wan_vace_14B_i2v.json
├── outputs/             # Generated files
├── logs/               # Bot logs
├── README.md          # This file
├── CHANGELOG.md       # Version history
├── GUIDELINES.md      # Development guidelines
└── PROJECT_PLAN.md    # Project roadmap
```

---

## 🎯 System Requirements

### **Minimum:**
- Python 3.8+
- 4GB RAM
- ComfyUI instance
- Discord Bot Token

### **Recommended:**
- Python 3.10+
- 8GB+ RAM
- Local ComfyUI with GPU
- SSD storage for fast I/O

### **Performance:**
- **Uptime**: >99% reliability
- **Response Time**: <30s images, <10min videos
- **Concurrent Users**: Unlimited
- **File Management**: Automatic cleanup
- **Error Recovery**: Graceful handling

---

## 🤝 Contributing

We welcome contributions! Here's how to get started:

1. **Fork the repository**
2. **Create feature branch**: `git checkout -b feature/amazing-feature`
3. **Follow guidelines**: Check `GUIDELINES.md`
4. **Test thoroughly**: Ensure all features work
5. **Submit PR**: With detailed description

### **Development Guidelines:**
- Follow modular architecture
- Add comprehensive error handling
- Include type hints and docstrings
- Test with real ComfyUI workflows
- Update documentation

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **ComfyUI Team** - For the amazing AI generation framework
- **Discord.py Developers** - For the excellent Discord library  
- **AI Art Community** - For inspiration and feedback
- **Contributors** - Everyone who helps improve DisComfy

---

## 🆘 Support

**Need help?** Here's how to get support:

1. **📖 Check Documentation** - Most issues are covered here
2. **🔍 Search Issues** - Someone may have had the same problem
3. **🐛 Report Bugs** - Create detailed issue reports
4. **💬 Join Community** - Get help from other users
5. **📧 Contact Maintainers** - For complex issues

---

**🎨 Ready to create amazing AI art? Install DisComfy and let your creativity flow! ✨**

---

*DisComfy v1.1.1 - The Professional Discord ComfyUI Bot*