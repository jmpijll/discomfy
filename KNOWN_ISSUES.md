# Known Issues

This document tracks known issues and limitations in DisComfy.

---

## 🎉 No Known Issues!

**Current Status**: All previously reported issues have been resolved!

### Recently Resolved Issues

#### ✅ Concurrent Queue Handling Bug (Fixed in v1.4.0)
**Status**: ✅ **RESOLVED** in v1.4.0 (October 31, 2025)

The concurrent generation hanging bug has been completely fixed. Multiple users can now generate images simultaneously without any issues.

**Solution**: WebSocket initialization moved to bot startup instead of per-generation. See [RELEASE_NOTES_v1.4.0.md](RELEASE_NOTES_v1.4.0.md) for details.

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

Last Updated: October 31, 2025  
Current Version: v1.4.0
