# Phase 5: Migration & Cleanup Plan

**Date:** November 2025  
**Status:** Ready to begin

---

## Migration Strategy

### Step 1: Update Imports in New Code
**Priority:** 🔴 HIGH  
**Effort:** 1 day

- [ ] Update `bot/ui/` components to use new imports
- [ ] Update `bot/commands/` to use new imports
- [ ] Remove dependencies on old `image_gen.py` imports where possible
- [ ] Test all imports work correctly

### Step 2: Remove Duplicate Code
**Priority:** 🔴 HIGH  
**Effort:** 1 day

- [ ] Identify duplicate functions between old and new code
- [ ] Remove duplicates from old code (keep in new modules)
- [ ] Update old code to import from new modules
- [ ] Verify no functionality is lost

### Step 3: Deprecate Old Entry Points
**Priority:** 🟡 MEDIUM  
**Effort:** 0.5 day

- [ ] Add deprecation warnings to old `bot.py` main
- [ ] Update README to recommend `main.py`
- [ ] Keep `bot.py` functional but mark as deprecated

### Step 4: Performance Optimization
**Priority:** 🟡 MEDIUM  
**Effort:** 2 days

- [ ] Profile bot performance
- [ ] Optimize hot paths
- [ ] Improve caching strategies
- [ ] Benchmark improvements

### Step 5: Final Cleanup
**Priority:** 🟢 LOW  
**Effort:** 0.5 day

- [ ] Code formatting (black, isort)
- [ ] Final linting pass
- [ ] Remove unused imports
- [ ] Update all docstrings

---

## Cleanup Tasks

### Files to Clean Up
1. `bot.py` - Update to use new modules, mark deprecated sections
2. `image_gen.py` - Remove duplicate functions, update to use new modules
3. `video_gen.py` - Update to use new architecture
4. Remove any unused utility functions

### Import Updates Needed
- Update all `from image_gen import` to use new modules where appropriate
- Update all `from video_gen import` to use new modules
- Ensure all new code uses v2.0 imports

---

## Migration Checklist

### Pre-Migration
- [x] All Phase 4 tests passing
- [x] Documentation complete
- [ ] Backup current codebase
- [ ] Create migration branch

### During Migration
- [ ] Update imports incrementally
- [ ] Test after each change
- [ ] Verify backward compatibility
- [ ] Run full test suite

### Post-Migration
- [ ] All tests passing
- [ ] No linter errors
- [ ] Performance benchmarks meet targets
- [ ] Documentation updated
- [ ] Version bump to v2.0

---

## Risk Mitigation

1. **Keep old code working** - Don't remove until fully migrated
2. **Test incrementally** - Test after each change
3. **Maintain fallback** - Keep old entry points available
4. **Document changes** - Update docs as we migrate

---

**Ready to begin Phase 5 migration!**

