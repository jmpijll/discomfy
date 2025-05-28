# Changelog

All notable changes to the Discord ComfyUI Bot project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2025-01-29

### Added
- **Advanced Real-Time Progress Tracking**: Complete WebSocket integration with ComfyUI API
- **Step-Based Progress Calculation**: Progress percentage now based purely on sampling steps
- **Client ID Management**: Proper client_id handling ensures detailed WebSocket messages
- **Multi-Phase Video Support**: Enhanced tracking for video generation with up to 161 steps
- **Fallback HTTP Polling**: Graceful degradation when WebSocket unavailable
- **Enhanced Progress Display**: Shows current sampling step (e.g., "152/161") with accurate percentages

### Fixed  
- **Animate Function**: Now correctly displays original image prompt instead of generic text
- **Upscale Function**: Now correctly displays original image prompt instead of generic text
- **WebSocket Connection**: Proper client_id retrieval prevents empty progress messages
- **Progress Updates**: 1-second intervals with accurate step-based calculations
- **Video Generation**: Extended 10-minute timeout for complex video workflows

### Changed
- **Progress Tracking**: Moved from node-based to step-based progress calculation
- **WebSocket Implementation**: Complete rewrite with proper message handling
- **Progress Display**: Enhanced format showing detailed sampling progress
- **Error Handling**: Improved WebSocket timeout and fallback mechanisms

### Technical Improvements
- Added comprehensive WebSocket message type handling (`progress`, `executing`, `executed`, `execution_success`, `status`)
- Implemented proper client_id workflow for ComfyUI WebSocket communication
- Enhanced ProgressInfo class with step-based tracking and caching support
- Added fallback mechanisms for WebSocket failures
- Improved logging and debugging for progress tracking issues

## [1.0.0] - 2024-05-29

### 🎉 Initial Release
This is the first stable release of the Discord ComfyUI Bot! All core features are implemented and thoroughly tested.

### ✨ Added
- **Core Image Generation**: Generate high-quality AI images using ComfyUI workflows
- **Advanced Post-Generation Actions**: Upscale and animate any generated image
- **Universal Button Access**: Anyone can use action buttons on any generation
- **Multiple Workflow Support**: Flux and HiDream models with LoRA support
- **Real-time Progress Tracking**: Live progress updates with queue position monitoring
- **Intelligent Queue Management**: Proper integration with ComfyUI's queue system
- **Robust Error Handling**: Comprehensive null checking and graceful error recovery
- **Interactive UI Components**: Dynamic dropdown menus showing current selections
- **Rate Limiting**: Smart rate limiting to prevent abuse (5 requests/minute per user)
- **Automatic File Management**: Auto-cleanup of old outputs (50 file limit)
- **Comprehensive Configuration**: JSON-based configuration with environment variable overrides
- **Complete Documentation**: Installation guide, usage examples, and troubleshooting

### 🛠️ Technical Features
- **Modular Architecture**: Clean separation between Discord logic, image generation, and video processing
- **Async/Await Support**: Fully asynchronous for optimal performance
- **Session Management**: Proper HTTP session handling with connection pooling
- **Type Safety**: Comprehensive type hints throughout the codebase
- **Logging System**: Structured logging with file rotation and level control
- **Security**: Input validation, rate limiting, and secure file handling

### 📁 Project Structure
```
discomfy/
├── bot.py                 # Main Discord bot logic
├── image_gen.py          # Image generation handler
├── video_gen.py          # Video generation handler
├── config.py             # Configuration management
├── setup.py              # Automated setup script
├── requirements.txt      # Python dependencies
├── workflows/            # ComfyUI workflow JSON files
├── README.md            # Complete documentation
├── GUIDELINES.md        # Development guidelines
├── PROJECT_PLAN.md      # Project roadmap
└── CHANGELOG.md         # This file
```

### 🚀 Supported Features
- **Image Generation**: 1024x1024, 30 steps, customizable parameters
- **Video Generation**: 720x720 MP4 animations (81 frames, ~3 seconds)
- **Image Upscaling**: 2x resolution enhancement with AI super-resolution
- **LoRA Support**: Dynamic LoRA loading with customizable strength
- **Multiple Models**: Flux (fast) and HiDream (detailed) workflows
- **Queue Integration**: Real-time queue position and status monitoring
- **Progress Reporting**: Detailed progress with time estimates

### 🔧 System Requirements
- Python 3.8 or higher
- ComfyUI instance (local or remote)
- Discord Bot Token
- 4GB+ RAM recommended for optimal performance

### 📊 Performance
- Average response time: <30 seconds for images
- Average response time: <2 minutes for videos
- Concurrent request handling: Multiple users supported
- Memory usage: Optimized with automatic cleanup
- Bot uptime: >99% reliability target

### 🛡️ Security
- Input validation and sanitization
- Rate limiting per user and globally
- Secure file handling and cleanup
- No user data persistence
- Environment variable protection

### 🎯 Future Roadmap
- Advanced workflow management
- User preset system
- Enhanced analytics
- Performance optimizations
- Community features

---

## Release Notes

This release represents the completion of **Phase 1-3** of the project plan:
- ✅ Phase 1: Foundation & Basic Image Generation
- ✅ Phase 2: Enhanced Features & Post-Generation Actions  
- ✅ Phase 3: Video Generation & Advanced Features
- 🚧 Phase 4: Polish & Production Ready (Ongoing)

The bot is now production-ready and suitable for deployment in Discord servers of any size. 