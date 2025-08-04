# Changelog

## [1.2.5] - 2025-01-29

### 🔧 Configuration & Setup Fixes

### Fixed
- **Missing Configuration Issue**: Fixed critical issue where users without `config.json` couldn't use any models
- **Automatic Config Creation**: Bot now automatically creates `config.json` from `config.example.json` when missing
- **Built-in Defaults**: Added fallback configuration with all three models (Flux, Flux Krea, HiDream) enabled
- **First-Time Setup**: Seamless out-of-the-box experience for new users
- **Config Migration**: Automatic workflow configuration migration for missing workflows

### Added
- **Smart Config Loading**: Enhanced configuration system with automatic setup
- **Fallback Workflows**: Built-in workflow definitions ensure models always work
- **Better Error Handling**: Improved error messages and automatic recovery

### 📋 Technical Details
- Auto-creation of `config.json` from `config.example.json`
- Built-in fallback workflow configurations for all models
- Enhanced config loading with automatic migration
- Improved first-time user experience

### 📊 Impact
This release resolves the "Selected model is not available" errors that affected users without proper configuration files, ensuring all models work immediately after installation.

## [1.2.4] - 2025-01-29

### 🐛 Critical Bug Fixes

### Fixed
- **Model Display Bug**: Fixed LoRA selection incorrectly showing "HiDream" when Flux Krea model is selected
- **Generation Display Bug**: Fixed generation setup view model display logic for all three models
- **Model Selection Logic**: All model selection now properly handles flux_krea model type
- **UI Consistency**: Ensured proper model display across all components:
  - 🚀 Flux - Standard model
  - ✨ Flux Krea ✨ NEW - Enhanced creative model
  - 🎨 HiDream - Detailed artistic model
- **Generation Errors**: Resolved "model not available" error when generating with Flux Krea

### 📋 Technical Details
- Updated LoRA selection callback model display logic
- Fixed generation setup view model display conditionals  
- Improved model type handling in workflow mapping
- Consistent model naming across all UI components

### 📊 Impact
This release fixes critical user-facing bugs that prevented proper usage of the new Flux Krea model introduced in v1.2.2.

## [1.2.3] - 2025-01-29

### 📚 Documentation Release

### Updated
- **Documentation Synchronization**: All documentation now properly reflects v1.2.3 release
- **README.md**: Updated version information and feature highlights
- **CHANGELOG.md**: Complete changelog entries for all versions
- **Release Notes**: Comprehensive release documentation available

### 📋 Notes
This is a documentation release that ensures all project documentation is properly synchronized and up-to-date with the latest Flux Krea model features and dropdown fixes introduced in v1.2.2.

## [1.2.2] - 2025-01-29

### 🚀 New Model Release: Flux Krea

### Added
- **✨ Flux Krea Model**: New "Flux Krea ✨ NEW" model available in dropdown selection
  - Enhanced creative generation capabilities with same performance as Flux
  - Uses identical LoRA compatibility as standard Flux model
  - Optimized settings: 1024x1024, 30 steps, CFG 5.0
  - Seamless integration with all existing features (upscale, animate, edit)
- **Enhanced Model Selection**: Users can now choose from 3 powerful models:
  - 🚀 Flux (Default) - High-quality, fast generation
  - ✨ Flux Krea ✨ NEW - Enhanced creative model
  - 🎨 HiDream - Detailed, artistic images
- **Workflow Integration**: Added `flux_krea_lora.json` workflow with automatic mapping

### 🐛 Bug Fixes
- **Fixed**: Model dropdown now shows "🤖 Flux (Default)" instead of appearing empty
- **Fixed**: All model selections (including HiDream) now properly display when chosen
- **Fixed**: Selected model remains visible in dropdown placeholder text
- **Fixed**: Visual consistency across all model selection interfaces

### 🔧 Technical Improvements
- **LoRA System**: Enhanced filtering logic to recognize `flux_krea` as Flux-compatible
- **Configuration**: Added `flux_krea_lora` workflow configuration to example config
- **UI/UX**: Improved dropdown initialization with proper default selection
- **Model Display**: Enhanced model names throughout progress and result displays
- **Command Integration**: Updated `/loras` command with "Flux Krea ✨ NEW" option

### 🎯 User Experience
- **Better Defaults**: Dropdown immediately shows current selection instead of blank state
- **Clear Feedback**: Enhanced visual indication of selected model across all interfaces
- **LoRA Clarity**: Updated LoRA command to show Flux LoRAs work with both Flux variants
- **Seamless Migration**: No configuration changes needed - works immediately after update

### 📋 Compatibility
- **Fully Backward Compatible**: All existing workflows continue unchanged
- **LoRA Sharing**: Flux and Flux Krea models share the same LoRA pool
- **Configuration**: No config file updates required for new features
- **Performance**: No additional overhead or setup requirements

## [1.2.1] - 2025-06-26

### 🐛 Bug Fixes
- **CRITICAL:** Fixed `NameError: name 'bot' is not defined` in slash commands
- `/generate` command now works correctly without runtime errors
- `/edit` command now works correctly without runtime errors
- All interactive features and progress tracking function properly

### 🔧 Technical Changes
- Added proper bot instance access via `interaction.client` in command functions
- Resolved variable scope issues in `generate_command()` and `edit_command()`

### 📋 Notes
This is a critical patch release that fixes a runtime error introduced in v1.2.0. All users should update immediately.

## [1.2.0] - 2025-01-29

