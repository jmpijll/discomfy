# WebSocket Bug Fix - Action Plan

**Date**: October 31, 2025  
**Target Version**: v1.4.0  
**Priority**: High  
**Estimated Effort**: 4-6 hours  

---

## Quick Summary

### The Bug
When two generations run concurrently, the second one completes in ComfyUI but never shows in Discord until a third generation is started. This creates a frustrating user experience where generations appear "stuck."

### Root Cause
The WebSocket connection is being recreated on every generation request due to the `async with self.image_generator` pattern. This causes race conditions and lifecycle mismatches between the WebSocket connection and generation tracking.

### The Fix
Move WebSocket initialization from per-generation context managers to bot startup. Open it once, keep it alive for the bot's lifetime, and properly close on shutdown.

### User's Original Insight
> "I noticed myself that we open the websocket on image generation (so when using image_gen or other), why dont we just open the websocket when starting the bot itself and define it in bot.py, would that not solve the issue?"

**User is 100% correct!** This simple architectural change will solve the bug.

---

## Implementation Steps

### Step 1: Modify `image_gen.py` ⏱️ 2 hours

#### 1.1 Remove Context Manager Pattern
- Remove `__aenter__()` method (lines 285-297)
- Remove `__aexit__()` method (lines 299-307)
- Remove `_ensure_websocket_connected()` method (lines 309-317)

#### 1.2 Add Initialization Method
```python
async def initialize(self):
    """Initialize generator at bot startup."""
    self.logger.info("🎨 Initializing ImageGenerator...")
    
    # Create persistent HTTP session
    self.session = aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=self.config.comfyui.timeout),
        connector=aiohttp.TCPConnector(limit=10, limit_per_host=5)
    )
    
    # Start persistent WebSocket
    ws_url = f"ws://{self.base_url.replace('http://', '').replace('https://', '')}/ws"
    self._websocket_task = asyncio.create_task(self._persistent_websocket_monitor(ws_url))
    
    # Wait for WebSocket to connect (up to 2 seconds)
    for _ in range(20):
        if self._websocket_connected:
            self.logger.info("✅ ImageGenerator initialized successfully")
            return
        await asyncio.sleep(0.1)
    
    self.logger.warning("⚠️ WebSocket not connected after initialization")
```

#### 1.3 Add Shutdown Method
```python
async def shutdown(self):
    """Shutdown generator at bot shutdown."""
    self.logger.info("🛑 Shutting down ImageGenerator...")
    
    # Cancel WebSocket task
    if self._websocket_task and not self._websocket_task.done():
        self._websocket_task.cancel()
        try:
            await self._websocket_task
        except asyncio.CancelledError:
            pass
    
    # Close HTTP session
    if self.session and not self.session.closed:
        await self.session.close()
    
    self.logger.info("✅ ImageGenerator shutdown complete")
```

#### 1.4 Add WebSocket Reconnection Logic
Update `_persistent_websocket_monitor()` to automatically reconnect if connection is lost:
```python
async def _persistent_websocket_monitor(self, ws_url: str):
    """Persistent WebSocket with auto-reconnect."""
    retry_count = 0
    max_retries = 999  # Infinite retries (bot lifetime)
    
    while retry_count < max_retries:
        try:
            import websockets
            full_ws_url = f"{ws_url}?clientId={self._bot_client_id}"
            
            async with websockets.connect(full_ws_url) as websocket:
                self._websocket_connected = True
                retry_count = 0  # Reset on successful connection
                self.logger.info(f"📡 WebSocket CONNECTED for bot session {self._bot_client_id[:8]}...")
                
                # Message processing loop (existing code)
                while True:
                    # ... existing message handling ...
                    
        except websockets.exceptions.WebSocketException as e:
            self._websocket_connected = False
            retry_count += 1
            self.logger.warning(f"📡 WebSocket disconnected: {e}. Reconnecting in 5s...")
            await asyncio.sleep(5)
        except asyncio.CancelledError:
            self.logger.info("📡 WebSocket monitor cancelled")
            raise
        except Exception as e:
            self.logger.error(f"📡 WebSocket error: {e}")
            await asyncio.sleep(5)
```

#### 1.5 Update test_connection()
Change error message from "Use async context manager" to "Call initialize() first"

