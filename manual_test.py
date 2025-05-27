#!/usr/bin/env python3
"""
Manual ComfyUI Test Script
Interactive script for testing individual prompts against ComfyUI.
Now uses workflow defaults by default.
"""

import asyncio
import sys
import json
from pathlib import Path

# ComfyUI server configuration
COMFYUI_URL = "http://your-comfyui-server:8188"

async def get_workflow_defaults():
    """Get default settings from the workflow."""
    try:
        workflow_path = Path("workflows/hidream_full_config-1.json")
        if not workflow_path.exists():
            print("⚠️  Workflow file not found, using fallback defaults")
            return {
                "width": 1024, "height": 1024, "steps": 50, "cfg": 5,
                "batch_size": 1, "negative_prompt": "bad ugly jpeg artifacts"
            }
        
        with open(workflow_path, 'r') as f:
            workflow = json.load(f)
        
        defaults = {}
        
        # KSampler settings (node 3)
        if "3" in workflow:
            ksampler = workflow["3"]["inputs"]
            defaults.update({
                "steps": ksampler.get("steps", 50),
                "cfg": ksampler.get("cfg", 5),
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
        
        return defaults
        
    except Exception as e:
        print(f"⚠️  Error reading workflow: {e}")
        return {
            "width": 1024, "height": 1024, "steps": 50, "cfg": 5,
            "batch_size": 1, "negative_prompt": "bad ugly jpeg artifacts"
        }

async def manual_test():
    """Interactive manual testing."""
    print("🎨 Manual ComfyUI Test (Using Workflow Defaults)")
    print("=" * 50)
    print(f"🎯 Server: {COMFYUI_URL}")
    print("=" * 50)
    
    # Get workflow defaults
    defaults = await get_workflow_defaults()
    print("🔧 Workflow defaults loaded:")
    print(f"   Size: {defaults['width']}x{defaults['height']}")
    print(f"   Steps: {defaults['steps']}, CFG: {defaults['cfg']}")
    print(f"   Batch: {defaults['batch_size']}")
    print(f"   Negative: {defaults['negative_prompt']}")
    print()
    
    try:
        from image_gen import ImageGenerator, save_output_image, get_unique_filename
        
        # Test connection first
        print("🔍 Testing connection...")
        async with ImageGenerator() as gen:
            gen.base_url = COMFYUI_URL.rstrip('/')
            gen.config.comfyui.url = COMFYUI_URL
            
            if not await gen.test_connection():
                print("❌ Cannot connect to ComfyUI server!")
                return
            
            print("✅ Connected successfully!")
            print()
            
            while True:
                print("📝 Enter your prompt (or 'quit' to exit):")
                prompt = input("> ").strip()
                
                if prompt.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if not prompt:
                    print("⚠️  Please enter a prompt")
                    continue
                
                # Ask if user wants to use defaults or customize
                print(f"\n⚙️  Use workflow defaults? (Y/n)")
                print(f"   Defaults: {defaults['width']}x{defaults['height']}, {defaults['steps']} steps, CFG {defaults['cfg']}")
                use_defaults = input("Use defaults? (Y/n): ").strip().lower()
                
                if use_defaults in ['n', 'no']:
                    # Custom settings
                    print("\n⚙️  Custom settings (press Enter to keep workflow default):")
                    
                    try:
                        width_input = input(f"Width (default {defaults['width']}): ").strip()
                        width = int(width_input) if width_input else defaults['width']
                        
                        height_input = input(f"Height (default {defaults['height']}): ").strip()
                        height = int(height_input) if height_input else defaults['height']
                        
                        steps_input = input(f"Steps (default {defaults['steps']}): ").strip()
                        steps = int(steps_input) if steps_input else defaults['steps']
                        
                        cfg_input = input(f"CFG Scale (default {defaults['cfg']}): ").strip()
                        cfg = float(cfg_input) if cfg_input else defaults['cfg']
                        
                        batch_input = input(f"Batch size (default {defaults['batch_size']}): ").strip()
                        batch_size = int(batch_input) if batch_input else defaults['batch_size']
                        
                        negative_input = input(f"Negative prompt (default: {defaults['negative_prompt'][:30]}...): ").strip()
                        negative_prompt = negative_input if negative_input else defaults['negative_prompt']
                        
                    except ValueError:
                        print("⚠️  Invalid input, using workflow defaults")
                        width, height, steps, cfg, batch_size = defaults['width'], defaults['height'], defaults['steps'], defaults['cfg'], defaults['batch_size']
                        negative_prompt = defaults['negative_prompt']
                else:
                    # Use workflow defaults
                    width, height, steps, cfg, batch_size = defaults['width'], defaults['height'], defaults['steps'], defaults['cfg'], defaults['batch_size']
                    negative_prompt = defaults['negative_prompt']
                
                print(f"\n🎨 Generating image...")
                print(f"   Prompt: {prompt}")
                print(f"   Size: {width}x{height}")
                print(f"   Steps: {steps}, CFG: {cfg}")
                print(f"   Batch: {batch_size}")
                print(f"   Negative: {negative_prompt[:50]}...")
                
                try:
                    # Progress callback
                    async def progress_callback(status: str, queue_position: int = 0):
                        if queue_position > 0:
                            print(f"   📊 {status} (Queue: {queue_position})")
                        else:
                            print(f"   📊 {status}")
                    
                    # Generate image
                    image_data, generation_info = await gen.generate_image(
                        prompt=prompt,
                        negative_prompt=negative_prompt,
                        width=width,
                        height=height,
                        steps=steps,
                        cfg=cfg,
                        batch_size=batch_size,
                        progress_callback=progress_callback
                    )
                    
                    # Save image
                    filename = get_unique_filename("manual_test")
                    output_path = save_output_image(image_data, filename)
                    
                    print(f"\n✅ Success!")
                    print(f"   📁 Saved: {output_path}")
                    print(f"   📊 Size: {len(image_data):,} bytes")
                    print(f"   📸 Images: {generation_info.get('num_images', 1)}")
                    
                    # Ask if user wants to view
                    view = input("\n👀 Open image? (y/N): ").lower()
                    if view == 'y':
                        import subprocess
                        subprocess.run(['open', output_path])  # macOS
                    
                except Exception as e:
                    print(f"\n❌ Generation failed: {e}")
                
                print("\n" + "-" * 50)
    
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure you're running from the virtual environment:")
        print("venv/bin/python manual_test.py")
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main function."""
    try:
        asyncio.run(manual_test())
    except KeyboardInterrupt:
        print("\n👋 Interrupted by user")
    except Exception as e:
        print(f"💥 Error: {e}")

if __name__ == "__main__":
    main() 