### 🎉 Major Feature Release: Advanced Editing & Custom Animation Prompts

### Added
- **🎬 Custom Animation Prompts**: Users can now input custom prompts when animating images
  - Original generation prompt is pre-filled as default
  - Full text input with 500 character limit
  - Users can modify prompts for different animation effects
  - Example: Change "mountain landscape" → "mountain landscape with flowing clouds"
- **✏️ Advanced Image Editing System**: Complete Flux Kontext integration
  - New `/edit` slash command for direct image editing
  - Natural language editing prompts (e.g., "add sunglasses and a hat")
  - Post-generation Edit button on all generated images
  - Customizable sampling steps (10-50) for quality control
  - Support for PNG, JPG, WebP image uploads
- **🎨 Enhanced Post-Generation Actions**: All action buttons now use interactive modals
  - **Upscale Modal**: Choose factor (2x/4x/8x), denoise strength, and steps
  - **Animation Modal**: Custom prompts + frame count, strength, and steps
  - **Edit Modal**: Natural language editing with step control
- **📊 Improved User Experience**: Consistent modal-based parameter selection
  - Pre-filled sensible defaults for all parameters
  - Input validation with clear error messages
  - Enhanced progress tracking for all operations
  - Dual prompt display (original + custom) in results

### Enhanced
- **Animation Workflow**: Complete overhaul of animation system
  - `AnimationParameterModal` now includes prompt input field
  - `_perform_animation()` method accepts custom animation prompts
  - `PostGenerationAnimationModal` for consistent experience across views
  - Enhanced result embeds showing both animation and original prompts
- **Image Editing Workflow**: Professional-grade editing capabilities
  - Flux Kontext workflow integration (`flux_kontext_edit.json`)
  - `generate_edit()` method in ImageGenerator class
  - `_update_edit_workflow_parameters()` for workflow customization
  - Complete error handling and progress tracking
- **Configuration System**: Extended workflow support
  - Added `flux_kontext_edit` workflow configuration
  - Updated example configurations with editing workflow
  - Enhanced workflow type detection and validation

### Technical Improvements
- **Modal System**: Comprehensive Discord modal implementation
  - `EditParameterModal` for individual image editing
  - `PostGenerationEditModal` for post-generation editing
  - Enhanced `AnimationParameterModal` with prompt input
  - Consistent error handling across all modals
- **Progress Tracking**: Enhanced progress callbacks for all operations
  - Unified progress display format across editing and animation
  - Real-time status updates with operation-specific messaging
  - Improved error recovery and user feedback
- **File Management**: Enhanced image and video handling
  - Support for multiple image formats in editing
  - Optimized file upload and processing
  - Improved temporary file cleanup

### User Interface
- **Help Command**: Updated with comprehensive feature documentation
  - Detailed explanation of custom animation prompts
  - Complete image editing workflow examples
  - Enhanced post-generation action descriptions
  - Pro tips for optimal usage
- **Interactive Feedback**: Enhanced user guidance
  - Clear parameter descriptions in all modals
  - Example prompts and usage hints
  - Improved error messages with actionable suggestions

### Configuration
- **Workflow Integration**: Complete editing workflow support
  - `flux_kontext_edit.json` workflow configuration
  - Updated `config.example.json` with editing settings
  - Enhanced workflow detection and validation
  - Backward compatibility with existing setups

### Documentation
- **README Updates**: Comprehensive feature documentation
  - New "Advanced Image Editing" section
  - Enhanced "Professional Video Generation" with custom prompts
  - Updated usage examples and quick start guide
  - New feature highlights and key benefits
- **Help System**: In-bot documentation updates
  - Updated `/help` command with new features
  - Enhanced command descriptions and examples
  - Improved workflow explanations and tips

### Compatibility
- **Backward Compatibility**: All existing features remain unchanged
  - Existing workflows continue to work without modification
  - Previous animation behavior available as default
  - Configuration files remain compatible
- **Progressive Enhancement**: New features are additive
  - Users can choose to use new prompts or keep defaults
  - Existing buttons and commands work as before
  - Optional parameters don't break existing usage

## [1.1.2] - 2025-01-29

### Fixed
- **Configuration Examples**: Updated `config.example.json` to match current workflow structure
- **Workflow References**: Fixed outdated workflow names (`hidream_full_config-1` → `flux_lora`)
- **Missing Workflows**: Added missing workflow configurations for `hidream_lora` and `video_wan_vace_14B_i2v`
- **Security Settings**: Corrected rate limits and file type restrictions to match production values
- **Video Support**: Added `.mp4` to allowed file types in example configuration
- **Output Limits**: Updated example config to show correct output file limit (100 instead of 50)
- **Environment Variables**: Cleaned up `env.example` to remove unused references

### Changed
- **Default Workflow**: Changed from `hidream_full_config-1` to `flux_lora` in example config
- **Workflow Structure**: Simplified workflow configuration removing deprecated `parameters` mappings
- **Rate Limits**: Updated to production values (5 per user, 20 global) in example
- **Prompt Length**: Increased max prompt length to 2000 characters in example
- **File Types**: Extended allowed file types to include video formats

### Documentation
- **Setup Instructions**: Example configuration files now accurately reflect current codebase
- **Installation Guide**: Users can copy example files without needing manual corrections
- **Workflow Configuration**: Clear examples of how to configure each workflow type
- **Security Settings**: Proper rate limiting and file validation examples

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