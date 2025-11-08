# Changelog

Complete version history for DisComfy.

---

## [2.0.0] - November 2, 2025

### 🎉 Major Release: Complete Architectural Overhaul

This is the biggest release in DisComfy history, featuring a complete transformation from monolithic to modular architecture while maintaining 100% backward compatibility.

#### 🏗️ Architecture

- **Refactored**: Complete transformation from monolithic to modular architecture
- **Structure**: Organized into `bot/`, `core/`, `config/`, `utils/` directories
- **Reduction**: 77% reduction in max file size (3,508 → 705 lines)
- **Modularity**: 50+ well-organized files with clear separation of concerns
- **Entry Point**: New `main.py` with clean architecture

#### 🎯 Code Quality

- **Testing**: Implemented comprehensive test suite (85/86 tests passing, 99% pass rate)
- **Best Practices**: Following Context7 patterns for discord.py and aiohttp
- **Type Safety**: Full Pydantic V2 migration with type hints throughout
- **Design Patterns**: Strategy, ABC, Factory, Repository patterns implemented
- **Validation**: Pydantic-powered validation with clear error messages

#### ✨ Features

- **Commands**: All 6 commands refactored with new architecture
  - `/generate` - Interactive generation with model selection
  - `/editflux` - High-quality Flux Kontext editing
  - `/editqwen` - Ultra-fast Qwen 2.5 VL editing
  - `/status` - Bot and ComfyUI status
  - `/help` - Command help
  - `/loras` - List available LoRAs
- **Generators**: Refactored ImageGenerator and VideoGenerator to v2.0 architecture
- **Progress**: Simplified progress tracking with better accuracy
- **UI Components**: Modular Discord UI (buttons, modals, views)

#### 🐛 Bug Fixes

- **WebSocket**: Continued improvements from v1.4.0
- **Progress**: Fixed 100% completion display issues
- **Pydantic**: Removed all V1 deprecation warnings
- **Discord.py**: Fixed SelectOption import for 2.x compatibility
- **Video**: Fixed Request/Response pattern issues
- **Validation**: Enhanced workflow validation

#### 📚 Documentation

- **Created**: 24+ comprehensive documentation files
- **Guides**: 
  - Migration Guide (v1.4.0 → v2.0.0)
  - API Reference (complete API docs)
  - Usage Examples (practical examples)
  - Testing Guide (comprehensive testing docs)
  - Installation Guide (Standard, Docker, Unraid)
  - Configuration Guide (all options explained)
  - Troubleshooting (common issues and solutions)
- **Organization**: Archived historical docs, clean root structure
- **Release Notes**: Complete v2.0.0 release documentation

#### 🐳 Docker & Deployment

- **Dockerfile**: Updated for v2.0 structure, uses `main.py`
- **GitHub Actions**: Configured for both GHCR and Docker Hub
- **Containers**: Auto-publish to:
  - `ghcr.io/jmpijll/discomfy`
  - `jamiehakker/discomfy` (Docker Hub)
- **Optimization**: Better layer caching, smaller image size
- **Tags**: Latest, version-specific, and commit SHA tags

#### 🔄 Backward Compatibility

- **100% Compatible**: No breaking changes from v1.4.0
- **Migration**: Old entry points still work (`bot.py`)
- **Configuration**: No config changes required
- **Workflows**: All workflows compatible
- **Commands**: All commands function identically

#### ⚡ Performance

- **Startup**: ~1 second (well under 3s target)
- **Tests**: 2.58s for 86 comprehensive tests
- **Code**: 60-75% reduction in key modules
- **Memory**: Optimized resource usage

#### 🛠️ Developer Experience

- **Imports**: Organized imports from new modules
- **Testing**: Easy to test individual components
- **Extensibility**: Clean base classes for new features
- **Type Hints**: Full type coverage
- **Linting**: Passes all quality checks

#### 📊 Statistics

- **Code Size Reduction**: 77% (3,508 → 705 lines max)
- **Test Pass Rate**: 99% (85/86 tests)
- **Files Created**: 50+ organized modules
- **Documentation**: 24+ comprehensive guides
- **Commits**: 100+ commits in v2.0 development

---

## [1.4.0] - October 31, 2025

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

- `image_gen.py`: Removed context managers, added lifecycle methods (~150 lines modified)
- `bot.py`: Updated initialization, removed 14 context manager usages (~20 lines modified)
- `video_gen.py`: Added lifecycle methods with resource sharing (~12 lines modified)

#### Testing

- ✅ Verified on production server with concurrent generations
- ✅ All tests passing, no regression
- ✅ WebSocket reconnection tested
- ✅ Startup and shutdown lifecycle tested

---

## [1.3.1] - October 5, 2025

### 🐛 Critical Bug Fixes for Custom Workflows

#### Fixed

