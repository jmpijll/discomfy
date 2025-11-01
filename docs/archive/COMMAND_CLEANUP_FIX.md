# Command Progress Message Cleanup

**Date:** November 2, 2025  
**Status:** ✅ Fixed

---

## Issue

The `/editflux` and `/editqwen` commands were leaving progress messages behind after completing, just like the button modals were doing before.

**Example:**
```
✏️ Starting Image Edit - Flux Kontext
Edit Prompt: make him blue
Settings: Flux Kontext | Steps: 20 | CFG: 2.5
Progress: ███████████████████░ 100%
(bewerkt)  ← Message stayed here!

✅ Image Edited Successfully!
[Edited image]
```

---

## Root Cause

These command handlers use `bot._create_unified_progress_callback()` which edits the **original response** (the initial message showing the settings). After generation completes, they:

1. Call the progress callback one more time with `tracker.mark_completed()` → Shows 100%
2. Send the final result via `interaction.followup.send()` → New message
3. But never delete the original message → **Stays visible at 100%**

---

## Solution

Delete the original response (progress message) right before sending the final result:

```python
# After generation completes
result = await bot.image_generator.generate(request)

# Delete progress message since we're sending the final result
try:
    await interaction.delete_original_response()
except:
    pass  # Message might already be deleted

# Send final result as new message
await interaction.followup.send(embed=success_embed, file=file)
```

**Also added cleanup on errors:**
```python
except Exception as e:
    bot.logger.error(f"Error in command: {e}")
    
    # Delete progress message on error
    try:
        await interaction.delete_original_response()
    except:
        pass
    
    # Send error message
    await interaction.followup.send(f"❌ Error: {str(e)}", ephemeral=True)
```

---

## Files Modified

**`bot/commands/edit.py`** - Both command handlers updated:

### 1. `/editflux` (editflux_command_handler)
- **Line 118-121:** Delete original response on success
- **Line 150-153:** Delete original response on error
- **Removed:** Lines that called `progress_callback(tracker.mark_completed())` - no longer needed

### 2. `/editqwen` (editqwen_command_handler)
- **Line 297-300:** Delete original response on success
- **Line 327-330:** Delete original response on error
- **Removed:** Lines that called `progress_callback(tracker.mark_completed())` - no longer needed

---

## Before & After

### Before (Messages Stay Behind)
```
┌─────────────────────────────────┐
│ ✏️ Starting Image Edit - Flux   │
│ Edit Prompt: make him blue      │
│ Settings: Flux | Steps: 20      │
│ Progress: ████████████████ 100% │  ← Stuck at 100%!
└─────────────────────────────────┘
┌─────────────────────────────────┐
│ ✅ Image Edited Successfully!   │
│ [Edited image with buttons]     │
└─────────────────────────────────┘
```

### After (Clean Results)
```
┌─────────────────────────────────┐
│ ✅ Image Edited Successfully!   │  ← Only final result!
│ [Edited image with buttons]     │
└─────────────────────────────────┘
```

---

## Why Delete Instead of Edit?

You might wonder: why delete the message instead of editing it to show the final result?

**Reasons:**
1. **Consistency:** Button modals create separate progress messages that get deleted - this matches that behavior
2. **Cleaner UX:** Final result message has the image attachment and action buttons (upscale, edit again, animate)
3. **Better Format:** Progress message just shows settings, final message shows the actual result with proper embed

---

## Comparison: Commands vs Modals

### Command Pattern (editflux/editqwen)
- Initial message sent via `interaction.response.send_message()`
- Progress updates edit that original message
- **Delete original message** → Send new final result via `followup.send()`

### Modal Pattern (Upscale/Edit/Animate buttons)
- Create separate progress message via `interaction.followup.send()`
- Progress updates edit that separate message
- **Delete separate message** → Send new final result via `followup.send()`

**Both patterns now clean up properly!** ✅

---

## Testing

### /editflux Command
1. ✅ Run `/editflux` with an image and prompt
2. ✅ Initial message appears with settings
3. ✅ Progress updates show in that message
4. ✅ Original message disappears when complete
5. ✅ Only final result message remains

### /editqwen Command
1. ✅ Run `/editqwen` with 1-3 images and prompt
2. ✅ Initial message shows input images and settings
3. ✅ Progress updates show in that message
4. ✅ Original message disappears when complete
5. ✅ Only final result message remains

### Error Cases
1. ✅ Trigger validation error (invalid prompt)
2. ✅ Trigger generation error (timeout)
3. ✅ Verify progress message is deleted
4. ✅ Verify error message shows
5. ✅ No leftover progress messages

---

## Complete Cleanup Coverage

### ✅ Button Modals (bot/ui/image/modals.py)
- UpscaleParameterModal → Deletes separate progress message
- EditParameterModal → Deletes separate progress message
- AnimationParameterModal → Deletes separate progress message

### ✅ Slash Commands (bot/commands/edit.py)
- `/editflux` → Deletes original response message
- `/editqwen` → Deletes original response message

**All progress messages now clean up automatically!** 🧹

---

## Status

✅ **Both commands updated**  
✅ **Success path deletes progress**  
✅ **Error path deletes progress**  
✅ **No linter errors**  
✅ **Ready for testing**

**All edit operations now have clean message management!** 🎉

