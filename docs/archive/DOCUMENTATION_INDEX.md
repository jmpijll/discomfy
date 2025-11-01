# DisComfy Documentation Index

Quick reference for finding documentation.

---

## 📋 Active Refactoring Documents (Root Directory)

**Read these for completing v2.0:**

- `NEXT_STEPS.md` - **START HERE** - Immediate action items
- `TESTING_CHECKLIST.md` - Comprehensive testing procedure
- `V2_SUMMARY.md` - Quick summary and status
- `REFACTORING_ASSESSMENT.md` - Detailed analysis and findings
- `REFACTORING_PROPOSAL_V2.0.md` - Original proposal (reference)

---

## 📖 Production Documentation (`/docs/`)

**For users and developers:**

- `API.md` - API documentation
- `MIGRATION_GUIDE.md` - How to migrate to v2.0
- `USAGE_EXAMPLES.md` - Practical usage examples
- `TESTING_GUIDE.md` - Testing guide
- `UNRAID_SETUP.md` - UnRAID setup instructions
- `GUIDELINES.md` - Development guidelines
- `PROJECT_PLAN.md` - Project structure and plan
- `README_V2.md` - v2.0 README
- `V2.0_RELEASE_NOTES.md` - v2.0 release notes
- `RELEASE_NOTES_v1.4.0.md` - v1.4.0 release notes

---

## 📦 Historical Archive (`/docs/archive/`)

**Historical documentation from refactoring:**

### Phase Progress (`/docs/archive/phases/`)
- All `PHASE*.md` files - Progress tracking for each phase

### Status Reports (`/docs/archive/`)
- `FINAL_STATUS.md`
- `INTEGRATION_STATUS.md`
- `REFACTORING_COMPLETE.md`
- `REFACTORING_FINAL_STATUS.md`
- `REFACTORING_PROGRESS_REPORT.md`
- `REFACTORING_STATUS.md`

### Technical Archives (`/docs/archive/`)
- `CLAUDE.md` - Historical notes
- `CONCURRENT_QUEUE_FIX_RESEARCH.md`
- `WEBSOCKET_BUG_*.md` - WebSocket debugging docs
- `RELEASE_NOTES_v1.2.*.md` - Old release notes
- `RELEASE_NOTES_v1.3.*.md` - Old release notes

See: `/docs/archive/README.md` for full index

---

## 🚀 Quick Navigation

### I want to...

**Complete the v2.0 refactoring:**
→ Start with `NEXT_STEPS.md`

**Test the bot before merging:**
→ Use `TESTING_CHECKLIST.md`

**Understand what was done:**
→ Read `V2_SUMMARY.md` (quick) or `REFACTORING_ASSESSMENT.md` (detailed)

**Learn how to use the bot:**
→ Check `/docs/USAGE_EXAMPLES.md`

**Migrate from v1.4:**
→ Read `/docs/MIGRATION_GUIDE.md`

**Understand the API:**
→ See `/docs/API.md`

**Review historical progress:**
→ Browse `/docs/archive/phases/`

**Check old issues:**
→ Look in `/docs/archive/`

---

## 📁 Project Structure

```
discomfy/
├── README.md                           # Main readme
├── CHANGELOG.md                        # Change history
├── KNOWN_ISSUES.md                     # Known issues
├── 
├── NEXT_STEPS.md                       # ← START HERE for v2.0
├── TESTING_CHECKLIST.md                # Testing guide
├── V2_SUMMARY.md                       # Quick summary
├── REFACTORING_ASSESSMENT.md           # Detailed analysis
├── REFACTORING_PROPOSAL_V2.0.md        # Original plan
├── DOCUMENTATION_INDEX.md              # This file
├── 
├── bot/                                # Bot code (v2.0)
├── core/                               # Core modules (v2.0)
├── config/                             # Configuration (v2.0)
├── utils/                              # Utilities (v2.0)
├── tests/                              # Test suite
├── workflows/                          # ComfyUI workflows
├── 
├── docs/                               # Production documentation
│   ├── *.md                           # User guides
│   └── archive/                       # Historical docs
│       ├── phases/                    # Phase progress
│       └── *.md                       # Status reports
├── 
├── main.py                            # Entry point (v2.0)
├── bot.py                             # Legacy entry point
├── image_gen.py                       # Legacy generator
└── video_gen.py                       # Video generator
```

---

## 🎯 Current Focus

**Status:** v2.0 refactoring at 85% complete  
**Next:** Integration testing (see `NEXT_STEPS.md`)  
**Timeline:** 1-2 weeks to production

---

*Last Updated: November 1, 2025*

