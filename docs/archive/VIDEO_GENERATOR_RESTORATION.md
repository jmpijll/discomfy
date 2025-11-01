# Video Generator Restoration - v2.0 Refactor

## Issue
Video support was accidentally disabled during cleanup because we deleted `video_gen.py` without creating the refactored `core/generators/video.py` as specified in the refactoring plan.

## Solution
Created `core/generators/video.py` following the v2.0 architecture:

### Key Changes

1. **New VideoGenerator Class** (`core/generators/video.py`)
   - Extends `BaseGenerator` (proper v2.0 architecture)
   - Uses shared `ComfyUIClient` for API calls
   - Implements `generate()` method with `VideoGenerationRequest`
   - Includes video-specific workflow parameter updates
   - Handles video file downloads from ComfyUI

2. **VideoGenerationRequest Model**
   - Extends `GenerationRequest` with video-specific fields:
     - `length`: Video length in frames (default: 81)
     - `strength`: Strength for I2V conversion (default: 0.7)

3. **Integration with Bot** (`bot/client.py`)
   - VideoGenerator now initialized with new v2.0 architecture
   - Shares ComfyUI client with ImageGenerator
   - No longer tries to import old `video_gen.py`

### Features Preserved from Old Code

✅ Video workflow parameter updates  
✅ Image-to-video (I2V) support with image uploads  
✅ Video file downloads from ComfyUI  
✅ Progress tracking via callbacks  
✅ Comprehensive logging  
✅ Error handling with custom exceptions  
✅ Utility functions (`save_output_video`, `get_unique_video_filename`)

### Architecture Benefits

- **Consistent API**: VideoGenerator follows same interface as ImageGenerator
- **Shared Resources**: Both generators use the same ComfyUI client and session
- **Better Testing**: Follows BaseGenerator contract for easier unit testing
- **Proper Validation**: Uses Pydantic models for request validation
- **Exception Hierarchy**: Uses custom exception classes for better error handling

## Testing

✅ Bot starts successfully  
✅ VideoGenerator initialized with v2.0 architecture  
✅ No linter errors  
✅ Ready for Discord testing

## Next Steps

1. Test video generation commands in Discord
2. Verify I2V (image-to-video) workflows
3. Test progress tracking during video generation
4. Create unit tests for VideoGenerator (similar to ImageGenerator tests)

## Files Modified

- **Created**: `core/generators/video.py` (367 lines)
- **Modified**: `bot/client.py` (VideoGenerator initialization)
- **Modified**: `core/generators/__init__.py` (exports)
- **Deleted**: Old `video_gen.py` (replaced with v2.0 version)

