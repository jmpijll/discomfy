# DisComfy Wiki Setup Guide 📚

Complete guide to setting up and publishing the DisComfy wiki on GitHub.

---

## 📋 What's Included

### Wiki Pages Created
1. **Home.md** - Welcome page with full navigation
2. **Installation-Guide.md** - Complete setup instructions  
3. **Configuration-Guide.md** - Detailed config reference
4. **User-Guide.md** - Complete user documentation
5. **Developer-Guide.md** - Developer and contributor guide
6. **Custom-Workflows.md** - Workflow creation guide
7. **Troubleshooting.md** - Common issues and solutions

### Additional Files
- **publish-wiki.ps1** - Automated publishing script (PowerShell)
- **wiki-docs/README.md** - Documentation about the wiki files

---

## 🚀 Quick Start (2 Steps)

### Step 1: Initialize Wiki on GitHub

Run the helper script:
```powershell
.\publish-wiki.ps1 -Action init
```

This will:
1. Open your browser to the wiki page
2. Show you instructions for creating the first page

**Or do it manually:**
1. Go to https://github.com/jmpijll/discomfy/wiki
2. Click **"Create the first page"**
3. Title: `Home`
4. Copy content from `wiki-docs/Home.md`
5. Click **"Save Page"**

### Step 2: Publish All Pages

After creating the first page:
```powershell
.\publish-wiki.ps1 -Action publish
```

This will:
1. Clone the wiki repository
2. Copy all wiki pages
3. Commit and push to GitHub
4. Open the published wiki in your browser

**Done!** Your wiki is now live at: https://github.com/jmpijll/discomfy/wiki

---

## 📝 Manual Publishing (Alternative)

If you prefer manual control:

### 1. Initialize Wiki
Create first page on GitHub (see Step 1 above)

### 2. Clone Wiki Repository
```powershell
cd ..
git clone https://github.com/jmpijll/discomfy.wiki.git
cd discomfy.wiki
```

### 3. Copy Wiki Files
```powershell
# Copy all pages
Copy-Item ..\discomfy\wiki-docs\*.md . -Exclude README.md

# Check files
dir *.md
```

### 4. Commit and Push
```powershell
git add *.md
git commit -m "Add comprehensive wiki documentation"
git push origin master
```

### 5. Verify
Visit: https://github.com/jmpijll/discomfy/wiki

---

## 🔄 Updating the Wiki

When you make changes to wiki pages:

### Using Script (Recommended)
```powershell
# Edit files in wiki-docs/
# Then run:
.\publish-wiki.ps1 -Action update
```

### Manually
```powershell
# Edit files in wiki-docs/
cd ..\discomfy.wiki

# Copy updated files
Copy-Item ..\discomfy\wiki-docs\*.md . -Exclude README.md

# Commit and push
git add *.md
git commit -m "Update wiki - describe changes"
git push origin master
```

---

## 📚 Wiki Structure

### Navigation Flow
```
Home (Navigation Hub)
  ├── Installation Guide
  │   └── Configuration Guide
  │       └── User Guide
  │
  ├── Developer Guide
  │   ├── Custom Workflows
  │   └── API Reference
  │
  └── Support
      ├── Troubleshooting
      └── FAQ
```

### Internal Links
Pages use `[[Page-Name]]` syntax for linking:
```markdown
See the [[Installation-Guide]] for setup.
Check [[Troubleshooting]] if you have issues.
```

---

## ✨ Wiki Features

### Comprehensive Coverage
- ✅ Installation (all platforms)
- ✅ Configuration (all options)
- ✅ User guide (all features)
- ✅ Developer guide (contributing)
- ✅ Custom workflows (creation guide)
- ✅ Troubleshooting (common issues)
- ✅ Examples and code snippets
- ✅ Best practices

### Well-Organized
- Clear hierarchy
- Consistent formatting
- Abundant examples
- Step-by-step instructions
- Code snippets
- Troubleshooting sections

### User-Friendly
- Easy navigation
- Quick reference tables
- Visual progress indicators
- Practical examples
- Pro tips
- Common pitfalls

---

## 🎯 Maintenance

### Regular Updates
Update wiki when:
- New features added
- Commands changed
- Configuration options updated
- Common issues discovered
- User feedback received

### Process
1. Edit files in `wiki-docs/`
2. Test locally (Markdown preview)
3. Run `.\publish-wiki.ps1 -Action update`
4. Verify on GitHub

### Quality Checks
- Test all code examples
- Verify links work
- Check for outdated info
- Ensure consistency
- Validate formatting

---

## 🔧 Troubleshooting Wiki Setup

### Wiki Repository Not Found
```
Error: repository 'https://github.com/jmpijll/discomfy.wiki.git/' not found
```

**Solution:** Create the first wiki page on GitHub first (Step 1)

### Authentication Required
```
Error: Failed to push to GitHub
```

**Solution:** Authenticate with GitHub CLI:
```powershell
gh auth login
```

Or use HTTPS with credentials when prompted.

### Permission Denied
```
Error: Permission denied (publickey)
```

**Solution:** Set up SSH keys or use HTTPS:
```powershell
git remote set-url origin https://github.com/jmpijll/discomfy.wiki.git
```

### Script Execution Policy
```
Error: cannot be loaded because running scripts is disabled
```

**Solution:** Allow script execution:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

---

## 📖 Best Practices

### Writing Wiki Content

**Do:**
- ✅ Use clear, concise language
- ✅ Include practical examples
- ✅ Add code snippets
- ✅ Link related pages
- ✅ Keep pages focused
- ✅ Update regularly

**Don't:**
- ❌ Use overly technical jargon
- ❌ Create orphan pages
- ❌ Duplicate content
- ❌ Leave broken links
- ❌ Forget to test examples

### Organizing Content

**Guidelines:**
- One topic per page
- Hierarchical structure
- Consistent formatting
- Progressive disclosure
- Cross-reference related topics

---

## 🆘 Getting Help

### Wiki Issues
- Check GitHub wiki documentation
- Review Markdown syntax
- Test locally first
- Create issue if needed

### DisComfy Issues
- Check [[Troubleshooting]] page
- Review logs
- Create GitHub issue
- Include error messages

---

## 🎉 Success!

After publishing, your wiki will be available at:
**https://github.com/jmpijll/discomfy/wiki**

Features:
- ✨ Professional documentation
- 📚 Comprehensive guides
- 🎯 Easy to navigate
- 🔍 Searchable
- 📱 Mobile-friendly
- 🌐 Publicly accessible

---

## 🔗 Resources

- **GitHub Wiki Docs**: https://docs.github.com/en/communities/documenting-your-project-with-wikis
- **Markdown Guide**: https://guides.github.com/features/mastering-markdown/
- **DisComfy Repo**: https://github.com/jmpijll/discomfy

---

**📚 Great documentation makes great projects! Enjoy your comprehensive wiki!**