### Step 2: Modify `bot.py` ⏱️ 1.5 hours

#### 2.1 Update setup_hook()
```python
async def setup_hook(self) -> None:
    """Set up the bot after login."""
    try:
        self.logger.info("Setting up bot...")
        
        # Initialize image generator
        self.image_generator = ImageGenerator()
        await self.image_generator.initialize()  # NEW!
        
        # Initialize video generator  
        self.video_generator = VideoGenerator()
        await self.video_generator.initialize()  # NEW!
        
        # Test ComfyUI connection (no context manager needed)
        if not await self.image_generator.test_connection():
            self.logger.warning("ComfyUI connection test failed - bot will still start")
        
        # ... rest of setup ...
```

#### 2.2 Add close() Method
```python
async def close(self) -> None:
    """Clean shutdown of the bot."""
    self.logger.info("🛑 Bot shutdown initiated...")
    
    # Shutdown generators
    if self.image_generator:
        await self.image_generator.shutdown()
    
    if self.video_generator:
        await self.video_generator.shutdown()
    
    # Call parent close
    await super().close()
    
    self.logger.info("✅ Bot shutdown complete")
```

#### 2.3 Replace Context Manager Usage (15 locations)

**Find and replace**:
```python
# OLD:
async with bot.image_generator as gen:
    images, gen_info = await gen.generate_image(...)

# NEW:
images, gen_info = await bot.image_generator.generate_image(...)
```

**Locations (line numbers may shift during editing)**:
1. Line 85: `setup_hook()` - testing connection
2. Line 461: Generate command
3. Line 675: Generate command with LoRA
4. Line 816: Generate button callback
5. Line 916: Regenerate button callback
6. Line 1394: Generate variations button
7. Line 1620: Video generation
8. Line 1842: Edit Flux command
9. Line 1896: Edit Qwen command
10. Line 2066: Edit button callback
11. Line 2376: Edit regenerate button
12. Line 2692: Upscale button callback
13. Line 2799: Upscale regenerate button
14. Line 2892: Video regenerate button
15. Line 3375: Upscale from edit button

**Strategy**: Use search and replace carefully, one at a time, testing after each change.

### Step 3: Modify `video_gen.py` ⏱️ 30 minutes

Apply the same pattern:
1. Add `initialize()` method
2. Add `shutdown()` method
3. Remove any context manager usage if present

### Step 4: Testing ⏱️ 1 hour

#### 4.1 Basic Functionality Test
```bash
# Start bot
python bot.py

# Expected logs:
# "🎨 Initializing ImageGenerator..."
# "📡 Connecting persistent WebSocket..."
# "📡 WebSocket CONNECTED for bot session..."
# "✅ ImageGenerator initialized successfully"
```

#### 4.2 Single Generation Test
1. Run `/generate prompt:test`
2. Expected: Completes successfully ✅

#### 4.3 Sequential Generation Test
1. Run `/generate prompt:test1`
2. Wait for completion
3. Run `/generate prompt:test2`
4. Expected: Both complete successfully ✅

#### 4.4 Concurrent Generation Test (THE KEY TEST)
1. Run `/generate prompt:concurrent1`
2. Immediately run `/generate prompt:concurrent2`
3. Expected: 
   - Gen 1 shows progress and completes ✅
   - Gen 2 shows "Queued" then progress and completes ✅
   - NO "stuck" generation ✅
   - NO need for Gen 3 to unstick Gen 2 ✅

#### 4.5 Rapid Fire Test
1. Run 5 generations in quick succession
2. Expected: All complete in order ✅

#### 4.6 Bot Shutdown Test
1. Press Ctrl+C
2. Expected logs:
   - "🛑 Bot shutdown initiated..."
   - "🛑 Shutting down ImageGenerator..."
   - "📡 WebSocket monitor cancelled"
   - "✅ ImageGenerator shutdown complete"
   - "✅ Bot shutdown complete"

### Step 5: Documentation ⏱️ 30 minutes

