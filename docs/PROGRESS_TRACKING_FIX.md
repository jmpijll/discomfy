# Progress Tracking Discord Update Fix

**Date:** November 1, 2025  
**Issue:** WebSocket tracking works but Discord message not updating  
**Status:** ✅ FIXED

---

## Problem

The progress tracking system had TWO critical bugs:

### Bug 1: ProgressTracker.update_step_progress() Not Setting Percentage

**Location:** `core/progress/tracker.py` line 202

**Problem:**
```python
# OLD CODE (BROKEN)
if self._current_step_sequence == 0:
    step_percentage = (current / total) * 100
    self.state.metrics.current_step = current  # ❌ Only set step, not percentage!
```

**Impact:** 
- WebSocket received step data correctly
- `update_step_progress()` was called
- But `percentage` was never set, stayed at 0%
- Discord callback checked percentage and saw 0%, showed "Preparing..."

**Fix:**
```python
# NEW CODE (FIXED)
if self._current_step_sequence == 0:
    step_percentage = (current / total) * 100
    self.state.metrics.percentage = min(95, step_percentage)  # ✅ Set percentage!
else:
    # For multi-sequence
    estimated_sequences = 4
    sequence_weight = 100 / estimated_sequences
    current_seq_progress = (current / total) * sequence_weight
    previous_seq_progress = self._current_step_sequence * sequence_weight
    self.state.metrics.percentage = min(95, previous_seq_progress + current_seq_progress)  # ✅ Set percentage!
```

---

### Bug 2: Not Using update_step_progress() Method

**Location:** `core/generators/image.py` line 372-375

**Problem:**
```python
# OLD CODE (BROKEN)
if step_total > 0:
    percentage = (step_current / step_total) * 100
    tracker.state.metrics.percentage = min(95, percentage)  # ❌ Manually set
    tracker.state.phase = f"Step {step_current}/{step_total}"  # ❌ Wrong format
```

**Impact:**
- Bypassed the proper `update_step_progress()` method
- Didn't trigger `_first_step_reached` flag
- Percentage calculation duplicated and inconsistent

**Fix:**
```python
# NEW CODE (FIXED)
if step_total > 0 and step_current > 0:
    # Mark as running if not already
    if tracker.state.status != ProgressStatus.RUNNING:
        tracker.update_execution_start()
    
    # Use the proper method that handles everything
    tracker.update_step_progress(step_current, step_total)  # ✅ Proper method!
```

---

## How Progress Tracking Works Now

### 1. WebSocket Receives Step Data
```
ComfyUI → WebSocket message: {"type": "progress", "value": 5, "max": 30}
    ↓
WebSocket handler updates: ws_data['step_current'] = 5, ws_data['step_total'] = 30
```

### 2. ImageGenerator Polls Progress
```
_wait_for_completion() loop (every 1 second):
    ↓
ws_data = self.websocket.get_generation_data(prompt_id)
    ↓
tracker.update_step_progress(5, 30)  # ✅ Uses proper method
    ↓
tracker.state.metrics.percentage = 16.7%  # ✅ Calculated correctly
tracker.state.phase = "Sampling (5/30)"   # ✅ Proper format
```

### 3. Discord Callback Updates Message
```
await progress_callback(tracker)
    ↓
Checks: tracker.state.metrics.percentage = 16.7%  # ✅ Now has value!
    ↓
Creates embed: "Progress: 16.7% - Sampling (5/30)"
    ↓
await message.edit(embed=embed)  # ✅ Discord message updates!
```

---

## Files Modified

| File | Lines Changed | Fix |
|------|---------------|-----|
| `core/progress/tracker.py` | 203, 210 | Set `percentage` in `update_step_progress()` |
| `core/generators/image.py` | 370-378 | Use `tracker.update_step_progress()` method |
| `core/progress/callbacks.py` | 42-43, 104-110, 151-156 | Improved logging & timing |

**Total:** 3 files, ~15 lines changed

---

## Progress Flow

