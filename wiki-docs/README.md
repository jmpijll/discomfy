# DisComfy Wiki Documentation

This directory contains comprehensive wiki documentation for DisComfy.

## 📚 Wiki Pages

1. **Home.md** - Wiki homepage with navigation
2. **Installation-Guide.md** - Complete installation instructions
3. **Configuration-Guide.md** - Detailed configuration reference
4. **User-Guide.md** - Complete user documentation
5. **Developer-Guide.md** - Developer and contributor guide
6. **Custom-Workflows.md** - Custom workflow creation guide
7. **Troubleshooting.md** - Common issues and solutions

## 🚀 Publishing to GitHub Wiki

### Step 1: Initialize Wiki on GitHub

1. Go to https://github.com/jmpijll/discomfy/wiki
2. Click **"Create the first page"**
3. Title: `Home`
4. Content: Copy from `Home.md`
5. Click **"Save Page"**

### Step 2: Clone Wiki Repository

```bash
# From discomfy directory
cd ..
git clone https://github.com/jmpijll/discomfy.wiki.git
cd discomfy.wiki
```

### Step 3: Copy Wiki Files

```bash
# Copy all wiki pages
cp ../discomfy/wiki-docs/*.md .

# Check files
ls -la
```

### Step 4: Push to GitHub

```bash
# Add all files
git add *.md

# Commit
git commit -m "Add comprehensive wiki documentation

- Installation guide
- Configuration guide
- User guide
- Developer guide
- Custom workflows guide
- Troubleshooting guide
"

# Push to GitHub
git push origin master
```

### Step 5: Verify

Visit https://github.com/jmpijll/discomfy/wiki to see your published wiki!

## 🔄 Updating Wiki

To update wiki content:

```bash
# Edit files in wiki-docs/
cd discomfy/wiki-docs
# Make changes...

# Copy to wiki repo
cd ../../discomfy.wiki
cp ../discomfy/wiki-docs/*.md .

# Commit and push
git add *.md
git commit -m "Update wiki documentation"
git push origin master
```

## ✨ Features

### Navigation
Wiki pages use `[[Page-Name]]` syntax for internal links.

Example:
```markdown
See the [[Installation-Guide]] for setup instructions.
```

### Structure
- Clear hierarchy
- Comprehensive examples
- Step-by-step instructions
- Code snippets
- Troubleshooting sections

### Best Practices
- Keep pages focused on single topics
- Use consistent formatting
- Include practical examples
- Link related pages
- Update as features change

## 📖 Page Descriptions

### Home
- Welcome page
- Navigation hub
- Feature overview
- Quick links

### Installation Guide
- Prerequisites
- Step-by-step setup
- Platform-specific instructions
- Verification steps
- Troubleshooting installation

### Configuration Guide
- Complete config reference
- All parameters explained
- Examples for different setups
- Security best practices
- Performance tuning

### User Guide
- All commands explained
- Interactive features
- Creative workflows
- Pro tips
- Examples and use cases

### Developer Guide
- Architecture overview
- Code style guidelines
- Adding features
- API reference
- Testing and debugging

### Custom Workflows
- Workflow requirements
- Creating workflows
- Integration steps
- Common patterns
- Debugging workflows

### Troubleshooting
- Common issues
- Solutions and fixes
- Diagnostic commands
- Recovery procedures
- Getting help

## 🎯 Maintenance

### Regular Updates
- Update when features added
- Fix errors promptly
- Add FAQ entries
- Expand examples
- Improve clarity

### Quality Checks
- Test all code examples
- Verify links work
- Check for outdated info
- Ensure consistency
- Validate formatting

## 📝 Contributing

To contribute to wiki:

1. Edit files in `wiki-docs/`
2. Test locally (Markdown preview)
3. Submit PR with changes
4. After merge, update wiki repo

## 🔗 Resources

- **GitHub Wiki Docs**: https://docs.github.com/en/communities/documenting-your-project-with-wikis
- **Markdown Guide**: https://guides.github.com/features/mastering-markdown/
- **DisComfy Repo**: https://github.com/jmpijll/discomfy

---

**📚 Comprehensive documentation = Happy users!**

