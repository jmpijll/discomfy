# 🎨 Discord ComfyUI Bot - AI Art Generation Made Easy!

Welcome to the most powerful Discord bot for AI image and video generation! This bot seamlessly integrates with ComfyUI to bring professional-grade AI art generation directly to your Discord server. Whether you're an artist, content creator, or just love experimenting with AI, this bot makes it incredibly easy to create stunning visuals with just a few commands!

**🎉 Repository**: [https://github.com/jmpijll/discomfy.git](https://github.com/jmpijll/discomfy.git)

## 🌟 What Makes This Bot Special?

This isn't just another AI bot - it's a complete creative powerhouse that brings the full capabilities of ComfyUI to Discord with an intuitive, user-friendly interface. Generate everything from simple images to complex video animations, all while chatting with your friends!

## 🔧 Development Status

- ✅ **Phase 1**: Foundation & Basic Image Generation (Complete)
- ✅ **Phase 2**: Post-Generation Actions & UI (Complete)
- ✅ **Phase 3**: Video Generation & Advanced Features (Complete)
- ✅ **Phase 4**: Polish & Production Ready (Complete)

**🎉 Version 1.0.0 - Production Ready!**

This bot is now feature-complete and ready for production deployment. All core functionality has been implemented, tested, and optimized for real-world use.

## ✨ Features

### ✅ Current Features (Phase 1, 2 & 3 Complete)
- **🎨 AI Image Generation**: Generate high-quality images using ComfyUI workflows
- **⚡ Slash Commands**: Simple `/generate` command with customizable parameters
- **🔍 Functional Upscaling**: 2x image upscaling with ComfyUI upscale workflow
- **🎬 Video Generation**: Convert images to 720x720 MP4 animations (81 frames)
- **👥 Community Friendly**: Anyone can use action buttons on any generation
- **⏰ Infinite Usage**: Buttons never expire and can be used multiple times
- **🛡️ Rate Limiting**: Smart rate limiting to prevent abuse (5 requests/minute per user)
- **📊 Real-time Progress**: Live progress updates with node execution tracking and 1-second intervals
- **🔧 Configurable Parameters**: Width, height, steps, CFG, batch size, seed control
- **📁 Auto-cleanup**: Automatic management of output files (100 file limit)
- **🔄 Queue Management**: Improved concurrent request handling
- **⚡ Enhanced Error Handling**: Better Discord interaction timeout protection
- **🚫 Null Safety**: Robust API response validation to prevent crashes

## 🚀 Enhanced Progress Tracking

The bot now features **real-time progress tracking** that provides detailed information about your generation progress:

### 📊 What You'll See:
- **Accurate Progress Percentage**: Based on actual node execution progress, not just elapsed time
- **Current Phase**: Descriptive status like "Processing prompt", "Generating image", "Sampling (15/20)"
- **Real-time Updates**: Progress updates every second for smooth, responsive feedback
- **Node Execution**: Track which nodes are running and how many are complete
- **Step Progress**: See individual sampling steps (e.g., "Step 15/20" for KSampler)
- **Time Estimation**: Improved ETA calculations based on actual progress
- **Queue Position**: Live updates when waiting in ComfyUI's generation queue

### 🔧 Technical Features:
- **WebSocket Integration**: Uses ComfyUI's WebSocket API for real-time node execution tracking
- **Cached Node Detection**: Automatically accounts for nodes that are skipped due to caching
- **Fallback Support**: Automatically falls back to HTTP polling if WebSocket fails
- **Rate Limit Friendly**: 1-second update intervals that don't overwhelm Discord or ComfyUI APIs

### 📈 Progress Display Format:
```
🎨 Generating
📊 67.3% ████████████░░░░░░░░
🔄 Sampling (15/20)
⏱️ Elapsed: 1m 23s | ETA: 32s
🎯 Step: 15/20
🔗 Nodes: 8/12
```

This enhanced tracking works for both **image generation** and **video generation**, giving you complete visibility into your AI creation process!

## 🚀 Installation & Setup

### Prerequisites
- Python 3.8 or higher
- ComfyUI instance (local or remote)
- Discord Bot Token
- Basic command line knowledge

### Step 1: Clone the Repository
```bash
git clone https://github.com/jmpijll/discomfy.git
cd discomfy
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
- 🔍 **Upscale**: Enhance image resolution with 2x AI super-resolution
- 🎬 **Animate**: Convert image to video (720x720 MP4, 81 frames)
- 💫 **Universal Access**: Anyone can use buttons on any generation

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

**Buttons not working**
- Check the logs in `logs/bot.log` for any errors
- Verify ComfyUI server is running and accessible
- Ensure upscale and video workflows are properly configured
- Check that required models are loaded in ComfyUI

**Video generation errors ("WorkflowConfig object has no attribute 'type'")**
- This issue has been fixed in the latest version
- Ensure your `config.json` includes `type` field for all workflows
- Restart the bot after updating configuration

**Queue conflicts (multiple requests failing)**
- The bot now includes improved queue management
- Multiple users can safely use buttons simultaneously
- Rate limiting prevents system overload
- If issues persist, check ComfyUI system resources

**Discord interaction timeouts ("Unknown interaction" errors)**
- These errors have been reduced with better timeout handling
- If you see this error, try the command again
- The bot now gracefully handles expired interactions

## 📁 Project Structure
```
discomfy/
├── bot.py                 # Main Discord bot logic
├── image_gen.py          # Image generation handler
├── video_gen.py          # Video generation handler
├── config.py             # Configuration management
├── setup.py              # Automated setup script
├── requirements.txt      # Python dependencies
├── config.json          # Bot configuration (create from example)
├── config.example.json   # Example configuration
├── .env                 # Environment variables (create from example)
├── env.example          # Example environment file
├── workflows/           # ComfyUI workflow JSON files
│   ├── flux_lora.json
│   ├── hidream_lora.json
│   ├── upscale_config-1.json
│   └── video_wan_vace_14B_i2v.json
├── outputs/             # Generated images and videos
├── logs/               # Bot logs
├── LICENSE             # MIT License
├── CHANGELOG.md        # Version history
├── README.md          # This file
├── GUIDELINES.md      # Development guidelines
└── PROJECT_PLAN.md    # Project roadmap
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