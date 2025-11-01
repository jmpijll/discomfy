# DisComfy v2.0 - Testing Checklist

**Version:** 2.0  
**Date:** November 1, 2025  
**Purpose:** Pre-merge verification checklist

---

## Quick Start

This checklist ensures v2.0 is production-ready before merging to main.

**Estimated Time:** 2-4 hours  
**Required:** Discord server with bot, ComfyUI running

---

## Prerequisites

### 1. Environment Setup
```bash
cd /Users/jamievanderpijll/discomfy

# Ensure you're on the refactor branch
git branch
# Should show: * v2.0-refactor

# Check Python version (need 3.10+)
python3 --version

# Install/verify dependencies
pip install -r requirements.txt
```

### 2. Configuration
```bash
# Ensure config.json exists
ls -la config.json

# Ensure ComfyUI is running
curl http://localhost:8188/system_stats
# Should return JSON with system info
```

---

## Testing Procedure

### Part 1: Basic Startup (5 minutes)

#### Test 1.1: Bot Starts Successfully
```bash
# Start the bot
python3 main.py

# Expected output:
# ✅ Configuration validation passed
# ✅ Setting up bot...
# ✅ Bot setup completed successfully
# ✅ Bot logged in as [BotName] (ID: xxxxx)
# ✅ Connected to X guild(s)
```

**Result:** [ ] PASS / [ ] FAIL

**If FAIL:** Check error message and fix before continuing.

---

### Part 2: Command Testing (15 minutes)

Test each command in Discord. Record results below.

#### Test 2.1: /generate (Basic Image)
```
Command: /generate prompt:"a beautiful sunset over mountains"

Expected:
✅ Bot responds immediately with setup view
✅ Configuration buttons appear
✅ "Generate" button works
✅ Progress updates appear (every 1-2 seconds)
✅ Final image displays
✅ Action buttons appear (Upscale, Variations, etc.)
```

**Result:** [ ] PASS / [ ] FAIL  
**Notes:** ___________________________________

---

#### Test 2.2: /generate (With Image - Video Mode)
```
Command: /generate prompt:"animate this" image:[upload any image]

Expected:
✅ Bot responds with video mode message
✅ (If implemented) Video generation starts
✅ (If not) "Coming soon" message appears
```

**Result:** [ ] PASS / [ ] FAIL / [ ] N/A  
**Notes:** ___________________________________

---

#### Test 2.3: /editflux
```
Command: /editflux image:[upload] prompt:"make it blue" steps:20

Expected:
✅ Bot validates image
✅ Edit starts immediately
✅ Progress updates appear
✅ Edited image displays
✅ Action buttons work
```

**Result:** [ ] PASS / [ ] FAIL  
**Notes:** ___________________________________

---

#### Test 2.4: /editqwen
```
Command: /editqwen image:[upload] prompt:"change the background"

Expected:
✅ Bot validates image
✅ Edit starts
✅ Progress updates
✅ Result displays
```

**Result:** [ ] PASS / [ ] FAIL  
**Notes:** ___________________________________

---

#### Test 2.5: /status
```
Command: /status

Expected:
✅ Shows bot status (online)
✅ Shows ComfyUI connection status
✅ Shows queue information
✅ Response time < 2 seconds
```

**Result:** [ ] PASS / [ ] FAIL  
**Notes:** ___________________________________

---

#### Test 2.6: /help
```
Command: /help

Expected:
✅ Shows help embed
✅ Lists all commands
✅ Shows usage examples
✅ Provides links to documentation
```

**Result:** [ ] PASS / [ ] FAIL  
**Notes:** ___________________________________

---

#### Test 2.7: /loras
```
Command: /loras

Expected:
✅ Lists available LoRAs
✅ Shows LoRA names
✅ Formatted nicely
```

**Result:** [ ] PASS / [ ] FAIL  
**Notes:** ___________________________________

---

### Part 3: Error Handling (10 minutes)

#### Test 3.1: Invalid Prompt
```
Command: /generate prompt:""

Expected:
✅ Error message appears
✅ Message is user-friendly
✅ Explains what's wrong
```

**Result:** [ ] PASS / [ ] FAIL  
**Notes:** ___________________________________

---

