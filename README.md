# 🎨 DisComfy - Discord AI Art Bot

**Version 2.2.0** | Advanced AI Image & Video Generation for Discord

**The most advanced Discord bot for AI image and video generation!** DisComfy seamlessly integrates with ComfyUI to bring professional-grade AI art generation directly to your Discord server. Create stunning visuals, upscale images, and generate videos with real-time progress tracking and interactive parameter selection.

**🚀 Current Version**: v2.2.0
**📂 Repository**: [https://github.com/jmpijll/discomfy.git](https://github.com/jmpijll/discomfy.git)
**🎯 Status**: Production Ready

### 🎉 What's New - Qwen Image 2512 Model

- 🧠 **NEW Model**: Qwen Image 2512 - High-quality text-to-image with built-in hi-res fix
- 🔬 **Hi-Res Fix Pipeline**: 1.5x latent upscale with dedicated refinement pass
- 📐 **Portrait Optimized**: Default 1296x1728 (3:4 ratio)
- ✨ **LoRA Support**: Compatible with Qwen Image 2512 LoRAs
- ⚡ **Fast Generation**: Only 8 steps at CFG 0.8 for the initial pass
- 🔧 **Workflow Enable/Disable**: Control models via environment variables

### 📝 Previous Releases

**v2.1.2 - ZI Turbo Model:**
- ⚡ ZI Turbo ultra-fast turbo generation
- 🔥 Only 10 steps with CFG 1.0 for rapid generation
- 🛠️ KSamplerAdvanced workflow updater

**v2.1.0 - Ultra High-Resolution Support:**
- 🚀 DyPE Flux Krea model with 4K resolution support
- 📐 Dynamic Position Encoding technology
- ⚙️ Adjustable DyPE exponent control

**v2.0.0 - Architectural Overhaul:**
- 🏗️ Complete modular architecture (77% code size reduction)
- ✅ 85/86 tests passing (99% pass rate)
- 📚 24+ comprehensive documentation guides
- 🐳 Docker support with GHCR and Docker Hub

**See [RELEASE_NOTES.md](RELEASE_NOTES.md) for complete details.**

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
- **Multiple Models**: Support for Flux, Flux Krea, DyPE Flux Krea (4K), ZI Turbo, **Qwen Image 2512 🧠 NEW**, HiDream, and custom workflows
- **Hi-Res Fix Pipeline**: Qwen Image 2512 features a built-in 1.5x latent upscale with refinement pass
- **Ultra High-Resolution**: DyPE Flux Krea supports resolutions up to 4096x4096 with advanced position encoding
- **LoRA Integration**: Dynamic LoRA loading with customizable strength
- **Flexible Parameters**: Control width, height, steps, CFG, batch size, DyPE exponent, and seed
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
- **Dual Editing Models**: Choose between Flux Kontext or Qwen 2.5 VL for editing
- **Natural Language Editing**: Describe changes in plain English
- **Flux Kontext**: High-quality editing with 10-50 steps (slower, more detailed)
- **Qwen 2.5 VL**: Ultra-fast editing with 4-20 steps (faster, efficient)
- **Multi-Image Qwen Editing**: NEW in v1.3.0 - Edit with 1, 2, or 3 input images
- **Direct Upload Support**: Edit any image with `/editflux` or `/editqwen` commands
- **Post-Generation Editing**: Both edit buttons available on all generated images
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

## 🐳 Docker Quick Start

DisComfy is available as a pre-built Docker container from both GitHub Container Registry (ghcr.io) and Docker Hub.

### **Using the Pre-built Image:**

**From GitHub Container Registry:**
```bash
# Pull the latest image
docker pull ghcr.io/jmpijll/discomfy:latest

# Or pull a specific version
docker pull ghcr.io/jmpijll/discomfy:v2.2.0
```

**From Docker Hub:**
```bash
# Pull the latest image
docker pull jamiehakker/discomfy:latest

# Or pull a specific version
docker pull jamiehakker/discomfy:v2.2.0
```

### **Running with Docker:**

```bash
docker run -d \
  --name discomfy \
  -v $(pwd)/config.json:/app/config.json:ro \
  -v $(pwd)/workflows:/app/workflows:ro \
  -v $(pwd)/outputs:/app/outputs \
  -v $(pwd)/logs:/app/logs \
  -e DISCORD_TOKEN=your_discord_token \
  -e COMFYUI_URL=http://your-comfyui-url:8188 \
  ghcr.io/jmpijll/discomfy:latest
```

### **Docker Compose Example:**

Create a `docker-compose.yml`:

```yaml
version: '3.8'

services:
  discomfy:
    # Use either:
    # image: ghcr.io/jmpijll/discomfy:latest
    # or:
    image: jamiehakker/discomfy:latest
    container_name: discomfy
    restart: unless-stopped
    volumes:
      - ./config.json:/app/config.json:ro
      - ./workflows:/app/workflows:ro
      - ./outputs:/app/outputs
      - ./logs:/app/logs
    environment:
      - DISCORD_TOKEN=${DISCORD_TOKEN}
      - COMFYUI_URL=${COMFYUI_URL:-http://localhost:8188}
    env_file:
      - .env
```

Then run:
```bash
docker-compose up -d
```

### **Building from Source:**

```bash
# Clone the repository
git clone https://github.com/jmpijll/discomfy.git
cd discomfy

# Build the Docker image
docker build -t discomfy:local .

# Run the container
docker run -d --name discomfy \
  -v $(pwd)/config.json:/app/config.json:ro \
  ghcr.io/jmpijll/discomfy:local
```

**Note:** Make sure your `config.json` and `workflows/` directory are accessible to the container, and that `outputs/` and `logs/` directories exist for the container to write to.

---

## 📖 Usage Examples

### **Basic Image Generation:**
```
/generate prompt:a majestic dragon soaring through clouds
```

### **Image Editing (Flux Kontext - High Quality):**
```
/editflux image:photo.jpg prompt:add sunglasses and a hat steps:25
```

### **Image Editing (Qwen - Ultra Fast):**
```
/editqwen image:photo.jpg prompt:add sunglasses and a hat steps:8
```

### **Multi-Image Qwen Editing (NEW in v1.3.0):**
```
# Single image (default)
/editqwen image:photo.jpg prompt:enhance the lighting steps:8

# Two images
/editqwen image:photo1.jpg image2:photo2.jpg prompt:combine both styles steps:8

# Three images
/editqwen image:photo1.jpg image2:photo2.jpg image3:photo3.jpg prompt:merge all three steps:8
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
3. Click ✏️ **Flux Edit** → High-quality editing with Flux Kontext
4. Click ⚡ **Qwen Edit** → Ultra-fast editing with Qwen 2.5 VL
5. Click 🎬 **Animate** → Select 161 frames, set strength
6. Anyone can use these buttons on any generation!

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

### **Enable/Disable Workflows:**
Control which models and features are available via environment variables:

```bash
# In your .env file
WORKFLOW_HIDREAM_LORA_ENABLED=false
WORKFLOW_VIDEO_WAN_VACE_14B_I2V_ENABLED=false
```

All workflows are enabled by default. This is useful for:
- Retiring old models
- Reducing server load
- Testing specific features
- Maintenance mode

See [Workflow Management Guide](docs/WORKFLOW_MANAGEMENT.md) for complete details

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
│   ├── flux_krea_lora.json    # Enhanced Flux Krea model
│   ├── dype-flux-krea-lora.json # DyPE 4K model
│   ├── ZITURBO1.json          # ZI Turbo fast generation
│   ├── qwen_image_2512_lora.json # Qwen Image 2512 with hi-res fix
│   ├── flux_kontext_edit.json # Flux Kontext editing
│   ├── qwen_image_edit.json   # Qwen 2.5 VL fast editing (1 image)
│   ├── qwen_image_edit_2.json # Qwen 2.5 VL multi-image (2 images)
│   ├── qwen_image_edit_3.json # Qwen 2.5 VL multi-image (3 images)
│   ├── hidream_lora.json
│   ├── upscale_config-1.json
│   └── video_wan_vace_14B_i2v.json
├── outputs/             # Generated files
├── logs/               # Bot logs
├── README.md          # This file
├── CHANGELOG.md       # Version history
├── KNOWN_ISSUES.md    # Known issues and limitations
├── docs/              # Documentation
│   ├── GUIDELINES.md  # Development guidelines
│   ├── PROJECT_PLAN.md # Project roadmap
│   ├── TESTING_GUIDE.md # Testing instructions
│   └── archive/       # Archived documentation
└── RELEASE_NOTES_v1.4.0.md  # Latest release notes
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

See [docs/GUIDELINES.md](docs/GUIDELINES.md) for detailed guidelines.

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

*DisComfy v2.2.0 - The Professional Discord ComfyUI Bot*

---

## 📚 Documentation

- **[README.md](README.md)** - This file (getting started, features, usage)
- **[CHANGELOG.md](CHANGELOG.md)** - Complete version history
- **[KNOWN_ISSUES.md](KNOWN_ISSUES.md)** - Known issues and limitations
- **[RELEASE_NOTES_v1.4.0.md](RELEASE_NOTES_v1.4.0.md)** - Latest release notes
- **[docs/GUIDELINES.md](docs/GUIDELINES.md)** - Development guidelines
- **[docs/PROJECT_PLAN.md](docs/PROJECT_PLAN.md)** - Project roadmap
- **[docs/TESTING_GUIDE.md](docs/TESTING_GUIDE.md)** - Testing instructions

For archived documentation and research, see [docs/archive/](docs/archive/).