```
┌─────────────────────────────────────────────────────────┐
│ ComfyUI Generation Running                              │
│ Step 5/30 in KSampler node                              │
└───────────────────────┬─────────────────────────────────┘
                        │
                        │ WebSocket message
                        ↓
┌─────────────────────────────────────────────────────────┐
│ WebSocket Handler (core/comfyui/websocket.py)          │
│ progress_data['step_current'] = 5                       │
│ progress_data['step_total'] = 30                        │
└───────────────────────┬─────────────────────────────────┘
                        │
                        │ Polling (1 sec)
                        ↓
┌─────────────────────────────────────────────────────────┐
│ ImageGenerator._wait_for_completion()                   │
│ ws_data = websocket.get_generation_data(prompt_id)     │
│ tracker.update_step_progress(5, 30)  ✅                 │
└───────────────────────┬─────────────────────────────────┘
                        │
                        │ Method call
                        ↓
┌─────────────────────────────────────────────────────────┐
│ ProgressTracker.update_step_progress()                  │
│ percentage = (5 / 30) * 100 = 16.7%                     │
│ state.metrics.percentage = 16.7%  ✅                     │
│ state.phase = "Sampling (5/30)"                         │
└───────────────────────┬─────────────────────────────────┘
                        │
                        │ Callback (1 sec)
                        ↓
┌─────────────────────────────────────────────────────────┐
│ Discord Progress Callback                               │
│ percentage = tracker.state.metrics.percentage = 16.7%   │
│ embed.add_field("Progress", "16.7% - Sampling (5/30)") │
│ await message.edit(embed=embed)  ✅                      │
└───────────────────────┬─────────────────────────────────┘
                        │
                        │ Discord API
                        ↓
┌─────────────────────────────────────────────────────────┐
│ Discord Message Updated                                 │
│ "🎨 Image Generation - Running"                         │
│ "Progress: 16.7% - Sampling (5/30)"                     │
└─────────────────────────────────────────────────────────┘
```

---

## Expected Behavior

### Before Fix ❌
```
Discord Message:
🎨 Image Generation
Progress: 0.0% - Preparing...

[Never updates, stuck at 0%]
```

### After Fix ✅
```
Discord Message (updates every second):

🎨 Image Generation - Running
Progress: 3.3% - Sampling (1/30)

🎨 Image Generation - Running
Progress: 16.7% - Sampling (5/30)

🎨 Image Generation - Running
Progress: 50.0% - Sampling (15/30)

🎨 Image Generation - Running
Progress: 83.3% - Sampling (25/30)

🎨 Image Generation - Running
Progress: 93.3% - Sampling (28/30)

[Message deleted, image appears]
```

---

## Testing Checklist

✅ WebSocket connects at startup  
✅ WebSocket receives step messages  
✅ `update_step_progress()` sets percentage  
✅ Progress callback called every 1 second  
✅ Discord message updates with real percentages  
✅ Phase shows "Sampling (X/Y)"  
✅ Progress reaches 90%+ before completion  
✅ Message deleted when complete  

---

## Logging

**WebSocket receiving steps:**
```
📈 Progress for 4bee1045...: 5/30
```

**Progress calculation:**
```
WebSocket progress: 5/30 (16.7%)
```

**Callback invocation:**
```
📊 Calling progress callback: 16.7% - Sampling (5/30)
```

**Discord update:**
```
✅ Updated Discord progress: 16.7% - Sampling (5/30)
```

---

## Root Cause Analysis

### Why Did This Happen?

1. **Copy-paste error** in `ProgressTracker.update_step_progress()`:
   - Calculated `step_percentage` but forgot to assign it
   - Only set `current_step`, not `percentage`

2. **Inconsistent API usage** in `ImageGenerator`:
   - Directly set `tracker.state.metrics.percentage` instead of calling method
   - Bypassed the proper initialization logic

### Prevention

- ✅ Use methods instead of direct state manipulation
- ✅ Follow the API patterns from old working code
- ✅ Test with real Discord messages, not just CLI logs

---

## Summary

**Two critical bugs fixed:**
1. ✅ `ProgressTracker.update_step_progress()` now sets `percentage`
2. ✅ `ImageGenerator` now calls proper `update_step_progress()` method

**Result:**
- Discord messages update in real-time
- Shows accurate step-based progress
- Users see live feedback during generation

**Progress tracking now works exactly like v1.4.0!** 🎉