#### Test 3.2: Invalid Image
```
Command: /editflux image:[upload .txt file] prompt:"test"

Expected:
✅ Validation fails
✅ Error message: "Please upload a valid image file"
✅ Bot doesn't crash
```

**Result:** [ ] PASS / [ ] FAIL  
**Notes:** ___________________________________

---

#### Test 3.3: Rate Limiting
```
Action: Send 15 /generate commands rapidly (within 10 seconds)

Expected:
✅ First 10 succeed
✅ Next 5 get rate limit message
✅ Message tells user to wait
✅ Bot doesn't crash
```

**Result:** [ ] PASS / [ ] FAIL  
**Notes:** ___________________________________

---

### Part 4: UI Interactions (10 minutes)

#### Test 4.1: Generation Setup View
```
1. Use /generate with any prompt
2. Click various configuration buttons
3. Change settings
4. Click "Generate"

Expected:
✅ All buttons respond
✅ Settings update correctly
✅ Only command author can interact
✅ Others get "Only the command author" message
✅ View times out after 5 minutes
```

**Result:** [ ] PASS / [ ] FAIL  
**Notes:** ___________________________________

---

#### Test 4.2: Post-Generation Actions
```
1. Generate an image
2. Click "Upscale" button
3. Wait for upscale
4. Try "Variations" button
5. Try "Similar" button

Expected:
✅ Each button works
✅ New generations start
✅ Progress updates work
✅ Results display correctly
```

**Result:** [ ] PASS / [ ] FAIL  
**Notes:** ___________________________________

---

### Part 5: Concurrent Operations (15 minutes)

#### Test 5.1: Multiple Users
```
Action: Have 3 different users run /generate simultaneously

Expected:
✅ All three queue successfully
✅ Queue positions show correctly
✅ All three complete
✅ No interference between users
✅ No errors in logs
```

**Result:** [ ] PASS / [ ] FAIL  
**Notes:** ___________________________________

---

#### Test 5.2: Same User Multiple Generations
```
Action: One user starts 3 generations quickly (1-2 seconds apart)

Expected:
✅ All queue successfully
✅ Progress updates don't mix
✅ All complete successfully
✅ Buttons work on each result
```

**Result:** [ ] PASS / [ ] FAIL  
**Notes:** ___________________________________

---

### Part 6: Performance Testing (20 minutes)

#### Test 6.1: Startup Time
```bash
# Restart bot and time it
time python3 main.py
# (Stop with Ctrl+C after "Bot logged in")

Target: < 3 seconds
```

**Actual Time:** __________ seconds  
**Result:** [ ] PASS (< 3s) / [ ] FAIL  
**Notes:** ___________________________________

---

#### Test 6.2: Command Response Time
```
Action: Use /generate and note time until first response

Expected: < 100ms (nearly instant)
```

**Actual Time:** __________ ms  
**Result:** [ ] PASS / [ ] FAIL  
**Notes:** ___________________________________

---

#### Test 6.3: Memory Usage
```bash
# Start bot
python3 main.py &
BOT_PID=$!

# Check initial memory (Mac)
ps -o rss,vsz,comm -p $BOT_PID

# Or use htop/Activity Monitor
# Generate 10 images
# Check memory again
# Should not grow significantly (max 50MB increase)
```

**Initial Memory:** __________ MB  
**After 10 Generations:** __________ MB  
**Increase:** __________ MB  
**Result:** [ ] PASS (< 50MB increase) / [ ] FAIL  
**Notes:** ___________________________________

---

#### Test 6.4: Long-Running Stability
```
Action: Leave bot running for 1 hour with periodic generations

Expected:
✅ No crashes
✅ No memory leaks
✅ Response times stay consistent
✅ No connection drops
```

**Result:** [ ] PASS / [ ] FAIL  
**Notes:** ___________________________________

---

### Part 7: Edge Cases (15 minutes)

#### Test 7.1: Very Long Prompt
```
Command: /generate prompt:"[1000 character prompt]"

Expected:
✅ Validation catches it (if > max length)
✅ Or truncates gracefully
✅ User-friendly error
```

**Result:** [ ] PASS / [ ] FAIL  
**Notes:** ___________________________________

---

#### Test 7.2: Special Characters in Prompt
```
Command: /generate prompt:"test 🎨 emoji & special < > / \ chars"

Expected:
✅ Handles gracefully
✅ No crashes
✅ Generates correctly
```

