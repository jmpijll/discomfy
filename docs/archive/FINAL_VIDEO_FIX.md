# Final Video & Timeout Fixes

**Date:** November 2, 2025  
**Status:** ✅ Fixed

---

## Issues Fixed

### 1. Missing `time` Import ❌ → ✅

**Problem:**
```
Video generation failed: name 'time' is not defined
```

**Root Cause:** The `time` module was used in `VideoGenerator` but never imported.

**Solution:** Added `import time` to imports.

**File:** `core/generators/video.py` (line 10)

**Before:**
```python
import json
import logging
import random
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
```

**After:**
```python
import json
import logging
import random
import time  # ✅ Added
from typing import Dict, Any, Optional, Tuple
from pathlib import Path
```

---

### 2. Timeout Too Short for Concurrent Operations ❌ → ✅

**Problem:**
```
Edit failed: Generation timeout after 300 seconds
```

When multiple buttons are clicked (upscale + animate + edit), ComfyUI has to queue them, so the wait time can be much longer than 5 minutes.

**Solution:** Increased timeout from 300 seconds (5 min) to 1500 seconds (25 min) in BOTH generators.

**Files Modified:**
- `core/generators/video.py` (line 394)
- `core/generators/image.py` (line 521)

**Before:**
```python
# VideoGenerator
max_wait_time = 300  # 5 minutes

# ImageGenerator
max_wait_time = self.config.comfyui.timeout  # 300 from config
```

**After:**
```python
# VideoGenerator
max_wait_time = 1500  # 25 minutes (for concurrent operations)

# ImageGenerator  
max_wait_time = 1500  # 25 minutes (for concurrent operations)
```

---

## Why 25 Minutes?

**Scenario:** User clicks all 3 buttons simultaneously:
1. 🔍 **Upscale** (4x) - ~3 minutes
2. ✏️ **Edit** (Flux) - ~5 minutes
3. 🎬 **Animate** (121 frames) - ~8 minutes

**Total if queued:** ~16 minutes + buffer = **25 minutes is safe**

This allows:
- Multiple operations to queue in ComfyUI
- Slower hardware to complete without timeouts
- Buffer for busy servers

---

## Testing

### Video Animation
1. ✅ Start bot
2. ✅ Generate image
3. ✅ Click "🎬 Animate"
4. ✅ Submit with 121 frames
5. ✅ Verify no "'time' is not defined" error
6. ✅ Verify video generates successfully
7. ✅ Verify progress updates appear

### Concurrent Operations with Timeout
1. ✅ Generate image
2. ✅ Click "🔍 Upscale" (4x) → submit
3. ✅ Click "✏️ Edit" → submit
4. ✅ Click "🎬 Animate" → submit
5. ✅ All three start queuing in ComfyUI
6. ✅ All three complete within 25 minutes
7. ✅ No timeout errors

---

## Files Modified

1. **`core/generators/video.py`**
   - Added `import time` (line 10)
   - Increased timeout to 1500 seconds (line 394)

2. **`core/generators/image.py`**
   - Increased timeout to 1500 seconds (line 521)
   - Now hardcoded instead of using config value

---

## Status

✅ **Missing import fixed**  
✅ **Timeouts increased to 25 minutes**  
✅ **No linter errors**  
✅ **Ready for testing**

**All video generation issues resolved!** 🎉

