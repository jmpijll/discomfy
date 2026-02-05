# Known Issues

This document tracks known issues and limitations in DisComfy.

---

## Known Limitations

### Progress Bar Accuracy for Multi-Sampler Workflows
**Status**: ⚠️ **Known Limitation**

Workflows with multiple KSampler nodes (such as Qwen Image 2512 with its hi-res fix pass) may show progress percentage that resets or jumps during generation. This is because ComfyUI only provides per-node step progress, not workflow-level completion percentage. The progress bar remains accurate within each sampling pass but may appear to reset between passes.

**Workaround**: The generation is progressing normally even if the percentage fluctuates. The final result will be delivered correctly.

---

### Recently Resolved Issues

#### ✅ Concurrent Queue Handling Bug (Fixed in v1.4.0)
**Status**: ✅ **RESOLVED** in v1.4.0 (October 31, 2025)

The concurrent generation hanging bug has been completely fixed. Multiple users can now generate images simultaneously without any issues.

---

## Reporting Issues

If you encounter a bug or issue:

1. **Check Documentation**: Review `README.md` and troubleshooting sections
2. **Check Logs**: Review `logs/bot.log` for error messages
3. **Search Issues**: Check if the issue was already reported on [GitHub Issues](https://github.com/jmpijll/discomfy/issues)
4. **Create Issue**: Report new issues with:
   - Detailed description
   - Steps to reproduce
   - Error messages/logs
   - Bot version and environment details

---

## Notes

Last Updated: February 5, 2026  
Current Version: v2.2.0
