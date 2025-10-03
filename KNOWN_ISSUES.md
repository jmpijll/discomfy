# Known Issues

## Concurrent Queue Handling (v1.2.11)

**Status**: Known Issue - Deferred  
**Severity**: Medium  
**Affects**: Concurrent generation tracking

### Issue
When multiple users start generations simultaneously (Gen A, Gen B), the second generation (Gen B) does not show completion in Discord until a third generation is started.

**Symptoms**:
- Gen A: Works perfectly ✅
- Gen B (while A running): Shows progress, but never completes in Discord ❌
- Gen C started: Gen B suddenly shows as complete, Gen C gets stuck ❌
- Single generation tracking: Works perfectly ✅

**Technical Details**:
- Persistent WebSocket is implemented and connected
- Progress tracking works correctly (real-time percentages, step counts)
- Completion detection via WebSocket works
- HTTP polling completion detection works
- Issue appears to be in the interaction between multiple concurrent async contexts

**Workaround**:
Users should wait for current generation to complete before starting a new one.

**Investigation Needed**:
- Async context manager lifecycle with concurrent requests
- Discord interaction response timing
- Progress callback execution across concurrent tasks

**Priority**: Medium (affects concurrent users, but single-user workflow works)

---

## Notes

Last Updated: October 4, 2025  
Version: 1.2.11

