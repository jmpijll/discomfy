# Changelog

## [1.2.9] - 2025-10-03

### 🐛 Concurrent Generation Progress Tracking Fix

### Fixed
- **HTTP Polling Progress**: Improved HTTP polling to extract actual progress data from ComfyUI's queue endpoint
- **WebSocket Fallback**: Enhanced fallback logic when WebSocket doesn't receive messages (due to client_id filtering)
- **Queued Generation Progress**: Queued generations now show progress via HTTP polling when WebSocket is unavailable
- **Completion Detection**: Improved history endpoint checking to detect completed generations more reliably

### Technical Details
- Enhanced HTTP polling to check for progress data in `queue_running` items (line 820-845)
- Added `websocket_has_progress` check to verify WebSocket has actual step data before applying
- WebSocket now marked as "best-effort" with HTTP polling as primary tracking mechanism
- Improved time-based fallback to only activate when no actual progress data is available
- Added more robust progress extraction from ComfyUI queue data structure

### Root Cause
ComfyUI's WebSocket with `?clientId={client_id}` parameter filters messages per client. When Generation B is queued while A is running:
1. Generation B's WebSocket connects with its own client_id
2. ComfyUI filters progress messages, so B's WebSocket receives nothing
3. Original code fell back to time-based estimation immediately
4. New code: HTTP polling now attempts to extract actual progress from queue data
5. If that fails, falls back to time-based estimation as last resort

### Impact
- Queued generations can now show progress even when WebSocket filtering prevents message reception
- HTTP polling provides actual step counts when available from ComfyUI's queue endpoint
- More reliable completion detection through history endpoint
- Better fallback chain: WebSocket → HTTP polling progress → Time-based estimation

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
