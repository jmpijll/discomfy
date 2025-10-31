# Release Notes - DisComfy v1.2.9

**Release Date:** October 3, 2025  
**Type:** Bug Fix - Concurrent Generation Progress Tracking

---

## 🐛 Concurrent Generation Progress Tracking Fix

This release improves progress tracking for concurrent generation requests by enhancing HTTP polling to work reliably when WebSocket message filtering prevents proper progress updates.

---

## What's Fixed

### HTTP Polling Progress Extraction
- **Issue:** Queued generations showed only elapsed time, no progress percentage
- **Fix:** Enhanced HTTP polling to extract actual progress data from ComfyUI's queue endpoint
- **Result:** Queued generations now show real progress data when WebSocket is unavailable

### WebSocket Fallback Logic
- **Issue:** Code fell back to time-based estimation immediately when WebSocket had no data
- **Fix:** Added intermediate step to try extracting progress from HTTP queue data before time-based fallback
- **Result:** Three-tier fallback: WebSocket → HTTP polling → Time-based estimation

### Completion Detection
- **Issue:** Completed generations weren't detected until a new generation was started
- **Fix:** History endpoint checking continues every second throughout execution
- **Result:** More reliable detection of completed generations

---

## Technical Changes

### Enhanced HTTP Polling (Lines 816-865)
```python
# New logic flow:
1. Check if WebSocket has valid progress data
2. If not, try to extract progress from queue_running items
3. If that fails, use time-based estimation as last resort
```

### Key Improvements
- Added `websocket_has_progress` check to verify WebSocket has actual step data
- HTTP polling now inspects `queue_running` item structure for embedded progress
- Progress extraction from queue data: `item[2]['progress']['value']` and `item[2]['progress']['max']`
- Time-based fallback only activates when no other progress data is available
- WebSocket marked as "best-effort" with note about client_id filtering

### Root Cause Analysis
ComfyUI's WebSocket API uses `?clientId={client_id}` parameter which filters messages per client:
1. Generation A connects with WebSocket using `client_id_A`
2. Generation B (queued) connects with WebSocket using `client_id_B`
3. ComfyUI filters progress messages by client_id
4. Generation B's WebSocket receives no messages because ComfyUI is running A's prompt
5. When B starts running, its WebSocket still doesn't receive messages properly

### Solution Strategy
Instead of trying to fix WebSocket filtering (which would require ComfyUI changes), we:
1. Keep WebSocket as optional "best-effort" for generators that CAN receive messages
2. Make HTTP polling robust enough to work independently
3. Extract actual progress from ComfyUI's `/queue` endpoint when available
4. Use time-based estimation only as last resort

---

## Testing Recommendations

After upgrading, test these scenarios:

### Test 1: Basic Concurrent Queue
```
1. Start Generation A (image)
2. While A is showing progress, start Generation B
3. Expected: B shows "⏳ Queued #1"
4. Expected: A completes and shows results
5. Expected: B status changes to "🎨 Generating"
6. Expected: B shows progress (may be time-based estimate)
7. Expected: B completes and shows results
```

### Test 2: Check Logs for Progress Source
Monitor logs to see which progress mechanism is working:
```
# WebSocket working (first generation):
📊 Applied WebSocket data: steps=15/30, progress: 20.0% -> 50.0%

# HTTP polling working (queued generation):
📊 HTTP polling progress: steps=8/20, progress: 0.0% -> 40.0%

# Time-based fallback (if neither works):
📊 Time-based estimate: 0.0% -> 25.0%
```

### Test 3: Completion Detection
```
1. Start a generation
2. Do NOT start another generation
3. Wait for completion
4. Expected: Results appear immediately after generation finishes
5. Expected: No need to start another generation to trigger detection
```

---

## Known Limitations

### WebSocket Client Filtering
- ComfyUI's WebSocket with `?clientId` parameter filters messages per client
- Queued generations may not receive WebSocket messages
- HTTP polling compensates for this limitation
- Not all ComfyUI versions include progress data in queue endpoint

### Progress Accuracy
- WebSocket provides most accurate progress (when available)
- HTTP polling provides actual progress if ComfyUI version supports it
- Time-based estimation used as fallback (less accurate but better than nothing)

---

## Upgrade Instructions

```bash
cd discomfy
git pull origin main

# Verify version
git describe --tags
# Should show: v1.2.9

# Restart your bot
```

---

## Future Improvements

Potential enhancements for future releases:
1. Implement single shared WebSocket connection for all generations
2. Create bot-side queue system to process requests sequentially
3. Explore ComfyUI API extensions for better concurrent support
4. Add configuration option to disable WebSocket entirely

---

## Support

If progress tracking still doesn't work correctly:
1. Check bot logs for error messages
2. Note which progress mechanism is being used (WebSocket/HTTP/Time-based)
3. Check your ComfyUI version and API capabilities
4. Report issue with detailed logs

---

**Previous Release:** [v1.2.8 - Dual Image Editing Models](RELEASE_NOTES_v1.2.8.md)

**Full Changelog:** [CHANGELOG.md](CHANGELOG.md)

