#!/usr/bin/env python3
"""
ComfyUI Workflow Defaults Test Script
Tests image generation using the actual workflow default settings,
only changing the prompt as requested.
"""

import asyncio
import logging
import sys
import time
from pathlib import Path
from typing import List, Dict, Any

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ComfyUI server configuration
COMFYUI_URL = "http://172.27.1.134:8188"

# Test prompts - only changing the prompt, using workflow defaults for everything else
TEST_PROMPTS = [
    {
        "name": "Simple Portrait",
        "prompt": "a beautiful woman with long flowing hair, portrait, photorealistic, high quality"
    },
    {
        "name": "Landscape Scene", 
        "prompt": "a serene mountain landscape at sunset, golden hour lighting, peaceful lake reflection"
    },
    {
        "name": "Fantasy Art",
        "prompt": "a majestic dragon flying over a medieval castle, fantasy art, detailed, epic"
    },
    {
        "name": "Cute Animals",
        "prompt": "cute cartoon cat, different poses, colorful, kawaii style"
    },
    {
        "name": "Cyberpunk City",
        "prompt": "cyberpunk city at night, neon lights, futuristic, detailed architecture"
    }
]

async def get_workflow_defaults():
    """Extract default settings from the workflow."""
    logger.info("🔍 Reading workflow defaults...")
    
    try:
        import json
        from pathlib import Path
        
        workflow_path = Path("workflows/hidream_full_config-1.json")
        if not workflow_path.exists():
            logger.error("❌ Workflow file not found!")
            return None
        
        with open(workflow_path, 'r') as f:
            workflow = json.load(f)
        
        # Extract defaults from the workflow
        defaults = {}
        
        # KSampler settings (node 3)
        if "3" in workflow:
            ksampler = workflow["3"]["inputs"]
            defaults.update({
                "steps": ksampler.get("steps", 50),
                "cfg": ksampler.get("cfg", 5),
                "sampler_name": ksampler.get("sampler_name", "uni_pc"),
                "scheduler": ksampler.get("scheduler", "simple"),
                "denoise": ksampler.get("denoise", 1.0)
            })
        
        # Image dimensions (node 53)
        if "53" in workflow:
            latent = workflow["53"]["inputs"]
            defaults.update({
                "width": latent.get("width", 1024),
                "height": latent.get("height", 1024),
                "batch_size": latent.get("batch_size", 1)
            })
        
        # Negative prompt (node 40)
        if "40" in workflow:
            negative = workflow["40"]["inputs"]
            defaults["negative_prompt"] = negative.get("text", "bad ugly jpeg artifacts")
        
        logger.info("✅ Workflow defaults extracted:")
        for key, value in defaults.items():
            logger.info(f"   {key}: {value}")
        
        return defaults
        
    except Exception as e:
        logger.error(f"❌ Failed to read workflow defaults: {e}")
        return None

async def test_with_workflow_defaults(test_case: Dict[str, Any], defaults: Dict[str, Any]) -> bool:
    """Test image generation using workflow defaults, only changing the prompt."""
    logger.info(f"🎨 Testing: {test_case['name']}")
    logger.info(f"   Prompt: {test_case['prompt'][:60]}...")
    logger.info(f"   Using workflow defaults:")
    logger.info(f"     Size: {defaults['width']}x{defaults['height']}")
    logger.info(f"     Steps: {defaults['steps']}, CFG: {defaults['cfg']}")
    logger.info(f"     Sampler: {defaults['sampler_name']}, Scheduler: {defaults['scheduler']}")
    logger.info(f"     Batch: {defaults['batch_size']}")
    
    try:
        from image_gen import ImageGenerator, save_output_image, get_unique_filename
        
        # Progress tracking
        async def progress_callback(status: str, queue_position: int = 0):
            progress_msg = f"Status: {status}"
            if queue_position > 0:
                progress_msg += f" (Queue position: {queue_position})"
            logger.info(f"   📊 {progress_msg}")
        
        start_time = time.time()
        
        async with ImageGenerator() as gen:
            # Override the URL for testing
            gen.base_url = COMFYUI_URL.rstrip('/')
            gen.config.comfyui.url = COMFYUI_URL
            
            # Use workflow defaults - only change the prompt
            image_data, generation_info = await gen.generate_image(
                prompt=test_case['prompt'],
                negative_prompt=defaults['negative_prompt'],
                width=defaults['width'],
                height=defaults['height'],
                steps=defaults['steps'],
                cfg=defaults['cfg'],
                batch_size=defaults['batch_size'],
                progress_callback=progress_callback
            )
        
        generation_time = time.time() - start_time
        
        # Save the generated image
        filename = get_unique_filename(f"workflow_test_{test_case['name'].lower().replace(' ', '_')}")
        output_path = save_output_image(image_data, filename)
        
        # Analyze the result
        image_size = len(image_data)
        logger.info(f"✅ Generation successful!")
        logger.info(f"   📁 Saved to: {output_path}")
        logger.info(f"   📊 Image size: {image_size:,} bytes")
        logger.info(f"   ⏱️  Generation time: {generation_time:.1f} seconds")
        logger.info(f"   🎯 Seed used: {generation_info.get('seed', 'Unknown')}")
        logger.info(f"   📸 Images generated: {generation_info.get('num_images', 1)}")
        
        # Basic validation
        if image_size < 1000:
            logger.warning("⚠️  Generated image seems very small, might be an issue")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Image generation failed: {e}")
        import traceback
        logger.error(f"   Error details: {traceback.format_exc()}")
        return False

