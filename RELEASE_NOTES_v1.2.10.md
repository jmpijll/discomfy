# Release Notes - DisComfy v1.2.10

**Release Date:** October 3, 2025  
**Type:** Critical Bug Fix

---

## 🐛 Critical Queue Handling Fix

This release addresses a critical bug that prevented proper handling of multiple concurrent generation requests. The bot now correctly manages ComfyUI's queue system and provides accurate progress updates for each generation.

---

## What's Fixed

### Queued Generation Progress
- **Issue:** Generations started while another was running would never show progress percentages, only elapsed time
- **Fix:** Removed `?clientId` parameter from WebSocket connections that was blocking message reception
- **Result:** Queued generations now properly receive and display progress updates when they start running

### Completion Detection
- **Issue:** Completed generations weren't detected by Discord until a new generation was started
- **Fix:** WebSocket now receives all messages and properly detects when each generation completes
- **Result:** Generations complete and show results immediately without needing another generation to trigger detection

### WebSocket Client Filtering
- **Issue:** ComfyUI was filtering WebSocket messages per client_id, preventing queued generations from receiving any messages
- **Fix:** WebSocket connects without client filtering, receives ALL messages, and filters by prompt_id instead
- **Result:** Each generation's WebSocket can see when its specific prompt starts executing and receive its progress messages

### Progress Message Filtering
- **Issue:** Multiple WebSocket connections would all receive progress messages, causing confusion
- **Fix:** Added `currently_executing_prompt` tracking to only apply progress updates for the actually running prompt
- **Result:** Each generation only responds to progress messages for its own execution

---

## Technical Changes

### WebSocket Connection
- **Removed** `?clientId={client_id}` parameter from WebSocket URL (line 602)
- WebSocket now connects to base URL without client filtering
- Allows reception of ALL messages from ComfyUI for proper filtering

### Progress Tracking
- Added `currently_executing_prompt` variable to track which prompt is actively running
- `executing` messages update this variable when a new prompt starts
- Progress messages only applied when `currently_executing_prompt == prompt_id`
- Prevents cross-contamination between concurrent generations

### Message Filtering
- Each WebSocket receives ALL ComfyUI messages (broadcast mode)
- `executing` messages filtered by prompt_id to detect when our prompt starts
- `progress` messages only applied when our prompt is confirmed as running
- `execution_cached` messages properly filtered by prompt_id
- Enhanced logging tracks prompt execution state transitions

### Root Cause Analysis
The bug was caused by including `?clientId={client_id}` in the WebSocket connection URL. This made ComfyUI filter messages to only that specific client, which prevented queued generations from receiving:
1. `executing` messages when their prompt started
2. `progress` messages during their generation
3. Completion signals when they finished

By connecting without the client filter and implementing prompt_id-based filtering instead, each WebSocket can properly track its own generation's progress.

---

## Impact

### Before This Fix
```
User A: Starts generation → Shows progress ✅
User B: Starts generation while A is running → Hangs indefinitely ❌
User A: Generation completes → Results appear
User B: Generation starts → Hangs again ❌
Bot restart required to resolve
```

### After This Fix
```
User A: Starts generation → Shows progress ✅
User B: Starts generation while A is running → Shows "Queued #1" ✅
User A: Generation completes → Results appear ✅
User B: Status changes to "Generating" → Shows progress ✅
User B: Generation completes → Results appear ✅
```

---

## Upgrade Instructions

### Standard Upgrade
```bash
cd discomfy
git pull origin main
# Restart the bot
```

### From Git Repository
```bash
cd discomfy
git fetch --all --tags
git checkout tags/v1.2.10
# Restart the bot
```

### No Configuration Changes Required
This release only contains bug fixes - no configuration changes needed!

---

## Testing Recommendations

After upgrading, test the fix with these scenarios:

### Test 1: Sequential Generations
1. User A starts an image generation
2. User B starts a generation while A's is running
3. Verify User B sees "Queued" status
4. Wait for User A's generation to complete
5. Verify User B's status changes to "Generating"
6. Verify User B's generation completes successfully

### Test 2: Multiple Users
1. Start generations from 3 different users in quick succession
2. Verify each shows proper queue position
3. Verify progress updates only show for the currently running generation
4. Verify all generations complete successfully

### Test 3: Video Generation
1. Start a video generation (takes 5-15 minutes)
2. Start an image generation while video is processing
3. Verify image generation shows "Queued" status
4. Verify it processes after video completes

---

## Known Issues

None currently identified in this release.

---

## Support

If you encounter any issues:
1. Check the bot logs for error messages
2. Verify ComfyUI is running and accessible
3. Restart the bot if needed
4. Report issues on GitHub with detailed logs

---

## Credits

This fix resolves the primary concurrent generation issue reported by users and identified through extensive debugging of the WebSocket progress tracking system.

---

**Previous Release:** [v1.2.9 - Concurrent Generation Progress Tracking](RELEASE_NOTES_v1.2.9.md)

**Full Changelog:** [CHANGELOG.md](CHANGELOG.md)

