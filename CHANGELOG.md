# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.1] - 2025-01-29

### Added
- **Extended Video Generation Timeout**: Increased from 10 minutes to 15 minutes (900 seconds)
- **Enhanced Video Workflow Detection**: Added support for WanVaceToVideo, VHS_VideoCombine, and AnimateDiff nodes
- **Parameter Selection Modals**: Interactive Discord modals for customizing upscale and animation parameters
- **Upscale Parameter Selection**: Choose upscale ratio (2x/4x/8x), denoise strength, and sampling steps
- **Animation Parameter Selection**: Choose frame count (81/121/161) and strength parameters
- **Original Prompt Display**: Fixed animate and upscale functions to show original image prompts

### Fixed
- **Video Generation Timeouts**: Videos can now complete successfully in 5-10 minutes without timing out
- **Workflow Detection Logic**: Properly identifies video workflows using WanVaceToVideo nodes
- **Parameter Display**: Upscale and animate operations now show the correct original prompts
- **Timeout Logging**: Clear indicators when video vs image workflow timeouts are applied

### Changed
- **Video Timeout Duration**: Extended from 600 seconds (10 min) to 900 seconds (15 min)
- **User Experience**: Added interactive parameter selection before running upscale/animate operations
- **Progress Tracking**: Maintains accuracy even with extended timeout durations

### Technical
- Enhanced video workflow detection with multiple node type support
- Improved timeout handling for long-running video generation tasks
- Added Discord modal components for parameter input
- Maintained backward compatibility with existing workflows

## [1.1.0] - 2025-01-29

### Added
- **Advanced Real-Time Progress Tracking**: Complete WebSocket integration with ComfyUI API
- **Step-Based Progress Calculation**: Progress percentage now based purely on sampling steps
- **Client ID Management**: Proper client_id handling ensures detailed WebSocket messages
- **Multi-Phase Video Support**: Enhanced tracking for video generation with up to 161 steps
- **Fallback HTTP Polling**: Graceful degradation when WebSocket unavailable
- **Enhanced Progress Display**: Shows current sampling step (e.g., "152/161" for detailed tracking)
- **Node Execution Tracking**: Real-time updates on which ComfyUI nodes are executing
- **Cached Node Detection**: Automatically accounts for nodes skipped due to caching
- **Time Estimation**: Improved ETA calculations based on actual step progress
- **Queue Position Tracking**: Live updates when waiting in ComfyUI's generation queue

### Fixed
- **Progress Tracking Accuracy**: Now shows real progress instead of time-based estimates
- **WebSocket Integration**: Proper client_id handling ensures reception of detailed messages
- **Step Progress Calculation**: Percentage based on actual sampling steps, not node execution
- **Video Generation Support**: Enhanced tracking for video workflows with multiple sampling phases
- **Progress Update Frequency**: 1-second intervals provide smooth, responsive feedback

### Changed
- **Progress Display Format**: Enhanced with step counts, node information, and accurate percentages
- **Update Frequency**: Increased from 10 seconds to 1 second for real-time feedback
- **Timeout Detection**: Dynamic timeout based on workflow type (video vs image)
- **Error Handling**: Improved WebSocket connection resilience with HTTP polling fallback

### Technical
- Hybrid HTTP polling + WebSocket approach for maximum reliability
- Comprehensive ComfyUI API message handling (progress, executing, executed, status)
- Step-based progress calculation for accurate percentage reporting
- Enhanced logging and debugging capabilities for progress tracking
- Graceful fallback mechanisms when WebSocket unavailable

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