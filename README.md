# 🎨 Discord ComfyUI Bot - AI Art Generation Made Easy!

Welcome to the most powerful Discord bot for AI image and video generation! This bot seamlessly integrates with ComfyUI to bring professional-grade AI art generation directly to your Discord server. Whether you're an artist, content creator, or just love experimenting with AI, this bot makes it incredibly easy to create stunning visuals with just a few commands!

## 🌟 What Makes This Bot Special?

This isn't just another AI bot - it's a complete creative powerhouse that brings the full capabilities of ComfyUI to Discord with an intuitive, user-friendly interface. Generate everything from simple images to complex video animations, all while chatting with your friends!

## ✨ Current Features

### 🖼️ Image Generation
- **Slash Commands**: Easy-to-use `/generate` command with autocomplete
- **Custom Prompts**: Write any prompt and watch your imagination come to life
- **Parameter Control**: Adjust width, height, steps, CFG scale, and more
- **Batch Generation**: Create multiple images at once with automatic collaging
- **Interactive UI**: Post-generation buttons for upscaling, variations, and more
- **Multiple Workflows**: Switch between different ComfyUI workflows on the fly
- **Smart Output Management**: Automatically saves and manages your creations

### 🎬 Video Generation (Coming Soon!)
- **Image-to-Video**: Transform your generated images into stunning animations
- **Custom Video Workflows**: Support for complex video generation pipelines
- **Video Parameters**: Control frame rate, duration, and animation style
- **Progress Tracking**: Real-time updates on video generation progress

### 🔧 Advanced Features
- **Modular Architecture**: Clean, extensible codebase for easy customization
- **Workflow Management**: Easy addition of new ComfyUI workflows
- **Error Handling**: Graceful error recovery with helpful user feedback
- **Rate Limiting**: Fair usage policies to ensure smooth operation
- **File Management**: Automatic cleanup and organization of generated content

## 🗺️ Roadmap - What's Coming Next!

### Phase 2: Enhanced Image Features (In Development)
- [ ] Advanced parameter customization
- [ ] LoRA model selection and management
- [ ] Preset saving and sharing
- [ ] Image upscaling and enhancement tools
- [ ] Style transfer capabilities

### Phase 3: Video Generation (Coming Soon)
- [ ] Full video generation pipeline
- [ ] Image-to-video conversion
- [ ] Video style transfer
- [ ] Animation controls and keyframing
- [ ] Video collaging and editing

### Phase 4: Community Features (Future)
- [ ] User galleries and sharing
- [ ] Collaborative generation sessions
- [ ] Custom workflow sharing
- [ ] Advanced user permissions
- [ ] Generation analytics and insights

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- ComfyUI instance (local or remote)
- Discord Bot Token
- Basic command line knowledge

### Step 1: Clone the Repository
```bash
git clone https://github.com/yourusername/discord-comfyui-bot.git
cd discord-comfyui-bot
```

### Step 2: Set Up Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure the Bot
1. Copy the example configuration:
   ```bash
   cp config.example.json config.json
   ```

2. Edit `config.json` with your settings:
   ```json
   {
     "discord": {
       "token": "YOUR_DISCORD_BOT_TOKEN",
       "guild_id": "YOUR_SERVER_ID"
     },
     "comfyui": {
       "url": "http://localhost:8188",
       "api_key": null
     },
     "generation": {
       "default_workflow": "basic_image_gen",
       "max_batch_size": 4,
       "output_limit": 50
     }
   }
   ```

3. Set up environment variables:
   ```bash
   # Create .env file
   echo "DISCORD_TOKEN=your_bot_token_here" > .env
   echo "COMFYUI_URL=http://localhost:8188" >> .env
   ```

