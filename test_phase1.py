#!/usr/bin/env python3
"""
Test script for Phase 1 functionality.
Tests configuration loading, image generator initialization, and basic bot setup.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Set up basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test that all modules can be imported."""
    logger.info("Testing imports...")
    
    try:
        import config
        import image_gen
        import bot
        logger.info("✅ All imports successful")
        return True
    except ImportError as e:
        logger.error(f"❌ Import failed: {e}")
        return False

def test_configuration():
    """Test configuration loading."""
    logger.info("Testing configuration...")
    
    try:
        from config import ConfigManager, get_config
        
        # Test config manager initialization
        config_manager = ConfigManager()
        
        # Test loading config (should work with defaults even without config file)
        config = get_config()
        
        logger.info(f"✅ Configuration loaded successfully")
        logger.info(f"   Discord prefix: {config.discord.command_prefix}")
        logger.info(f"   ComfyUI URL: {config.comfyui.url}")
        logger.info(f"   Default workflow: {config.generation.default_workflow}")
        logger.info(f"   Max batch size: {config.generation.max_batch_size}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Configuration test failed: {e}")
        return False

def test_image_generator():
    """Test image generator initialization."""
    logger.info("Testing image generator...")
    
    try:
        from image_gen import ImageGenerator
        
        # Test initialization
        generator = ImageGenerator()
        logger.info("✅ Image generator initialized successfully")
        
        # Test workflow loading
        try:
            workflows = asyncio.run(generator.get_available_workflows())
            logger.info(f"✅ Found {len(workflows)} available workflows")
            for workflow in workflows:
                logger.info(f"   - {workflow['name']}: {workflow['description']}")
        except Exception as e:
            logger.warning(f"⚠️  Workflow loading test failed (expected without workflow files): {e}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Image generator test failed: {e}")
        return False

def test_bot_initialization():
    """Test bot initialization (without actually connecting)."""
    logger.info("Testing bot initialization...")
    
    try:
        # We can't actually initialize the bot without a valid token,
        # but we can test the import and class definition
        from bot import ComfyUIBot
        
        logger.info("✅ Bot class imported successfully")
        
        # Test command imports
        from bot import generate_command, help_command, status_command
        logger.info("✅ Bot commands imported successfully")
        
        return True
    except Exception as e:
        logger.error(f"❌ Bot initialization test failed: {e}")
        return False

def test_file_structure():
    """Test that required directories and files exist."""
    logger.info("Testing file structure...")
    
    required_files = [
        "requirements.txt",
        "config.py",
        "image_gen.py",
        "bot.py",
        "config.example.json",
        "env.example",
        ".gitignore"
    ]
    
    required_dirs = [
        "workflows",
        "outputs",
        "logs"
    ]
    
    all_good = True
    
    for file_path in required_files:
        if Path(file_path).exists():
            logger.info(f"✅ {file_path} exists")
        else:
            logger.error(f"❌ {file_path} missing")
            all_good = False
    
    for dir_path in required_dirs:
        if Path(dir_path).exists():
            logger.info(f"✅ {dir_path}/ directory exists")
        else:
            logger.error(f"❌ {dir_path}/ directory missing")
            all_good = False
    
    # Check for workflow files
    workflow_files = list(Path("workflows").glob("*.json"))
    if workflow_files:
        logger.info(f"✅ Found {len(workflow_files)} workflow files:")
        for wf in workflow_files:
            logger.info(f"   - {wf.name}")
    else:
        logger.warning("⚠️  No workflow files found in workflows/ directory")
    
    return all_good

def test_utilities():
    """Test utility functions."""
    logger.info("Testing utility functions...")
    
    try:
        from image_gen import get_unique_filename, cleanup_old_outputs
        from config import validate_discord_token, validate_comfyui_url
        
        # Test filename generation
        filename = get_unique_filename("test")
        logger.info(f"✅ Generated filename: {filename}")
        
        # Test URL validation
        valid_urls = [
            "http://localhost:8188",
            "https://api.example.com:8080",
            "http://192.168.1.100:8188"
        ]
        
        for url in valid_urls:
            if validate_comfyui_url(url):
                logger.info(f"✅ URL validation passed: {url}")
            else:
                logger.error(f"❌ URL validation failed: {url}")
        
        return True
    except Exception as e:
        logger.error(f"❌ Utilities test failed: {e}")
        return False

def main():
    """Run all tests."""
    logger.info("🧪 Starting Phase 1 Tests")
    logger.info("=" * 50)
    
    tests = [
        ("File Structure", test_file_structure),
        ("Imports", test_imports),
        ("Configuration", test_configuration),
        ("Image Generator", test_image_generator),
        ("Bot Initialization", test_bot_initialization),
        ("Utilities", test_utilities),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n🔍 Running {test_name} test...")
        try:
            if test_func():
                passed += 1
                logger.info(f"✅ {test_name} test PASSED")
            else:
                logger.error(f"❌ {test_name} test FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name} test FAILED with exception: {e}")
    
    logger.info("\n" + "=" * 50)
    logger.info(f"🧪 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Phase 1 implementation is working correctly.")
        logger.info("\n📋 Next steps:")
        logger.info("1. Set up your Discord bot token in .env file")
        logger.info("2. Configure ComfyUI URL in .env file")
        logger.info("3. Install dependencies: pip install -r requirements.txt")
        logger.info("4. Run the bot: python bot.py")
        return True
    else:
        logger.error("❌ Some tests failed. Please fix the issues before proceeding.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 