#### 5.1 Update CHANGELOG.md
```markdown
## [1.4.0] - 2025-10-31

### Fixed
- **MAJOR**: Fixed WebSocket lifecycle bug causing second concurrent generation to hang
  - WebSocket now opens once at bot startup instead of per-generation
  - Properly handles concurrent generations from multiple users
  - No more "stuck" generations requiring a third generation to unstick
  - Improved reliability and performance

### Changed
- Refactored ImageGenerator and VideoGenerator to use explicit initialization
- Removed context manager pattern for generators
- Added automatic WebSocket reconnection on disconnect
```

#### 5.2 Update KNOWN_ISSUES.md
Remove the concurrent queue handling issue:
```markdown
# Known Issues

(Empty - all previous issues resolved in v1.4.0!)

---

## Previously Resolved Issues

### Concurrent Queue Handling
**Status**: ✅ Fixed in v1.4.0  
**Issue**: Second concurrent generation would hang until third generation started
**Solution**: Moved WebSocket initialization to bot startup
```

#### 5.3 Create RELEASE_NOTES_v1.4.0.md
Document the fix with:
- User-facing changes
- Technical details
- Migration notes (none needed)
- Testing performed

---

## Rollback Plan

If issues arise:

1. **Quick Rollback** (< 5 minutes):
   ```bash
   git revert HEAD
   python bot.py
   ```

2. **Issues to Watch For**:
   - WebSocket not connecting at startup
   - Generations failing to start
   - Bot not shutting down cleanly

3. **Monitoring**:
   - Watch logs for "📡 WebSocket CONNECTED"
   - Test concurrent generations after deployment
   - Monitor for any error messages

---

## Success Criteria

### Must Have ✅
- [ ] Bot starts successfully with WebSocket connected
- [ ] Single generations work
- [ ] Sequential generations work
- [ ] **Concurrent generations work (no hanging!)**
- [ ] Bot shuts down cleanly

### Should Have ✅
- [ ] WebSocket auto-reconnects on disconnect
- [ ] Performance improvement visible (faster queue times)
- [ ] Clean logs (no errors or warnings)

### Nice to Have ✅
- [ ] Load test with 10+ concurrent users
- [ ] 24-hour uptime test
- [ ] Memory usage monitoring

---

## Communication Plan

### Before Deployment
1. Notify users: "Bot will restart for important concurrent generation fix"
2. Expected downtime: 2-3 minutes
3. Improved feature: "Multiple generations can now run truly concurrently!"

### After Deployment
1. Test with multiple users
2. Monitor for 1 hour
3. Announce success: "Concurrent generation bug fixed! Try it out!"

### If Issues
1. Immediate rollback
2. Notify users: "Reverted to previous version, investigating"
3. Debug and try again

---

## Timeline

### Day 1: Implementation (4-6 hours)
- Morning: Modify image_gen.py (2 hours)
- Afternoon: Modify bot.py (1.5 hours)
- Evening: Modify video_gen.py + Testing (1.5 hours)

### Day 2: Testing & Deployment (2-3 hours)
- Morning: Comprehensive testing (1 hour)
- Afternoon: Documentation (30 minutes)
- Deployment: Live testing (1 hour)
- Monitoring: First 24 hours

---

## Notes

### User's Insight
The user correctly identified the issue:
> "Why don't we just open the websocket when starting the bot itself and define it in bot.py?"

This is **exactly the right solution**. The research confirms it.

### Previous Attempt
v1.2.10 tried to fix this with "persistent WebSocket" but didn't go far enough:
- ✅ Used shared client_id (correct)
- ❌ Kept context manager pattern (incorrect)
- ❌ Session recreation on every generation (incorrect)

### This Fix
Completes what v1.2.10 started:
- ✅ Shared client_id (kept)
- ✅ Removed context manager pattern (fixed)
- ✅ Persistent session throughout bot lifetime (fixed)
- ✅ WebSocket opened once at startup (fixed)

---

## Risk Assessment

### Overall Risk: **LOW** ✅

**Why Low Risk?**
- Simple architectural change
- Reduces complexity (removes context managers)
- Well-tested pattern (similar to original intent)
- Easy rollback (single commit)

**Confidence Level**: **95%** ✅

This fix directly addresses the root cause and aligns with the original design intent from v1.2.10.

---

**Ready to Proceed?** YES ✅

All research is complete. Implementation can begin immediately.

---

**Document Version**: 1.0  
**Author**: AI Assistant  
**Date**: October 31, 2025  