### Step 5: Set Up Discord Bot
1. Go to [Discord Developer Portal](https://discord.com/developers/applications)
2. Create a new application and bot
3. Copy the bot token to your configuration
4. Invite the bot to your server with appropriate permissions:
   - Send Messages
   - Use Slash Commands
   - Attach Files
   - Embed Links

### Step 6: Prepare ComfyUI
1. Ensure ComfyUI is running and accessible
2. Test the API endpoint: `http://your-comfyui-url/system_stats`
3. Place your workflow JSON files in the `workflows/` folder

### Step 7: Run the Bot
```bash
python bot.py
```

You should see:
```
🤖 Bot is starting up...
✅ Connected to Discord as YourBotName#1234
🎨 ComfyUI connection verified
🚀 Bot is ready! Use /generate to start creating!
```

## 📖 How to Use

### Basic Image Generation
```
/generate prompt:a beautiful sunset over mountains
```

### Advanced Generation with Parameters
```
/generate prompt:cyberpunk city at night width:1024 height:768 steps:30 cfg:7.5 batch_size:2
```

### Using Different Workflows
```
/generate prompt:anime character workflow:anime_style_v2
```

### Interactive Features
After generation, use the buttons to:
- 🔍 **Upscale**: Enhance image resolution
- 🎲 **Variations**: Generate similar images
- 🎬 **Animate**: Convert to video (coming soon!)
- 💾 **Save**: Add to your personal gallery

## 🔧 Adding Custom Workflows

1. Export your ComfyUI workflow as API format
2. Save the JSON file to `workflows/` folder
3. Add workflow configuration to `config.json`:
   ```json
   "workflows": {
     "my_custom_workflow": {
       "file": "my_workflow.json",
       "name": "My Custom Style",
       "description": "Custom workflow for special effects",
       "parameters": {
         "prompt_node": "16",
         "width_node": "53",
         "height_node": "53"
       }
     }
   }
   ```
4. Restart the bot - your workflow is now available!

## 🛠️ Troubleshooting

### Bot Won't Start
**Problem**: Bot fails to connect to Discord
**Solution**: 
- Verify your bot token in `config.json` or `.env`
- Check that the bot has proper permissions
- Ensure your internet connection is stable

### ComfyUI Connection Issues
**Problem**: "ComfyUI not accessible" error
**Solution**:
- Verify ComfyUI is running: visit `http://your-comfyui-url` in browser
- Check the URL in your configuration
- Ensure no firewall is blocking the connection
- For remote ComfyUI, verify API key if required

### Generation Fails
**Problem**: Images fail to generate
**Solution**:
- Check ComfyUI logs for errors
- Verify workflow JSON is valid
- Ensure all required models are installed in ComfyUI
- Check available VRAM/memory
- Try with simpler parameters first

### Discord Upload Fails
**Problem**: Generated images won't upload to Discord
**Solution**:
- Check file size (Discord limit: 8MB default, 25MB Nitro)
- Verify bot has "Attach Files" permission
- Check output folder permissions
- Try generating smaller images

### Slash Commands Not Appearing
**Problem**: `/generate` command doesn't show up
**Solution**:
- Wait up to 1 hour for Discord to sync commands
- Restart the bot
- Check bot permissions in server settings
- Verify guild_id in configuration

### Performance Issues
**Problem**: Bot is slow or unresponsive
**Solution**:
- Check ComfyUI performance and queue
- Reduce batch sizes
- Monitor system resources
- Consider upgrading hardware
- Implement rate limiting

### Memory Issues
**Problem**: Bot crashes with memory errors
**Solution**:
- Reduce image resolution
- Lower batch sizes
- Check output folder cleanup is working
- Monitor system memory usage
- Restart bot periodically

## 📁 Project Structure
```
discord-comfyui-bot/
├── bot.py                 # Main Discord bot logic
├── image_gen.py          # Image generation handler
├── video_gen.py          # Video generation handler (coming soon)
├── config.py             # Configuration management
├── requirements.txt      # Python dependencies
├── config.json          # Bot configuration
├── .env                 # Environment variables
├── workflows/           # ComfyUI workflow JSON files
│   ├── basic_image_gen.json
│   └── hidream_full_config-1.json
├── outputs/             # Generated images and videos
├── logs/               # Bot logs
└── docs/               # Additional documentation
```

## 🤝 Contributing

We love contributions! Whether it's bug fixes, new features, or workflow additions, your help makes this bot better for everyone.

1. Fork the repository
2. Create a feature branch
3. Follow the guidelines in `GUIDELINES.md`
4. Test your changes thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

Need help? Here's how to get support:

1. **Check this README** - Most common issues are covered here
2. **Review the Guidelines** - Check `GUIDELINES.md` for development questions
3. **Search Issues** - Someone might have had the same problem
4. **Create an Issue** - Describe your problem with details
5. **Join our Discord** - Get help from the community

## 🙏 Acknowledgments

- ComfyUI team for the amazing AI generation framework
- Discord.py developers for the excellent Discord library
- The AI art community for inspiration and feedback
- All contributors who help make this project better

---

**Ready to start creating amazing AI art? Install the bot and let your creativity flow! 🎨✨** 