**Result:** [ ] PASS / [ ] FAIL  
**Notes:** ___________________________________

---

#### Test 7.3: ComfyUI Connection Loss
```
Action:
1. Start generation
2. Stop ComfyUI mid-generation
3. Observe bot behavior

Expected:
✅ Error is caught
✅ User gets friendly error message
✅ Bot doesn't crash
✅ Bot reconnects when ComfyUI restarts
```

**Result:** [ ] PASS / [ ] FAIL  
**Notes:** ___________________________________

---

#### Test 7.4: Button Click After Timeout
```
Action:
1. Use /generate
2. Wait 6 minutes (timeout is 5 minutes)
3. Try to click a button

Expected:
✅ Buttons are disabled
✅ Error message: "This interaction failed"
✅ No bot errors
```

**Result:** [ ] PASS / [ ] FAIL  
**Notes:** ___________________________________

---

### Part 8: Logging & Monitoring (10 minutes)

#### Test 8.1: Log Quality
```bash
# Check logs
tail -f /path/to/logfile.log
# Or check console output

Expected:
✅ Appropriate log levels (INFO, WARNING, ERROR)
✅ Timestamps on all logs
✅ Clear messages
✅ No spam
✅ Errors are logged with stack traces
```

**Result:** [ ] PASS / [ ] FAIL  
**Notes:** ___________________________________

---

#### Test 8.2: Error Handling
```
Action: Trigger various errors and check logs

Expected:
✅ All errors are logged
✅ Stack traces included
✅ User gets friendly message (not raw error)
✅ Bot continues running
```

**Result:** [ ] PASS / [ ] FAIL  
**Notes:** ___________________________________

---

## Test Coverage Report (Optional)

If pytest is available:

```bash
# Install coverage tool
pip install pytest pytest-cov

# Run tests with coverage
python3 -m pytest tests/ --cov=bot --cov=core --cov=config --cov=utils --cov-report=term --cov-report=html

# View results
open htmlcov/index.html
```

**Coverage Achieved:** ___________%  
**Target:** 70%+  
**Result:** [ ] PASS / [ ] FAIL / [ ] SKIPPED

---

## Summary

### Test Results

| Category | Tests | Passed | Failed | Notes |
|----------|-------|--------|--------|-------|
| Startup | 1 | ___ | ___ | |
| Commands | 7 | ___ | ___ | |
| Error Handling | 3 | ___ | ___ | |
| UI Interactions | 2 | ___ | ___ | |
| Concurrent Ops | 2 | ___ | ___ | |
| Performance | 4 | ___ | ___ | |
| Edge Cases | 4 | ___ | ___ | |
| Logging | 2 | ___ | ___ | |
| **TOTAL** | **25** | ___ | ___ | |

### Pass Rate: _____ / 25 (_____%)

**Minimum to Pass: 23/25 (92%)**

---

## Issues Found

| # | Issue Description | Severity | Status | Fix ETA |
|---|-------------------|----------|--------|---------|
| 1 | | | | |
| 2 | | | | |
| 3 | | | | |

---

## Decision

Based on test results:

**[ ] READY TO MERGE**
- All critical tests pass
- Minor issues documented
- Performance meets targets
- Ready for production

**[ ] NOT READY - NEEDS WORK**
- Critical failures found
- Performance issues
- Needs more testing
- See issues table above

**[ ] NEEDS MORE TESTING**
- Some tests skipped
- Need longer stability test
- Need more users to test
- Schedule beta testing

---

## Sign-Off

**Tester:** ___________________  
**Date:** ___________________  
**Time Spent:** ___________ hours  

**Notes:**
```
[Additional notes, observations, or recommendations]
```

---

## Next Steps

### If Ready to Merge:
```bash
# 1. Commit any fixes
git add .
git commit -m "Pre-merge testing complete"

# 2. Final check
git log --oneline -10

# 3. Merge to main
git checkout main
git merge v2.0-refactor
git tag v2.0.0
git push origin main --tags

# 4. Create release notes
# 5. Update README
# 6. Monitor production
```

### If Not Ready:
```bash
# 1. Create issues for failures
# 2. Fix critical issues
# 3. Re-run affected tests
# 4. Repeat until ready
```

---

**End of Checklist**

*Save this file with results for documentation*

