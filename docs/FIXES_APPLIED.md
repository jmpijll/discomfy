# Fixes Applied - Model Selection & Old Code Cleanup

**Date:** November 1, 2025  
**Issues Fixed:** Model dropdown reversion, LoRA dropdown not showing, old code references

---

## Issues Identified

1. **Model Dropdown Always Reverts to Flux (Fast)**
   - Selected model wasn't persisting in the UI
   - ModelSelectMenu wasn't being rebuilt with correct default

2. **LoRA Dropdown Never Shows**
   - LoRA menu wasn't being added to the view properly
   - View children weren't being updated correctly after model change

3. **Old Code References**
   - Still importing from deleted `image_gen.py` module
   - `from image_gen import ProgressInfo` causing errors
   - Multiple files had backward compatibility code for old module

---

## Fixes Applied

### Fix 1: Model Selection Persistence (`bot/ui/generation/select_menus.py`)

**Problem:** When user selected a different model, the dropdown would revert to "Flux (Fast)" on the next interaction.

**Solution:** Rebuild the ModelSelectMenu with the correct `current_model` parameter:

```python
# Remove old model and LoRA select menus
items_to_remove = []
for item in view.children:
    if isinstance(item, (ModelSelectMenu, LoRASelectMenu)):
        items_to_remove.append(item)

for item in items_to_remove:
    view.remove_item(item)

# Add new model select menu with correct default
new_model_menu = ModelSelectMenu(current_model=selected_model)
view.children.insert(0, new_model_menu)

# Add updated LoRA select menu if LoRAs are available
if view.loras:
    new_lora_menu = LoRASelectMenu(view.loras, view.selected_lora)
    view.children.insert(1, new_lora_menu)
```

**Key Changes:**
- ✅ Defer interaction **before** rebuilding view
- ✅ Remove **both** model and LoRA menus completely
- ✅ Recreate ModelSelectMenu with `current_model=selected_model`
- ✅ Always add LoRA menu when LoRAs are available
- ✅ Log changes for debugging

### Fix 2: LoRA Menu Display

**Problem:** LoRA select menu was never showing up, even though LoRAs were available.

**Solution:** Properly insert LoRA menu at index 1 (right after model menu) with correct data structure:

```python
# LoRAs have 'filename' and 'display_name' keys
lora_filename = lora.get('filename', 'Unknown')
lora_display = lora.get('display_name', lora_filename)
```

**Key Changes:**
- ✅ Use correct keys: `filename` and `display_name` (not `name`)
- ✅ Insert LoRA menu at consistent position (index 1)
- ✅ Update view immediately when model changes

### Fix 3: Remove Old `image_gen` References

**Problem:** Multiple files still importing from deleted `image_gen.py` module, causing runtime errors.

**Files Updated:**

1. **`bot/ui/generation/complete_setup_view.py`**
   - Removed: `from image_gen import ProgressInfo`
   - Removed: Old ProgressInfo completion logic
   - Simplified cleanup code

2. **`bot/commands/edit.py`** (2 occurrences)
   - Removed: `from image_gen import ProgressInfo`
   - Removed: ImportError fallback logic
   - Now uses only new `ProgressTracker`

3. **`core/generators/image.py`**
   - Removed: `from image_gen import ProgressInfo` try/except
   - Removed: `old_progress` variable and all related code
   - Removed: Dual progress tracking (old + new)
   - Cleaned up `_wait_for_completion_with_websocket` method

**Before:**
```python
try:
    from image_gen import ProgressInfo
    old_progress = ProgressInfo()
    old_progress.mark_completed()
    await progress_callback(old_progress)
except ImportError:
    # Fallback...
```

**After:**
```python
from core.progress.tracker import ProgressTracker
tracker = ProgressTracker()
tracker.mark_completed()
await progress_callback(tracker)
```

---

## Testing Results

### ✅ Bot Startup
```
✅ Configuration loaded successfully
✅ Command handlers registered
✅ VideoGenerator initialized
✅ Bot logged in successfully
✅ NO ERRORS - no references to old code
```

### ✅ Expected Behavior Now

1. **Model Selection:**
   - Select "Flux Krea" → dropdown shows "Flux Krea ✨ NEW"
   - Select "HiDream" → dropdown shows "HiDream"
   - Selection **persists** across interactions

2. **LoRA Menu:**
   - When Flux selected → shows Flux-compatible LoRAs
   - When Flux Krea selected → shows Flux-compatible LoRAs
   - When HiDream selected → shows HiDream-compatible LoRAs
   - LoRA menu **always visible** when LoRAs available

3. **Progress Tracking:**
   - Uses only new `ProgressTracker` (v2.0)
   - No more "No module named 'image_gen'" errors
   - Clean progress updates throughout generation

---

## Files Modified

| File | Changes | Lines Changed |
|------|---------|---------------|
| `bot/ui/generation/select_menus.py` | Fixed model selection persistence & LoRA menu | ~40 lines |
| `bot/ui/generation/complete_setup_view.py` | Removed old ProgressInfo import | ~15 lines |
| `bot/commands/edit.py` | Removed old ProgressInfo fallback (2×) | ~20 lines |
| `core/generators/image.py` | Removed all old ProgressInfo code | ~30 lines |

**Total:** 4 files modified, ~105 lines cleaned up

---

## Verification Steps

1. ✅ Start bot - no import errors
2. 🔜 Test `/generate` command
3. 🔜 Select different models - verify dropdown persists
4. 🔜 Verify LoRA menu appears for each model
5. 🔜 Complete generation - verify no errors in logs

---

## Next Steps

**Ready for Discord Testing!**

Test the following in Discord:

```
1. /generate prompt:"test image"
   → Select Flux (Fast)
   → Verify LoRA menu shows
   → Generate

2. /generate prompt:"test image"
   → Select Flux Krea ✨ NEW
   → Verify dropdown STAYS on Flux Krea
   → Verify LoRA menu shows
   → Generate

3. /generate prompt:"test image"
   → Select HiDream
   → Verify dropdown STAYS on HiDream
   → Verify LoRA menu shows (HiDream LoRAs only)
   → Generate
```

All issues should now be resolved! 🎉

