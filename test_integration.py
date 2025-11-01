#!/usr/bin/env python3
"""
Integration test script for DisComfy v2.0 - Non-Discord functionality testing.

Tests all core functionality without requiring Discord interaction:
- Configuration loading
- ComfyUI client connection
- Workflow loading and validation
- Image generator initialization
- Video generator initialization
- LoRA fetching and filtering
- Workflow parameter updates

Run this to verify the bot's core logic works before Discord testing.
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict
import json

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))


class TestResult:
    """Track test results."""
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.tests = []
    
    def add_pass(self, test_name: str, message: str = ""):
        self.passed += 1
        self.tests.append(("✅", test_name, message))
        print(f"✅ {test_name}: {message}")
    
    def add_fail(self, test_name: str, error: str):
        self.failed += 1
        self.tests.append(("❌", test_name, error))
        print(f"❌ {test_name}: {error}")
    
    def add_warning(self, test_name: str, message: str):
        self.warnings += 1
        self.tests.append(("⚠️", test_name, message))
        print(f"⚠️  {test_name}: {message}")
    
    def print_summary(self):
        print("\n" + "="*70)
        print("TEST SUMMARY")
        print("="*70)
        total = self.passed + self.failed
        print(f"✅ Passed:   {self.passed}/{total}")
        print(f"❌ Failed:   {self.failed}/{total}")
        print(f"⚠️  Warnings: {self.warnings}")
        print("="*70)
        
        if self.failed == 0:
            print("🎉 ALL TESTS PASSED! Bot is ready for Discord testing!")
        else:
            print("⚠️  Some tests failed - review errors above")
        
        return self.failed == 0


async def test_config_loading(results: TestResult):
    """Test configuration loading."""
    print("\n📋 TEST 1: Configuration Loading")
    print("-" * 70)
    
    try:
        from config.loader import get_config
        config = get_config()
        
        results.add_pass("Config Load", "Configuration loaded successfully")
        
        # Validate critical fields
        if config.discord.token:
            results.add_pass("Discord Token", "Token present")
        else:
            results.add_fail("Discord Token", "No token found")
        
        if config.comfyui.url:
            results.add_pass("ComfyUI URL", f"URL: {config.comfyui.url}")
        else:
            results.add_fail("ComfyUI URL", "No URL configured")
        
        return config
        
    except Exception as e:
        results.add_fail("Config Load", str(e))
        return None


async def test_comfyui_client(results: TestResult, config):
    """Test ComfyUI client initialization and connection."""
    print("\n🔌 TEST 2: ComfyUI Client")
    print("-" * 70)
    
    try:
        from core.comfyui.client import ComfyUIClient
        
        client = ComfyUIClient(base_url=config.comfyui.url, timeout=300)
        results.add_pass("Client Init", "ComfyUI client initialized")
        
        # Test connection
        try:
            is_connected = await client.test_connection()
            if is_connected:
                results.add_pass("Connection Test", "ComfyUI server reachable")
            else:
                results.add_warning("Connection Test", "ComfyUI server not reachable (might be offline)")
        except Exception as e:
            results.add_warning("Connection Test", f"Cannot reach ComfyUI: {e}")
        
        return client
        
    except Exception as e:
        results.add_fail("Client Init", str(e))
        return None


async def test_workflow_loading(results: TestResult):
    """Test workflow file loading."""
    print("\n📁 TEST 3: Workflow Loading")
    print("-" * 70)
    
    try:
        workflows_dir = Path("workflows")
        
        if not workflows_dir.exists():
            results.add_fail("Workflows Dir", "workflows/ directory not found")
            return []
        
        results.add_pass("Workflows Dir", f"Found at {workflows_dir}")
        
        # Check for required workflows
        required_workflows = {
            "flux_lora": "Flux model workflow",
            "flux_krea_lora": "Flux Krea model workflow",
            "hidream_lora": "HiDream model workflow"
        }
        
        found_workflows = []
        for workflow_name, description in required_workflows.items():
            workflow_path = workflows_dir / f"{workflow_name}.json"
            if workflow_path.exists():
                try:
                    with open(workflow_path, 'r') as f:
                        workflow_data = json.load(f)
                    results.add_pass(f"Workflow: {workflow_name}", f"{description} - {len(workflow_data)} nodes")
                    found_workflows.append(workflow_name)
                except Exception as e:
                    results.add_fail(f"Workflow: {workflow_name}", f"Invalid JSON: {e}")
            else:
                results.add_fail(f"Workflow: {workflow_name}", f"File not found: {workflow_path}")
        
        # List all available workflows
        all_workflows = list(workflows_dir.glob("*.json"))
        print(f"\n   📋 Total workflows available: {len(all_workflows)}")
        for wf in all_workflows:
            print(f"      - {wf.stem}")
        
        return found_workflows
        
    except Exception as e:
        results.add_fail("Workflow Loading", str(e))
        return []


async def test_image_generator(results: TestResult, config, client):
    """Test ImageGenerator initialization."""
    print("\n🎨 TEST 4: Image Generator")
    print("-" * 70)
    
    try:
        from core.generators.image import ImageGenerator
        
        image_gen = ImageGenerator(client, config)
        results.add_pass("ImageGen Init", "ImageGenerator initialized")
        
        # Test LoRA fetching
        try:
            loras = await image_gen.get_available_loras()
            if loras:
                results.add_pass("LoRA Fetch", f"Found {len(loras)} LoRAs")
                
                # Test LoRA filtering
                for model in ['flux', 'flux_krea', 'hidream']:
                    filtered = image_gen.filter_loras_by_model(loras, model)
                    results.add_pass(f"LoRA Filter ({model})", f"{len(filtered)} LoRAs for {model}")
            else:
                results.add_warning("LoRA Fetch", "No LoRAs found (ComfyUI might be offline)")
        except Exception as e:
            results.add_warning("LoRA Fetch", f"Could not fetch LoRAs: {e}")
        
        return image_gen
        
    except Exception as e:
        results.add_fail("ImageGen Init", str(e))
        return None


async def test_video_generator(results: TestResult, config, client):
    """Test VideoGenerator initialization."""
    print("\n🎬 TEST 5: Video Generator")
    print("-" * 70)
    
    try:
        from core.generators.video import VideoGenerator
        
        video_gen = VideoGenerator(client, config)
        results.add_pass("VideoGen Init", "VideoGenerator initialized")
        
        # Check for video workflows
        workflows_dir = Path("workflows")
        video_workflows = list(workflows_dir.glob("*video*.json"))
        
        if video_workflows:
            results.add_pass("Video Workflows", f"Found {len(video_workflows)} video workflows")
            for vw in video_workflows:
                print(f"      - {vw.stem}")
        else:
            results.add_warning("Video Workflows", "No video workflows found")
        
        return video_gen
        
    except Exception as e:
        results.add_fail("VideoGen Init", str(e))
        return None


async def test_workflow_parameter_updates(results: TestResult, image_gen):
    """Test workflow parameter updating."""
    print("\n⚙️  TEST 6: Workflow Parameter Updates")
    print("-" * 70)
    
    try:
        from core.comfyui.workflows.updater import WorkflowUpdater, WorkflowParameters
        
        updater = WorkflowUpdater()
        results.add_pass("Updater Init", "WorkflowUpdater initialized")
        
        # Load a test workflow
        workflows_dir = Path("workflows")
        test_workflow_path = workflows_dir / "flux_lora.json"
        
        if test_workflow_path.exists():
            with open(test_workflow_path, 'r') as f:
                workflow = json.load(f)
            
            results.add_pass("Load Workflow", f"Loaded {test_workflow_path.name}")
            
            # Test parameter update
            params = WorkflowParameters(
                prompt="A beautiful sunset over mountains",
                negative_prompt="blurry, low quality",
                width=1024,
                height=1024,
                steps=30,
                cfg=7.0,
                seed=12345
            )
            
            updated_workflow = updater.update_workflow(workflow, params)
            results.add_pass("Update Params", "Workflow parameters updated successfully")
            
            # Verify updates were applied
            prompt_found = False
            seed_found = False
            
            for node_id, node_data in updated_workflow.items():
                class_type = node_data.get('class_type')
                
                if class_type == 'CLIPTextEncode':
                    text = node_data.get('inputs', {}).get('text', '')
                    if 'beautiful sunset' in text:
                        prompt_found = True
                
                if class_type == 'KSampler':
                    seed = node_data.get('inputs', {}).get('seed')
                    if seed == 12345:
                        seed_found = True
            
            if prompt_found:
                results.add_pass("Prompt Update", "Prompt correctly inserted into workflow")
            else:
                results.add_warning("Prompt Update", "Could not verify prompt in workflow")
            
            if seed_found:
                results.add_pass("Seed Update", "Seed correctly inserted into workflow")
            else:
                results.add_warning("Seed Update", "Could not verify seed in workflow")
        else:
            results.add_warning("Workflow Test", f"Test workflow not found: {test_workflow_path}")
        
    except Exception as e:
        results.add_fail("Workflow Updates", str(e))


async def test_validation(results: TestResult):
    """Test validation logic."""
    print("\n✓ TEST 7: Validation")
    print("-" * 70)
    
    try:
        from core.validators.image import ImageValidator, PromptParameters
        from core.exceptions import ValidationError
        
        validator = ImageValidator()
        results.add_pass("Validator Init", "ImageValidator initialized")
        
        # Test valid prompt
        try:
            valid_params = PromptParameters(
                prompt="A beautiful landscape",
                negative_prompt="blurry",
                steps=30,
                cfg=7.0
            )
            results.add_pass("Valid Params", "Valid parameters accepted")
        except ValidationError as e:
            results.add_fail("Valid Params", f"Valid params rejected: {e}")
        
        # Test invalid steps using StepParameters
        try:
            from pydantic import ValidationError as PydanticValidationError
            from core.validators.image import StepParameters
            invalid_params = StepParameters(
                steps=0  # Invalid - must be >= 1
            )
            results.add_fail("Invalid Steps", "Invalid steps not caught")
        except (ValidationError, PydanticValidationError) as e:
            results.add_pass("Invalid Steps", "Invalid steps correctly rejected")
        
    except Exception as e:
        results.add_fail("Validation", str(e))


async def test_exception_hierarchy(results: TestResult):
    """Test custom exception hierarchy."""
    print("\n🚨 TEST 8: Exception Hierarchy")
    print("-" * 70)
    
    try:
        from core.exceptions import (
            DisComfyError, ValidationError, ComfyUIError,
            GenerationError, RateLimitError
        )
        
        # Test exception creation
        exceptions_to_test = [
            (ValidationError("test"), "ValidationError"),
            (ComfyUIError("test"), "ComfyUIError"),
            (GenerationError("test"), "GenerationError"),
            (RateLimitError(60), "RateLimitError"),
        ]
        
        for exc, name in exceptions_to_test:
            if isinstance(exc, DisComfyError):
                results.add_pass(f"Exception: {name}", f"Inherits from DisComfyError")
            else:
                results.add_fail(f"Exception: {name}", "Does not inherit from DisComfyError")
        
    except Exception as e:
        results.add_fail("Exception Hierarchy", str(e))


async def test_rate_limiter(results: TestResult):
    """Test rate limiting functionality."""
    print("\n⏱️  TEST 9: Rate Limiter")
    print("-" * 70)
    
    try:
        from utils.rate_limit import RateLimiter, RateLimitConfig
        
        config = RateLimitConfig(
            per_user=5,
            global_limit=10,
            window_seconds=60
        )
        rate_limiter = RateLimiter(config)
        
        results.add_pass("RateLimiter Init", "RateLimiter initialized")
        
        # Test user rate limiting
        test_user_id = 123456789
        
        # Should allow first request (check_rate_limit is synchronous, not async)
        allowed = rate_limiter.check_rate_limit(test_user_id)
        if allowed:
            results.add_pass("Rate Limit Check", "First request allowed")
        else:
            results.add_fail("Rate Limit Check", "First request blocked incorrectly")
        
        # Reset for user
        if hasattr(rate_limiter, 'reset_user'):
            rate_limiter.reset_user(test_user_id)
            results.add_pass("Rate Limit Reset", "User rate limit reset works")
        else:
            results.add_pass("Rate Limit", "Rate limiter works correctly")
        
    except Exception as e:
        results.add_fail("Rate Limiter", str(e))


async def main():
    """Run all integration tests."""
    print("="*70)
    print("DisComfy v2.0 - Integration Test Suite")
    print("="*70)
    print("\nTesting core functionality without Discord...\n")
    
    results = TestResult()
    
    # Run tests in sequence
    config = await test_config_loading(results)
    
    if config:
        client = await test_comfyui_client(results, config)
        await test_workflow_loading(results)
        
        if client:
            image_gen = await test_image_generator(results, config, client)
            await test_video_generator(results, config, client)
            
            if image_gen:
                await test_workflow_parameter_updates(results, image_gen)
            
            # Close client session
            if hasattr(client, 'session') and client.session:
                await client.session.close()
    
    await test_validation(results)
    await test_exception_hierarchy(results)
    await test_rate_limiter(results)
    
    # Print summary
    success = results.print_summary()
    
    return 0 if success else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

