# Changelog

## [2.1.1] - 2025-11-08

### 🐛 Bug Fixes: Docker Container Support for DyPE Workflow

#### Fixed Docker Container Issues
- **DyPE Workflow Missing in Containers**: Added `dype_flux_krea_lora` workflow to default configurations
  - Updated `config.example.json` with DyPE workflow configuration
  - Updated `config/migration.py` get_default_workflows() to include DyPE
  - Dockerfile now copies `config.example.json` to container
  - Containers without mounted config.json will now have DyPE workflow available

#### Root Cause
When users ran the Docker container without mounting their own `config.json`, the bot fell back to hardcoded default workflows in `get_default_workflows()` which didn't include the new DyPE workflow added in v2.1.0. This caused the error: `Image generation failed: 'dype_flux_krea_lora'`.

#### Solution
- Added DyPE workflow to all three config sources:
  1. `config.example.json` (template file)
  2. `config/migration.py` default workflows (fallback)
  3. Dockerfile now includes example config in container

Users upgrading from v2.1.0 to v2.1.1:
- If using Docker with environment variables: Pull new image, containers will automatically have DyPE workflow
- If using mounted config.json: The migration system will automatically add DyPE workflow on startup
- No manual intervention required!

### Technical Details
- Modified Files:
  - `config.example.json`: Added dype_flux_krea_lora workflow configuration
  - `config/migration.py`: Added dype_flux_krea_lora to get_default_workflows()
  - `Dockerfile`: Now copies config.example.json to container for fallback use

---

## [2.1.0] - 2025-11-08

### 🚀 New Features: DyPE Flux Krea Model + Smart Image Compression

#### New Model Support
- **DyPE Flux Krea**: Ultra high-resolution image generation (up to 4K)
  - Dynamic Position Encoding for exceptional detail at high resolutions
  - Default 2560x2560 resolution with up to 4096x4096 support
  - Optimized defaults: 40 steps, CFG 1.0, dype_exponent 2.0
  - Full LoRA support with 19 compatible LoRAs
  - Added `dype-flux-krea-lora.json` workflow