- **LoRA Selector Error**: Fixed `'CompleteSetupView' object has no attribute 'insert_item'` error
  - Changed from non-existent `insert_item()` to correct `children.insert()` method
  - LoRA selector now initializes properly without errors
  - Credit to [@AyoKeito](https://github.com/AyoKeito) for identifying the issue

- **Custom Workflow Validation**: Fixed `"Cannot execute because a node is missing the class_type property"` error
  - Added comprehensive `_validate_workflow()` method to check workflow structure
  - Validates all nodes have required `class_type` property
  - Checks for proper workflow dictionary structure
  - Warns about missing `inputs` properties

#### Added

- **Intelligent Error Messages**: New validation provides detailed, actionable error messages
  - Lists specific nodes with issues (up to 5)
  - Explains what's wrong with each node
  - Provides common solutions and export format guidance
  - Tells users to use "Save (API Format)" in ComfyUI
  - Includes example of correct node structure

#### Technical Details

- `bot.py` (Line 823): Fixed LoRA selector initialization method
- `image_gen.py` (Lines 438-511): Added `_validate_workflow()` method
- `image_gen.py` (Line 429): Updated `_load_workflow()` to call validation
- Validation runs before sending workflow to ComfyUI, catching errors early

#### Impact

- ✅ Custom workflows now provide clear guidance when structure is invalid
- ✅ Users can debug workflow issues without trial-and-error
- ✅ LoRA selector works reliably for all model types
- ✅ Better developer experience for custom workflow creation

---

## [1.3.0] - October 4, 2025

### ✨ New Feature: Multi-Image Qwen Editing

#### Added

- **Multi-Image Qwen Edit**: `/editqwen` command now supports 1-3 input images
- **Workflow Selection**: Automatically selects correct workflow based on image count:
  - 1 image → `qwen_image_edit.json`
  - 2 images → `qwen_image_edit_2.json`
  - 3 images → `qwen_image_edit_3.json`
- **Optional Image Parameters**: Added `image2` and `image3` optional parameters to `/editqwen` command
- **Smart Validation**: Ensures image3 cannot be provided without image2

#### Changed

- **Image Generator**: Enhanced `generate_edit()` method with `additional_images` parameter
- **Workflow Parameters**: Updated `_update_qwen_edit_workflow_parameters()` to handle multiple `LoadImage` nodes
- **Progress Display**: Shows total image count in progress messages
- **Initial Response**: Displays all input images with their file sizes

#### Technical Details

- Multi-image data passed as `List[bytes]` via `additional_images` parameter
- Images uploaded with unique timestamps to ComfyUI
- LoadImage nodes automatically assigned to correct images by node ID order
- All Qwen workflows (1, 2, and 3 images) fully supported

---

## [1.2.11] - October 4, 2025

### 🔧 Critical Fix: True Persistent WebSocket Implementation

#### Fixed

- **Concurrent Generation Completion**: Fixed bug where second generation never completed until third started
- **Progress Tracking**: Fixed issue where progress stayed on "Checking status..." then jumped to 100%
- **WebSocket Architecture**: Implemented single persistent WebSocket that monitors ALL generations simultaneously
- **Session Management**: WebSocket now stays alive across multiple `async with` context manager cycles

#### Technical Details

- Previous fix (v1.2.10) used shared client_id but still created separate WebSocket per generation
- Multiple WebSockets competed for messages, causing progress tracking failures
- New architecture: ONE persistent WebSocket for entire bot session
- Each generation registers/unregisters with `_active_generations` dictionary
- Persistent monitor routes messages to correct generation by `prompt_id`
- WebSocket starts on first generation, persists across all subsequent generations

#### Impact

- ✅ All concurrent generations now complete correctly without manual intervention
- ✅ Real-time progress tracking works for all generations
- ✅ No more "stuck at Checking status" issues
- ✅ True concurrent queue handling as originally intended

---

## [1.2.10] - October 3, 2025

### 🐛 Critical Queue Handling Fix

#### Fixed

- **Queued Generation Progress**: Fixed critical bug where generations started while another is running would never show progress percentages
- **WebSocket Client Filtering**: Removed `?clientId` parameter from WebSocket connections
- **Completion Detection**: Fixed issue where completed generations weren't detected until new generation started
- **Progress Message Filtering**: Implemented proper prompt-based filtering
- **Concurrent Request Handling**: Multiple users can now safely queue generations simultaneously

#### Technical Details

- Removed `?clientId={client_id}` from WebSocket URL that was filtering messages
- WebSocket now receives ALL messages from ComfyUI
- Added `currently_executing_prompt` tracking
- Progress messages filtered by matching against currently executing prompt_id

---

## [1.2.9] - October 3, 2025

### 🐛 Concurrent Generation Progress Tracking Fix

Note: This version exists in remote repository with different implementation approach.

---

## [1.2.8] - October 3, 2025

### 🚀 Dual Image Editing Models

#### Added

- **Qwen 2.5 VL Ultra-Fast Editing**: New `/editqwen` command (30-60 seconds)
- **Dual Edit Buttons**: Both **✏️ Flux Edit** and **⚡ Qwen Edit** buttons on generated images
- **Smart Parameter Validation**: Context-aware step validation (4-20 for Qwen, 10-50 for Flux)
- **Automatic CFG Adjustment**: Optimized CFG values per workflow
- **New Workflow Integration**: Added `qwen_image_edit.json` workflow support

#### Changed

- **Command Renamed**: `/edit` → `/editflux` (Flux Kontext high-quality editing)
- **Edit Buttons Split**: Single edit button now split into Flux and Qwen variants
- **Modal Titles**: Context-aware modal titles indicating model being used
- **Progress Messages**: Model-specific progress indicators

---

## Earlier Versions

For complete version history, see the [repository's commit history](https://github.com/jmpijll/discomfy/commits/main).

---

## Version Numbering

DisComfy follows [Semantic Versioning](https://semver.org/):

- **MAJOR** version (2.0.0) - Incompatible API changes (but v2.0.0 is backward compatible!)
- **MINOR** version (1.3.0) - New functionality in backward-compatible manner
- **PATCH** version (1.3.1) - Backward-compatible bug fixes

---

## Upgrade Guide

See **[[Migration Guide]]** for detailed upgrade instructions.

**Quick Upgrade:**
```bash
git pull origin main
pip install -r requirements.txt --upgrade
python main.py
```

---

For the latest changes, see [GitHub Releases](https://github.com/jmpijll/discomfy/releases).

