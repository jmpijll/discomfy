# Changelog

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
