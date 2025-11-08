# Welcome to DisComfy Wiki! 🎨

**DisComfy** is the most advanced Discord bot for AI image and video generation, seamlessly integrating ComfyUI with Discord to bring professional-grade AI art creation to your server.

**Current Version:** v2.0.0  
**Status:** Production Ready  
**Repository:** [github.com/jmpijll/discomfy](https://github.com/jmpijll/discomfy)

---

## 📚 Documentation Navigation

### Getting Started
- **[[Getting Started]]** - Quick setup guide to get running in minutes
- **[[Installation Guide]]** - Complete installation instructions (Standard, Docker, Unraid)
- **[[Configuration Guide]]** - Detailed configuration and customization
- **[[Migration Guide]]** - Upgrading from v1.4.0 to v2.0.0

### Using DisComfy
- **[[User Guide]]** - Complete guide to all bot features and commands
- **[[Features]]** - Detailed feature documentation
- **[[Usage Examples]]** - Practical examples and use cases
- **[[Custom Workflows]]** - Creating and using custom ComfyUI workflows

### Development
- **[[Developer Guide]]** - Integrating new features and workflows
- **[[API Reference]]** - Technical API documentation
- **[[Testing Guide]]** - Running and writing tests
- **[[Contributing]]** - How to contribute to the project

### Reference
- **[[Troubleshooting]]** - Common issues and solutions
- **[[FAQ]]** - Frequently asked questions
- **[[Known Issues]]** - Current limitations and workarounds
- **[[Changelog]]** - Version history and release notes

---

## 🎉 What's New in v2.0.0 - Major Architectural Overhaul

### Architecture
- 🏗️ **Complete Refactor**: Transformed from monolithic to modular architecture
- 📦 **Organized Structure**: `bot/`, `core/`, `config/`, `utils/` directories
- 📉 **77% Size Reduction**: Max file size reduced from 3,508 → 705 lines
- 🔧 **50+ Modules**: Well-organized files with clear separation of concerns

### Code Quality
- ✅ **85/86 Tests Passing**: 99% test pass rate with comprehensive coverage
- 📝 **Best Practices**: Following Context7 patterns for discord.py and aiohttp
- 🔒 **Type Safety**: Full Pydantic V2 migration with type hints
- 🎨 **Design Patterns**: Strategy, ABC, Factory, Repository patterns

### Features
- 🚀 **All Commands Refactored**: `/generate`, `/editflux`, `/editqwen`, `/status`, `/help`, `/loras`
- 🎯 **Simplified Architecture**: Cleaner generators and validators
- 📊 **Better Progress Tracking**: Improved accuracy and display
- 🐳 **Docker Optimized**: Auto-publish to GHCR and Docker Hub

### Backward Compatibility
- 💯 **100% Compatible**: No breaking changes from v1.4.0
- 🔄 **Smooth Migration**: Old entry points still work
- ⚙️ **No Config Changes**: Existing configuration compatible

See the full [Release Notes](https://github.com/jmpijll/discomfy/blob/main/RELEASE_NOTES.md) for details.

---

## 🌟 Key Features

### 🎨 AI Image Generation
- Multiple AI models (Flux, Flux Krea, HiDream)
- LoRA support with dynamic loading
- Batch generation capabilities
- Full parameter customization (width, height, steps, CFG, seed)

### ✏️ Advanced Image Editing
- **Flux Kontext** - High-quality editing (10-50 steps)
- **Qwen 2.5 VL** - Ultra-fast editing (4-20 steps)
- Natural language editing prompts
- Direct upload support

### 🔍 Image Upscaling
- Multiple ratios (2x, 4x, 8x magnification)
- AI-powered super-resolution
- Customizable denoise strength and steps
- Original prompt preservation

### 🎬 Video Generation
- High-quality MP4 animation from images
- Custom animation prompts
- Multiple frame counts (81, 121, 161 frames)
- Extended timeout support (15 minutes)

### 📊 Real-Time Progress Tracking
- Step-based progress calculation
- WebSocket integration with ComfyUI
- Queue position monitoring
- Detailed node execution tracking

### ⚙️ Interactive User Experience
- Parameter selection modals
- Universal button access (anyone can use any generation's buttons)
- Buttons never expire
- Smart rate limiting

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- ComfyUI instance (local or remote)
- Discord Bot Token

### Installation

```bash
# Clone repository
git clone https://github.com/jmpijll/discomfy.git
cd discomfy

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure
cp config.example.json config.json
# Edit config.json with your Discord token and ComfyUI URL

# Run
python main.py
```

See **[[Getting Started]]** for detailed instructions.

---

## 🐳 Docker Quick Start

**Pre-built images available from GHCR and Docker Hub:**

```bash
# Pull from GitHub Container Registry
docker pull ghcr.io/jmpijll/discomfy:latest

# Or pull from Docker Hub
docker pull jamiehakker/discomfy:latest

# Run
docker run -d \
  --name discomfy \
  -e DISCORD_TOKEN=your_token \
  -e COMFYUI_URL=http://your-comfyui-url:8188 \
  -v $(pwd)/outputs:/app/outputs \
  ghcr.io/jmpijll/discomfy:latest
```

See **[[Installation Guide]]** for Docker Compose and Unraid setup.

---

## 📖 Popular Wiki Pages

1. **[[Getting Started]]** - Start here if you're new!
2. **[[User Guide]]** - Learn all the features
3. **[[Installation Guide]]** - Complete setup instructions
4. **[[Usage Examples]]** - Practical command examples
5. **[[Troubleshooting]]** - Fix common issues
6. **[[Migration Guide]]** - Upgrade from v1.4.0
7. **[[API Reference]]** - Developer documentation

---

## 🎯 System Requirements

### Minimum
- Python 3.8+
- 4GB RAM
- ComfyUI instance
- Discord Bot Token

### Recommended
- Python 3.10+
- 8GB+ RAM
- Local ComfyUI with GPU
- SSD storage for fast I/O

---

## 🤝 Community & Support

### Need Help?
1. Check the **[[FAQ]]** for common questions
2. Browse **[[Troubleshooting]]** for solutions
3. Search existing [GitHub Issues](https://github.com/jmpijll/discomfy/issues)
4. Create a new issue with detailed information

### Want to Contribute?
- See **[[Contributing]]** guide
- Check **[[Developer Guide]]** for technical details
- Review **[[Testing Guide]]** for testing procedures
- Read **[[API Reference]]** for architecture details

---

## 📊 Project Statistics

- **Code Size Reduction**: 77% (v1.4.0 → v2.0.0)
- **Test Coverage**: 85/86 tests passing (99%)
- **Documentation**: 24+ comprehensive guides
- **Modules**: 50+ well-organized files
- **Backward Compatible**: 100%

---

## 🔗 Quick Links

- **[GitHub Repository](https://github.com/jmpijll/discomfy)**
- **[Latest Release](https://github.com/jmpijll/discomfy/releases/latest)**
- **[Docker Hub](https://hub.docker.com/r/jamiehakker/discomfy)**
- **[GHCR Package](https://github.com/jmpijll/discomfy/pkgs/container/discomfy)**
- **[Changelog](https://github.com/jmpijll/discomfy/blob/main/CHANGELOG.md)**
- **[Report Issues](https://github.com/jmpijll/discomfy/issues)**

---

## 📝 About This Wiki

This wiki provides comprehensive documentation for DisComfy v2.0, including:
- Installation and configuration guides
- User tutorials and examples
- Developer documentation and API references
- Testing and contribution guidelines
- Troubleshooting resources and FAQs

Navigate using the links above or use the sidebar to browse all pages.

---

**🎨 Ready to create amazing AI art? Start with the [[Getting Started]] guide!**
