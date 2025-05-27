#!/usr/bin/env python3
"""
Setup script for Discord ComfyUI Bot.
Helps users install dependencies and configure the bot.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def print_header(text):
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"🤖 {text}")
    print("=" * 60)

def print_step(step_num, total_steps, description):
    """Print a formatted step."""
    print(f"\n📋 Step {step_num}/{total_steps}: {description}")

def run_command(command, description=""):
    """Run a command and handle errors."""
    try:
        print(f"   Running: {command}")
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Error: {e}")
        if e.stderr:
            print(f"   Error details: {e.stderr.strip()}")
        return False

def check_python_version():
    """Check if Python version is compatible."""
    print_step(1, 6, "Checking Python version")
    
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro} is compatible")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} is not compatible")
        print("   This bot requires Python 3.8 or higher")
        return False

def create_virtual_environment():
    """Create a virtual environment."""
    print_step(2, 6, "Creating virtual environment")
    
    venv_path = Path("venv")
    if venv_path.exists():
        print("   ⚠️  Virtual environment already exists")
        response = input("   Do you want to recreate it? (y/N): ").lower()
        if response == 'y':
            print("   Removing existing virtual environment...")
            shutil.rmtree(venv_path)
        else:
            print("   Using existing virtual environment")
            return True
    
    if run_command("python -m venv venv"):
        print("   ✅ Virtual environment created successfully")
        return True
    else:
        print("   ❌ Failed to create virtual environment")
        return False

def install_dependencies():
    """Install required dependencies."""
    print_step(3, 6, "Installing dependencies")
    
    # Determine the correct pip command based on OS
    if sys.platform == "win32":
        pip_cmd = "venv\\Scripts\\pip"
    else:
        pip_cmd = "venv/bin/pip"
    
    commands = [
        f"{pip_cmd} install --upgrade pip",
        f"{pip_cmd} install -r requirements.txt"
    ]
    
    for cmd in commands:
        if not run_command(cmd):
            print("   ❌ Failed to install dependencies")
            return False
    
    print("   ✅ Dependencies installed successfully")
    return True

def setup_configuration():
    """Set up configuration files."""
    print_step(4, 6, "Setting up configuration")
    
    # Copy example files if they don't exist
    config_files = [
        ("config.example.json", "config.json"),
        ("env.example", ".env")
    ]
    
    for example_file, target_file in config_files:
        if not Path(target_file).exists():
            if Path(example_file).exists():
                shutil.copy2(example_file, target_file)
                print(f"   ✅ Created {target_file} from {example_file}")
            else:
                print(f"   ❌ Example file {example_file} not found")
                return False
        else:
            print(f"   ⚠️  {target_file} already exists, skipping")
    
    print("\n   📝 Configuration files created. You need to edit them:")
    print("   1. Edit .env file and add your Discord bot token")
    print("   2. Edit .env file and set your ComfyUI URL")
    print("   3. Optionally edit config.json for advanced settings")
    
    return True

def test_installation():
    """Test the installation."""
    print_step(5, 6, "Testing installation")
    
    # Determine the correct python command based on OS
    if sys.platform == "win32":
        python_cmd = "venv\\Scripts\\python"
    else:
        python_cmd = "venv/bin/python"
    
    if run_command(f"{python_cmd} test_phase1.py"):
        print("   ✅ Installation test passed")
        return True
    else:
        print("   ❌ Installation test failed")
        return False

def show_next_steps():
    """Show next steps to the user."""
    print_step(6, 6, "Next steps")
    
    print("\n   🎉 Setup completed! Here's what to do next:")
    print("\n   1. 🔑 Get a Discord Bot Token:")
    print("      - Go to https://discord.com/developers/applications")
    print("      - Create a new application")
    print("      - Go to 'Bot' section and create a bot")
    print("      - Copy the bot token")
    print("      - Add it to your .env file: DISCORD_TOKEN=your_token_here")
    
    print("\n   2. 🎨 Set up ComfyUI:")
    print("      - Make sure ComfyUI is running (default: http://localhost:8188)")
    print("      - Update COMFYUI_URL in .env if using a different URL")
    
    print("\n   3. 🚀 Run the bot:")
    if sys.platform == "win32":
        print("      - Windows: venv\\Scripts\\python bot.py")
    else:
        print("      - macOS/Linux: venv/bin/python bot.py")
    
    print("\n   4. 📱 Invite bot to Discord:")
    print("      - Go to OAuth2 > URL Generator in Discord Developer Portal")
    print("      - Select 'bot' and 'applications.commands' scopes")
    print("      - Select necessary permissions")
    print("      - Use the generated URL to invite your bot")
    
    print("\n   📚 For more help, check the README.md file!")

def main():
    """Main setup function."""
    print_header("Discord ComfyUI Bot Setup")
    print("This script will help you set up the Discord ComfyUI Bot")
    
    # Check if we're in the right directory
    if not Path("requirements.txt").exists():
        print("❌ Error: requirements.txt not found")
        print("Please run this script from the bot's root directory")
        sys.exit(1)
    
    steps = [
        check_python_version,
        create_virtual_environment,
        install_dependencies,
        setup_configuration,
        test_installation,
        show_next_steps
    ]
    
    for step_func in steps:
        if not step_func():
            print(f"\n❌ Setup failed at step: {step_func.__name__}")
            print("Please fix the error and run the setup again")
            sys.exit(1)
    
    print_header("Setup Complete!")
    print("🎉 Your Discord ComfyUI Bot is ready to use!")
    print("Don't forget to configure your Discord token and ComfyUI URL!")

if __name__ == "__main__":
    main() 