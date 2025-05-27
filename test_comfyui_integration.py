#!/usr/bin/env python3
"""
ComfyUI Integration Test Script
Tests the image generation functionality against a real ComfyUI instance.
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

# Test configuration
COMFYUI_URL = "http://your-comfyui-server:8188"
TEST_PROMPTS = [
    {
        "name": "Simple Portrait",
        "prompt": "a beautiful woman with long flowing hair, portrait, photorealistic, high quality",
        "negative_prompt": "blurry, low quality, distorted",
        "width": 512,
        "height": 512,
        "steps": 20,
        "cfg": 7.0,
        "batch_size": 1
    },
    {
        "name": "Landscape Scene",
        "prompt": "a serene mountain landscape at sunset, golden hour lighting, peaceful lake reflection",
        "negative_prompt": "people, buildings, cars, modern objects",
        "width": 768,
        "height": 512,
        "steps": 25,
        "cfg": 6.0,
        "batch_size": 1
    },
    {
        "name": "Fantasy Art",
        "prompt": "a majestic dragon flying over a medieval castle, fantasy art, detailed, epic",
        "negative_prompt": "modern, realistic, photography",
        "width": 512,
        "height": 768,
        "steps": 30,
        "cfg": 8.0,
        "batch_size": 1
    },
    {
        "name": "Multiple Images",
        "prompt": "cute cartoon cat, different poses, colorful, kawaii style",
        "negative_prompt": "realistic, dark, scary",
        "width": 512,
        "height": 512,
        "steps": 20,
        "cfg": 7.0,
        "batch_size": 2
    },
    {
        "name": "High Resolution",
        "prompt": "cyberpunk city at night, neon lights, futuristic, detailed architecture",
        "negative_prompt": "blurry, low quality, daytime",
        "width": 1024,
        "height": 1024,
        "steps": 35,
        "cfg": 7.5,
        "batch_size": 1
    }
]

async def test_connection():
    """Test basic connection to ComfyUI server."""
    logger.info("🔍 Testing ComfyUI connection...")
    
    try:
        from image_gen import ImageGenerator
        
        async with ImageGenerator() as gen:
            # Override the URL for testing
            gen.base_url = COMFYUI_URL.rstrip('/')
            gen.config.comfyui.url = COMFYUI_URL
            
            success = await gen.test_connection()
            if success:
                logger.info("✅ ComfyUI connection successful!")
                return True
            else:
                logger.error("❌ ComfyUI connection failed!")
                return False
                
    except Exception as e:
        logger.error(f"❌ Connection test failed with exception: {e}")
        return False

async def test_workflow_loading():
    """Test workflow loading functionality."""
    logger.info("🔍 Testing workflow loading...")
    
    try:
        from image_gen import ImageGenerator
        
        generator = ImageGenerator()
        # Override the URL for testing
        generator.base_url = COMFYUI_URL.rstrip('/')
        generator.config.comfyui.url = COMFYUI_URL
        
        workflows = await generator.get_available_workflows()
        
        if workflows:
            logger.info(f"✅ Found {len(workflows)} available workflows:")
            for workflow in workflows:
                logger.info(f"   - {workflow['name']}: {workflow['description']}")
            return True
        else:
            logger.warning("⚠️  No workflows found, but this might be expected")
            return True
            
    except Exception as e:
        logger.error(f"❌ Workflow loading test failed: {e}")
        return False

async def test_image_generation(test_case: Dict[str, Any]) -> bool:
    """Test image generation with a specific test case."""
    logger.info(f"🎨 Testing: {test_case['name']}")
    logger.info(f"   Prompt: {test_case['prompt'][:50]}...")
    logger.info(f"   Size: {test_case['width']}x{test_case['height']}")
    logger.info(f"   Steps: {test_case['steps']}, CFG: {test_case['cfg']}")
    logger.info(f"   Batch: {test_case['batch_size']}")
    
    try:
        from image_gen import ImageGenerator, save_output_image, get_unique_filename
        
        # Progress tracking
        progress_updates = []
        async def progress_callback(status: str, queue_position: int = 0):
            progress_msg = f"Status: {status}"
            if queue_position > 0:
                progress_msg += f" (Queue position: {queue_position})"
            progress_updates.append(progress_msg)
            logger.info(f"   📊 {progress_msg}")
        
        start_time = time.time()
        
        async with ImageGenerator() as gen:
            # Override the URL for testing
            gen.base_url = COMFYUI_URL.rstrip('/')
            gen.config.comfyui.url = COMFYUI_URL
            
            image_data, generation_info = await gen.generate_image(
                prompt=test_case['prompt'],
                negative_prompt=test_case['negative_prompt'],
                width=test_case['width'],
                height=test_case['height'],
                steps=test_case['steps'],
                cfg=test_case['cfg'],
                batch_size=test_case['batch_size'],
                progress_callback=progress_callback
            )
        
        generation_time = time.time() - start_time
        
        # Save the generated image
        filename = get_unique_filename(f"test_{test_case['name'].lower().replace(' ', '_')}")
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
        if image_size < 1000:  # Very small file, probably an error
            logger.warning("⚠️  Generated image seems very small, might be an issue")
            return False
        
        if image_size > 50 * 1024 * 1024:  # Very large file, might be an issue
            logger.warning("⚠️  Generated image seems very large, might be an issue")
            return False
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Image generation failed: {e}")
        import traceback
        logger.error(f"   Error details: {traceback.format_exc()}")
        return False

async def analyze_generated_images():
    """Analyze the generated images to see if they look reasonable."""
    logger.info("🔍 Analyzing generated images...")
    
    try:
        from PIL import Image
        import os
        
        output_dir = Path("outputs")
        if not output_dir.exists():
            logger.warning("⚠️  No outputs directory found")
            return
        
        # Find test images (created in the last hour)
        current_time = time.time()
        recent_images = []
        
        for img_file in output_dir.glob("test_*.png"):
            if current_time - img_file.stat().st_mtime < 3600:  # Last hour
                recent_images.append(img_file)
        
        if not recent_images:
            logger.warning("⚠️  No recent test images found")
            return
        
        logger.info(f"📊 Analyzing {len(recent_images)} recent test images:")
        
        for img_path in recent_images:
            try:
                with Image.open(img_path) as img:
                    width, height = img.size
                    mode = img.mode
                    file_size = img_path.stat().st_size
                    
                    logger.info(f"   📸 {img_path.name}:")
                    logger.info(f"      Size: {width}x{height} pixels")
                    logger.info(f"      Mode: {mode}")
                    logger.info(f"      File size: {file_size:,} bytes")
                    
                    # Basic image validation
                    if width < 256 or height < 256:
                        logger.warning(f"      ⚠️  Image seems small for AI generation")
                    elif width > 2048 or height > 2048:
                        logger.warning(f"      ⚠️  Image seems very large")
                    else:
                        logger.info(f"      ✅ Image dimensions look good")
                    
                    if mode not in ['RGB', 'RGBA']:
                        logger.warning(f"      ⚠️  Unusual color mode: {mode}")
                    else:
                        logger.info(f"      ✅ Color mode looks good")
                        
            except Exception as e:
                logger.error(f"   ❌ Failed to analyze {img_path.name}: {e}")
        
    except Exception as e:
        logger.error(f"❌ Image analysis failed: {e}")

async def test_error_scenarios():
    """Test various error scenarios to ensure proper error handling."""
    logger.info("🔍 Testing error scenarios...")
    
    error_tests = [
        {
            "name": "Empty Prompt",
            "prompt": "",
            "should_fail": True
        },
        {
            "name": "Very Long Prompt",
            "prompt": "a" * 2000,  # Very long prompt
            "should_fail": True
        },
        {
            "name": "Invalid Dimensions",
            "prompt": "test image",
            "width": 100,  # Too small
            "height": 100,
            "should_fail": True
        },
        {
            "name": "Invalid Steps",
            "prompt": "test image",
            "steps": 0,  # Invalid
            "should_fail": True
        },
        {
            "name": "Invalid CFG",
            "prompt": "test image",
            "cfg": 50.0,  # Too high
            "should_fail": True
        }
    ]
    
    passed_tests = 0
    
    for test in error_tests:
        try:
            from image_gen import ImageGenerator
            
            logger.info(f"   Testing: {test['name']}")
            
            async with ImageGenerator() as gen:
                # Override the URL for testing
                gen.base_url = COMFYUI_URL.rstrip('/')
                gen.config.comfyui.url = COMFYUI_URL
                
                try:
                    await gen.generate_image(
                        prompt=test['prompt'],
                        width=test.get('width', 512),
                        height=test.get('height', 512),
                        steps=test.get('steps', 20),
                        cfg=test.get('cfg', 7.0)
                    )
                    
                    if test['should_fail']:
                        logger.warning(f"      ⚠️  Expected failure but succeeded")
                    else:
                        logger.info(f"      ✅ Succeeded as expected")
                        passed_tests += 1
                        
                except Exception as e:
                    if test['should_fail']:
                        logger.info(f"      ✅ Failed as expected: {type(e).__name__}")
                        passed_tests += 1
                    else:
                        logger.error(f"      ❌ Unexpected failure: {e}")
                        
        except Exception as e:
            logger.error(f"   ❌ Error test setup failed: {e}")
    
    logger.info(f"📊 Error scenario tests: {passed_tests}/{len(error_tests)} passed")
    return passed_tests == len(error_tests)

async def main():
    """Run all ComfyUI integration tests."""
    logger.info("🧪 Starting ComfyUI Integration Tests")
    logger.info("=" * 60)
    logger.info(f"🎯 Target ComfyUI Server: {COMFYUI_URL}")
    logger.info("=" * 60)
    
    # Test results tracking
    test_results = []
    
    # 1. Test connection
    logger.info("\n📡 Phase 1: Connection Test")
    connection_ok = await test_connection()
    test_results.append(("Connection", connection_ok))
    
    if not connection_ok:
        logger.error("❌ Cannot proceed without ComfyUI connection!")
        return False
    
    # 2. Test workflow loading
    logger.info("\n📋 Phase 2: Workflow Loading Test")
    workflow_ok = await test_workflow_loading()
    test_results.append(("Workflow Loading", workflow_ok))
    
    # 3. Test image generation with various prompts
    logger.info("\n🎨 Phase 3: Image Generation Tests")
    generation_results = []
    
    for i, test_case in enumerate(TEST_PROMPTS, 1):
        logger.info(f"\n--- Test {i}/{len(TEST_PROMPTS)} ---")
        result = await test_image_generation(test_case)
        generation_results.append(result)
        test_results.append((f"Generation: {test_case['name']}", result))
        
        # Small delay between tests to be nice to the server
        if i < len(TEST_PROMPTS):
            logger.info("   ⏳ Waiting 2 seconds before next test...")
            await asyncio.sleep(2)
    
    # 4. Analyze generated images
    logger.info("\n📊 Phase 4: Image Analysis")
    await analyze_generated_images()
    
    # 5. Test error scenarios
    logger.info("\n🚨 Phase 5: Error Handling Tests")
    error_handling_ok = await test_error_scenarios()
    test_results.append(("Error Handling", error_handling_ok))
    
    # Summary
    logger.info("\n" + "=" * 60)
    logger.info("📋 TEST SUMMARY")
    logger.info("=" * 60)
    
    passed = sum(1 for _, result in test_results if result)
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
    
    logger.info(f"\n📊 Overall Results: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 ALL TESTS PASSED! ComfyUI integration is working perfectly!")
        logger.info("\n📁 Check the 'outputs/' directory for generated images")
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