#### Smart Image Compression
- **Lossless PNG Optimization**: Automatically compresses large images while preserving quality
  - Two-tier compression strategy: PNG optimization first, JPEG fallback
  - PNG compression levels 9, 6, 3 tried sequentially (completely lossless)
  - JPEG fallback with high-quality settings (98→95→92→...→60)
  - Only compresses images >10MB (Discord's upload limit)
  - Original PNG always saved to disk for archival
  - Compression notice in Discord embed shows format used and ratio

#### UI Improvements
- **Fixed LoRA Dropdown**: Resolved Discord's 25 option limit issue
  - "None" option now added first, followed by 24 LoRAs
  - Prevents "Invalid Form Body" errors
  - LoRA strength button now appears correctly for DyPE model
- **WAN LoRA Filtering**: Video workflow LoRAs no longer appear in image generation
  - Reduces clutter in LoRA dropdown
  - Prevents confusion about LoRA compatibility
- **DyPE-Specific Modal**: Custom parameter modal for DyPE model
  - DyPE exponent control (0.5-4.0) instead of batch size
  - Extended dimension limits (512-4096 vs 512-2048)
  - Model-specific defaults and validation

#### Technical Improvements
- **WorkflowUpdater**: Added `DyPEFluxUpdater` for DyPE-specific nodes
  - Handles `DyPE_FLUX` node parameter updates
  - Supports width, height, and dype_exponent parameters
- **Model Configuration**: Added DyPE config to workflows
  - Default dimensions, steps, CFG, and dype_exponent
  - Workflow file mapping in configuration
- **Validation**: Extended dimension validation for DyPE (up to 4096px)

#### Bug Fixes
- **LoRA Selection State**: Fixed LoRA reset when changing models
- **Button Visibility**: LoRA strength button now appears reliably
- **Progress Display**: Better handling of high-resolution generation progress
- **File Size Handling**: Graceful handling of images exceeding Discord limits

#### Performance
- **Compression Speed**: Fast lossless PNG optimization (<1s for most images)
- **Minimal Quality Loss**: High-quality JPEG settings when conversion needed
- **Efficient Caching**: Compression results cached for action buttons

### Technical Details
- Modified Files:
  - `bot/ui/generation/select_menus.py`: Fixed LoRA dropdown, added DyPE defaults
  - `bot/ui/generation/modals.py`: Added DyPE-specific parameter modal
  - `bot/ui/generation/post_view.py`: Implemented smart compression system
  - `bot/ui/generation/complete_setup_view.py`: Added DyPE workflow mapping
  - `core/generators/image.py`: Added WAN LoRA filtering
  - `core/comfyui/workflows/updater.py`: Added DyPEFluxUpdater
  - `config.json`: Added dype_flux_krea_lora workflow configuration

## [2.0.0] - 2025-11-02

### 🎉 Major Release: Complete Architectural Overhaul

#### Architecture
- **Refactored**: Complete transformation from monolithic to modular architecture
- **Structure**: Organized into `bot/`, `core/`, `config/`, `utils/` directories
- **Reduction**: 77% reduction in max file size (3,508 → 705 lines)
- **Modularity**: 50+ well-organized files with clear separation of concerns

#### Code Quality
- **Testing**: Implemented comprehensive test suite (85/86 tests passing, 99%)
- **Best Practices**: Following Context7 patterns for discord.py and aiohttp
- **Type Safety**: Full Pydantic V2 migration with type hints throughout
- **Design Patterns**: Strategy, ABC, Factory, Repository patterns implemented

#### Features
- **Commands**: All 6 commands refactored with new architecture (/generate, /editflux, /editqwen, /status, /help, /loras)
- **Generators**: Refactored ImageGenerator and VideoGenerator to v2.0 architecture
- **Validation**: Pydantic-powered validation with clear error messages
- **Progress**: Simplified progress tracking with better accuracy

#### Bug Fixes
- **WebSocket**: Continued improvements from v1.4.0
- **Progress**: Fixed 100% completion display issues
- **Pydantic**: Removed all V1 deprecation warnings
- **Discord.py**: Fixed SelectOption import for 2.x compatibility
- **Video**: Fixed Request/Response pattern issues

#### Documentation
- **Created**: 24+ comprehensive documentation files
- **Guides**: Migration guide, API docs, usage examples, testing guide
- **Organization**: Archived historical docs, clean root structure
- **Release Notes**: Complete v2.0.0 release documentation

#### Docker & Deployment
- **Dockerfile**: Updated for v2.0 structure, uses `main.py`
- **GitHub Actions**: Configured for both GHCR and Docker Hub
- **Containers**: Auto-publish to ghcr.io and Docker Hub
- **Optimization**: Better layer caching, smaller image size

#### Backward Compatibility
- **100% Compatible**: No breaking changes from v1.4.0
- **Migration**: Old entry points still work, smooth upgrade path
- **Configuration**: No config changes required

#### Performance
- **Startup**: ~1 second (well under 3s target)
- **Tests**: 2.58s for 86 comprehensive tests
- **Code**: 60-75% reduction in key modules

#### Developer Experience
- **Entry Point**: New `main.py` with clean architecture
- **Imports**: Organized imports from new modules
- **Testing**: Easy to test individual components
- **Extensibility**: Clean base classes for new features

See [RELEASE_NOTES.md](RELEASE_NOTES.md) for complete details.

## [1.4.0] - 2025-10-31

### 🐛 Critical Bug Fix: Concurrent Generation Hanging Issue Resolved

#### Fixed
- **Concurrent Generation Hanging Bug**: Fixed critical issue where second concurrent generation would complete in ComfyUI but never display in Discord
  - Moved WebSocket initialization from per-generation to bot startup
  - Removed context manager pattern that caused race conditions
  - Added explicit `initialize()` and `shutdown()` methods
  - WebSocket now opens once and stays alive for entire bot lifetime
  - Both concurrent generations now complete successfully without hanging
  - Fixes [#2](https://github.com/jmpijll/discomfy/issues/2)

#### Improved
- **Performance**: 5-10x faster generation queue times (no session recreation)
- **Reliability**: Automatic WebSocket reconnection (up to 999 retries)
- **Code Quality**: Removed 47 lines of complex code, simpler architecture
- **Resource Management**: Single persistent HTTP session for bot lifetime

#### Technical Details
- `image_gen.py`: Removed context managers, added lifecycle methods
- `bot.py`: Updated initialization, removed 14 context manager usages
- `video_gen.py`: Added lifecycle methods with resource sharing

#### Testing
- ✅ Verified on production server with concurrent generations
- ✅ All tests passing, no regression

---

## [1.3.1] - 2025-10-05

### 🐛 Critical Bug Fixes for Custom Workflows

### Fixed
- **LoRA Selector Error**: Fixed `'CompleteSetupView' object has no attribute 'insert_item'` error
  - Changed from non-existent `insert_item()` to correct `children.insert()` method
  - LoRA selector now initializes properly without errors
  - Credit to [@AyoKeito](https://github.com/AyoKeito) for identifying the issue

- **Custom Workflow Validation**: Fixed `"Cannot execute because a node is missing the class_type property"` error
  - Added comprehensive `_validate_workflow()` method to check workflow structure
  - Validates all nodes have required `class_type` property
  - Checks for proper workflow dictionary structure
  - Warns about missing `inputs` properties

### Added
- **Intelligent Error Messages**: New validation provides detailed, actionable error messages
  - Lists specific nodes with issues (up to 5)
  - Explains what's wrong with each node
  - Provides common solutions and export format guidance
  - Tells users to use "Save (API Format)" in ComfyUI
  - Includes example of correct node structure

### Technical Details
- `bot.py` (Line 823): Fixed LoRA selector initialization method
- `image_gen.py` (Lines 438-511): Added `_validate_workflow()` method
- `image_gen.py` (Line 429): Updated `_load_workflow()` to call validation
- Validation runs before sending workflow to ComfyUI, catching errors early

### Impact
- ✅ Custom workflows now provide clear guidance when structure is invalid
- ✅ Users can debug workflow issues without trial-and-error
- ✅ LoRA selector works reliably for all model types
- ✅ Better developer experience for custom workflow creation

## [1.3.0] - 2025-10-04

### ✨ New Feature: Multi-Image Qwen Editing

### Added
- **Multi-Image Qwen Edit**: `/editqwen` command now supports 1-3 input images
- **Workflow Selection**: Automatically selects correct workflow based on image count:
  - 1 image → `qwen_image_edit.json`
  - 2 images → `qwen_image_edit_2.json`
  - 3 images → `qwen_image_edit_3.json`
- **Optional Image Parameters**: Added `image2` and `image3` optional parameters to `/editqwen` command
- **Smart Validation**: Ensures image3 cannot be provided without image2

### Changed
- **Image Generator**: Enhanced `generate_edit()` method with `additional_images` parameter
- **Workflow Parameters**: Updated `_update_qwen_edit_workflow_parameters()` to handle multiple `LoadImage` nodes
- **Progress Display**: Shows total image count in progress messages
- **Initial Response**: Displays all input images with their file sizes

### Technical Details
- Multi-image data passed as `List[bytes]` via `additional_images` parameter
- Images uploaded with unique timestamps to ComfyUI
- LoadImage nodes automatically assigned to correct images by node ID order
- All Qwen workflows (1, 2, and 3 images) fully supported

### Known Issues
- **Concurrent Queue Handling**: Second generation may not complete until third is started (documented in `KNOWN_ISSUES.md`)

## [1.2.11] - 2025-10-04

### 🔧 Critical Fix: True Persistent WebSocket Implementation

### Fixed
- **Concurrent Generation Completion**: Fixed bug where second generation never completed until third started
- **Progress Tracking**: Fixed issue where progress stayed on "Checking status..." then jumped to 100%
- **WebSocket Architecture**: Implemented single persistent WebSocket that monitors ALL generations simultaneously
- **Session Management**: WebSocket now stays alive across multiple `async with` context manager cycles

### Technical Details
- Previous fix (v1.2.10) used shared client_id but still created separate WebSocket per generation
- Multiple WebSockets competed for messages, causing progress tracking failures
- New architecture: ONE persistent WebSocket for entire bot session
- Each generation registers/unregisters with `_active_generations` dictionary
- Persistent monitor routes messages to correct generation by `prompt_id`
- WebSocket starts on first generation, persists across all subsequent generations

### Root Cause (v1.2.10)
- `async with generator` pattern created/destroyed sessions per generation
- Each generation spawned its own WebSocket connection
- Even with shared client_id, multiple connections interfered with each other
- Solution required architectural change: persistent WebSocket independent of sessions

### Impact
- ✅ All concurrent generations now complete correctly without manual intervention
- ✅ Real-time progress tracking works for all generations (step counts, percentages)
- ✅ No more "stuck at Checking status" issues
- ✅ No more requiring third generation to detect second's completion
- ✅ True concurrent queue handling as originally intended

## [1.2.10] - 2025-10-03

### 🐛 Critical Queue Handling Fix

### Fixed
- **Queued Generation Progress**: Fixed critical bug where generations started while another is running would never show progress percentages
- **WebSocket Client Filtering**: Removed `?clientId` parameter from WebSocket connections that was preventing queued generations from receiving progress messages
- **Completion Detection**: Fixed issue where completed generations weren't detected until a new generation started
- **Progress Message Filtering**: Implemented proper prompt-based filtering to prevent cross-contamination between concurrent generations
- **Concurrent Request Handling**: Multiple users can now safely queue generations simultaneously with accurate progress tracking

### Technical Details
- Removed `?clientId={client_id}` from WebSocket connection URL (line 602) - was causing ComfyUI to filter messages per client
- WebSocket now connects without client filtering to receive ALL messages from ComfyUI
- Added `currently_executing_prompt` tracking in `_track_websocket_progress()` to identify which prompt is actually running
- Progress messages filtered by matching against currently executing prompt_id
- Each generation's WebSocket properly receives 'executing' messages to detect when its prompt starts running
- Enhanced logging to track prompt execution state transitions

### Root Cause
The issue was caused by the WebSocket connecting with `?clientId={client_id}` parameter, which made ComfyUI filter messages to only that specific client. When Generation B was queued while Generation A was running:
1. Generation B's WebSocket connected with its own client_id
2. ComfyUI filtered messages, so Generation B's WebSocket didn't receive ANY messages
3. When Generation B started executing, its WebSocket never received the 'executing' or 'progress' messages
4. Result: Generation B showed elapsed time but no progress percentage
5. HTTP polling eventually detected completion in history, but only when triggered by a new generation

### Impact
This fix resolves the core issue with concurrent generation handling. Users can now:
- Queue multiple generations that show accurate progress when running
- See "Queued" status with position while waiting
- See progress percentages and step counts when generation actually starts
- Have all generations complete properly without needing to start another generation to trigger completion detection

## [1.2.9] - 2025-10-03

### 🐛 Concurrent Generation Progress Tracking Fix (Remote Release)

Note: This version exists in the remote repository with a different implementation approach.

## [1.2.8] - 2025-10-03

### 🚀 Dual Image Editing Models - Choose Your Speed!

### Added
- **Qwen 2.5 VL Ultra-Fast Editing**: New `/editqwen` command for lightning-fast image editing (30-60 seconds)
- **Dual Edit Buttons**: Both **✏️ Flux Edit** and **⚡ Qwen Edit** buttons on all generated images
- **Smart Parameter Validation**: Context-aware step validation (4-20 for Qwen, 10-50 for Flux)
- **Automatic CFG Adjustment**: Optimized CFG values per workflow (1.0 for Qwen, 2.5 for Flux)
- **New Workflow Integration**: Added `qwen_image_edit.json` workflow support

### Changed
- **Command Renamed**: `/edit` → `/editflux` (Flux Kontext high-quality editing)
- **Edit Buttons Split**: Single edit button now split into Flux and Qwen variants
- **Modal Titles**: Context-aware modal titles indicating which model is being used
- **Progress Messages**: Model-specific progress indicators and status messages

### Enhanced
- **Flexible Editing Workflow**: Choose between quality (Flux) or speed (Qwen)
- **Model-Specific Defaults**: Each model has optimized default parameters
- **Workflow Type Parameter**: Added `workflow_type` to `generate_edit()` method
- **Improved Documentation**: Updated README with dual editing model information
- **Better User Feedback**: Clear indication of which model is being used

### Technical Details
- Added `_update_qwen_edit_workflow_parameters()` method to ImageGenerator
- Updated `generate_edit()` to support both "flux" and "qwen" workflow types
- Modified edit button callbacks to pass workflow type to modals
- Enhanced modal classes to accept and handle workflow_type parameter
- Updated command registration to include both editflux and editqwen commands

### 📊 Impact
This release introduces a game-changing dual editing system that lets users choose between high-quality detailed editing or ultra-fast editing based on their needs. Qwen 2.5 VL provides excellent results in a fraction of the time (30-60 seconds vs 1-3 minutes), making it perfect for rapid iteration and testing.
