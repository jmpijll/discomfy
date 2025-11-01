# Animate Button Fix - "'NoneType' object can't be awaited"

**Date:** November 1, 2025  
**Status:** ✅ Fixed

---

## Issue

When clicking the "🎬 Animate" button on a generated image, the video generation failed with:
```
Video generation failed: 'NoneType' object can't be awaited
```

---

## Root Cause

The `VideoGenerator.validate_request()` method was trying to `await` the parent class method:

```python
# Video generator (video.py line 58)
async def validate_request(self, request: VideoGenerationRequest) -> None:
    # Call base validation
    await super().validate_request(request)  # ❌ Problem here!
    
    # Video-specific validation
    if request.length < 1:
        raise ValidationError("Video length must be at least 1 frame")
    ...
```

However, the base class method in `BaseGenerator` is **not async** and just returns `None`:

```python
# Base generator (base.py line 103)
def validate_request(self, request: GenerationRequest) -> bool:
    """Validate generation request."""
    pass  # Returns None
```

When you try to `await None`, Python raises: `TypeError: object NoneType can't be awaited`

---

## Solution

Removed the `await super().validate_request(request)` call since:
1. The base method does nothing (just `pass`)
2. The base method is not async
3. All validation is done in the child class anyway

**Fixed code:**
```python
async def validate_request(self, request: VideoGenerationRequest) -> None:
    """
    Validate video generation request.
    
    Args:
        request: Video generation request to validate
        
    Raises:
        ValidationError: If request is invalid
    """
    # Video-specific validation (no super call)
    if request.length < 1:
        raise ValidationError("Video length must be at least 1 frame")
    
    if request.length > 300:
        raise ValidationError("Video length cannot exceed 300 frames")
    
    if not 0.0 <= request.strength <= 1.0:
        raise ValidationError("Strength must be between 0.0 and 1.0")
```

---

## Technical Details

### Error Chain
1. User clicks "🎬 Animate" button
2. `AnimationParameterModal` calls `bot.video_generator.generate_video()`
3. `generate_video()` calls `await self.generate(request, progress_callback)`
4. `generate()` calls `await self.validate_request(request)`
5. `validate_request()` calls `await super().validate_request(request)`
6. Base method returns `None` (not a coroutine)
7. Python tries to `await None` → **Error!**

### The Fix
Simply remove the problematic `await super()` call:
- **File:** `core/generators/video.py`
- **Line:** 58 (removed)
- **Change:** Deleted `await super().validate_request(request)`

---

## Testing

### Video Generation Flow
1. ✅ Generate an image using `/generate`
2. ✅ Click the "🎬 Animate" button on the result
3. ✅ Set frame count (e.g., 121) and strength (e.g., 0.7)
4. ✅ Submit the modal
5. ✅ Video generation should start and complete successfully
6. ✅ Video file should be returned and playable

### Expected Behavior
- No more "'NoneType' object can't be awaited" error
- Video generation progresses normally
- ComfyUI workflow is queued and executed
- Video is downloaded and sent to Discord

---

## Files Modified

**`core/generators/video.py`** (line 47-65)
- Removed `await super().validate_request(request)` call
- Kept all video-specific validation logic

---

## Status

✅ **Fixed and ready for testing**  
✅ **No linter errors**  
✅ **All validation logic preserved**

The animate button should now work correctly!