async def analyze_workflow_images():
    """Analyze the generated images from workflow defaults test."""
    logger.info("🔍 Analyzing workflow default test images...")
    
    try:
        from PIL import Image
        import os
        
        output_dir = Path("outputs")
        if not output_dir.exists():
            logger.warning("⚠️  No outputs directory found")
            return
        
        # Find workflow test images (created in the last hour)
        current_time = time.time()
        recent_images = []
        
        for img_file in output_dir.glob("workflow_test_*.png"):
            if current_time - img_file.stat().st_mtime < 3600:  # Last hour
                recent_images.append(img_file)
        
        if not recent_images:
            logger.warning("⚠️  No recent workflow test images found")
            return
        
        logger.info(f"📊 Analyzing {len(recent_images)} workflow test images:")
        
        for img_path in recent_images:
            try:
                with Image.open(img_path) as img:
                    width, height = img.size
                    mode = img.mode
                    file_size = img_path.stat().st_size
                    
                    logger.info(f"   📸 {img_path.name}:")
                    logger.info(f"      Size: {width}x{height} pixels")
                    logger.info(f"      Mode: {mode}")
                    logger.info(f"      File size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
                    
                    # Validate against workflow defaults (should be 1024x1024)
                    if width == 1024 and height == 1024:
                        logger.info(f"      ✅ Correct workflow dimensions")
                    else:
                        logger.warning(f"      ⚠️  Unexpected dimensions (expected 1024x1024)")
                    
                    if mode in ['RGB', 'RGBA']:
                        logger.info(f"      ✅ Good color mode")
                    else:
                        logger.warning(f"      ⚠️  Unusual color mode: {mode}")
                        
            except Exception as e:
                logger.error(f"   ❌ Failed to analyze {img_path.name}: {e}")
        
    except Exception as e:
        logger.error(f"❌ Image analysis failed: {e}")

async def main():
    """Run workflow defaults test."""
    logger.info("🧪 Starting ComfyUI Workflow Defaults Test")
    logger.info("=" * 60)
    logger.info(f"🎯 Target ComfyUI Server: {COMFYUI_URL}")
    logger.info("📋 Testing with actual workflow defaults, only changing prompts")
    logger.info("=" * 60)
    
    # Test results tracking
    test_results = []
    
    # 1. Get workflow defaults
    logger.info("\n📋 Phase 1: Reading Workflow Defaults")
    defaults = await get_workflow_defaults()
    
    if not defaults:
        logger.error("❌ Cannot proceed without workflow defaults!")
        return False
    
    # 2. Test connection
    logger.info("\n📡 Phase 2: Connection Test")
    try:
        from image_gen import ImageGenerator
        
        async with ImageGenerator() as gen:
            gen.base_url = COMFYUI_URL.rstrip('/')
            gen.config.comfyui.url = COMFYUI_URL
            
            success = await gen.test_connection()
            if success:
                logger.info("✅ ComfyUI connection successful!")
                test_results.append(("Connection", True))
            else:
                logger.error("❌ ComfyUI connection failed!")
                test_results.append(("Connection", False))
                return False
                
    except Exception as e:
        logger.error(f"❌ Connection test failed: {e}")
        test_results.append(("Connection", False))
        return False
    
    # 3. Test image generation with workflow defaults
    logger.info("\n🎨 Phase 3: Image Generation with Workflow Defaults")
    
    for i, test_case in enumerate(TEST_PROMPTS, 1):
        logger.info(f"\n--- Test {i}/{len(TEST_PROMPTS)} ---")
        result = await test_with_workflow_defaults(test_case, defaults)
        test_results.append((f"Generation: {test_case['name']}", result))
        
        # Small delay between tests
        if i < len(TEST_PROMPTS):
            logger.info("   ⏳ Waiting 3 seconds before next test...")
            await asyncio.sleep(3)
    
    # 4. Analyze generated images
    logger.info("\n📊 Phase 4: Image Analysis")
    await analyze_workflow_images()
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📋 WORKFLOW DEFAULTS TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
    
    logger.info(f"\n📊 Overall Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 ALL WORKFLOW DEFAULTS TESTS PASSED!")
        logger.info("\n📁 Check the 'outputs/' directory for generated images")
        logger.info("🔧 Images generated using actual workflow defaults:")
        logger.info(f"   - Steps: {defaults['steps']}")
        logger.info(f"   - CFG: {defaults['cfg']}")
        logger.info(f"   - Size: {defaults['width']}x{defaults['height']}")
        logger.info(f"   - Sampler: {defaults['sampler_name']}")
        logger.info(f"   - Scheduler: {defaults['scheduler']}")
        logger.info("🚀 Ready to proceed with Discord integration!")
        return True
    else:
        logger.error("❌ Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("\n⏹️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"💥 Test suite crashed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1) 