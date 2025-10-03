"""
Shared ClientID Test - THE REAL SOLUTION
=========================================

Test using a SINGLE shared clientId for ALL generations.
This way, ONE WebSocket can receive messages for ALL prompts submitted by the bot.

This is the correct fix for the concurrent queue handling bug.
"""

import asyncio
import aiohttp
import json
import uuid
import websockets
from datetime import datetime

COMFYUI_URL = "http://your-comfyui-server:8188"
WS_URL = "ws://your-comfyui-server:8188/ws"

# Load workflow
with open('workflows/flux_lora.json', 'r') as f:
    BASE_WORKFLOW = json.load(f)

# SHARED client_id for ALL generations (simulating a bot session)
SHARED_CLIENT_ID = str(uuid.uuid4())

print(f"Bot Session Client ID: {SHARED_CLIENT_ID}\n")


async def queue_generation_with_shared_id(session: aiohttp.ClientSession, prompt_text: str, gen_num: int, seed: int) -> str:
    """Queue a generation using the SHARED client_id"""
    workflow = json.loads(json.dumps(BASE_WORKFLOW))
    workflow["136"]["inputs"]["text"] = prompt_text
    workflow["25"]["inputs"]["noise_seed"] = seed
    workflow["17"]["inputs"]["steps"] = 15
    
    # Use SHARED client_id (NOT unique per generation)
    payload = {
        "prompt": workflow,
        "client_id": SHARED_CLIENT_ID  # ← THE KEY CHANGE
    }
    
    async with session.post(f"{COMFYUI_URL}/prompt", json=payload) as response:
        result = await response.json()
        prompt_id = result.get('prompt_id')
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        print(f"[{timestamp}] Gen #{gen_num} QUEUED: {prompt_id[:8]}... | client_id: {SHARED_CLIENT_ID[:8]}...")
        
        return prompt_id


async def monitor_with_shared_client_id(prompt_ids: list, duration: int = 90):
    """Monitor ALL generations with ONE WebSocket using shared client_id"""
    print(f"\n{'='*80}")
    print(f"MONITORING WITH SHARED CLIENT ID")
    print(f"WebSocket URL: {WS_URL}?clientId={SHARED_CLIENT_ID}")
    print(f"Tracking {len(prompt_ids)} generations")
    print(f"{'='*80}\n")
    
    generation_progress = {pid: {'messages': 0, 'progress_updates': 0, 'completed': False} for pid in prompt_ids}
    
    try:
        # Connect with SHARED client_id
        async with websockets.connect(f"{WS_URL}?clientId={SHARED_CLIENT_ID}") as websocket:
            print(f"[WS] Connected with shared client_id!\n")
            
            start_time = asyncio.get_event_loop().time()
            last_summary = start_time
            
            while asyncio.get_event_loop().time() - start_time < duration:
                try:
                    message = await asyncio.wait_for(websocket.recv(), timeout=2.0)
                    data = json.loads(message)
                    
                    msg_type = data.get('type')
                    msg_data = data.get('data', {})
                    
                    # Filter out monitoring messages
                    if msg_type == 'crystools.monitor':
                        continue
                    
                    # Check which generation this is for
                    msg_prompt_id = msg_data.get('prompt_id')
                    
                    if msg_prompt_id in generation_progress:
                        generation_progress[msg_prompt_id]['messages'] += 1
                        
                        timestamp = datetime.now().strftime("%H:%M:%S.%f")[:-3]
                        gen_num = prompt_ids.index(msg_prompt_id) + 1
                        
                        if msg_type == 'executing':
                            node = msg_data.get('node')
                            if node is None:
                                generation_progress[msg_prompt_id]['completed'] = True
                                print(f"[{timestamp}] Gen #{gen_num} | [COMPLETED]")
                            else:
                                print(f"[{timestamp}] Gen #{gen_num} | executing node {node}")
                        
                        elif msg_type == 'progress':
                            step = msg_data.get('value')
                            total = msg_data.get('max')
                            generation_progress[msg_prompt_id]['progress_updates'] += 1
                            pct = (step / total * 100) if total > 0 else 0
                            print(f"[{timestamp}] Gen #{gen_num} | Progress: {step}/{total} ({pct:.1f}%)")
                        
                        elif msg_type == 'progress_state':
                            print(f"[{timestamp}] Gen #{gen_num} | progress_state update")
                    
                    elif msg_type == 'status':
                        queue_remaining = msg_data.get('status', {}).get('exec_info', {}).get('queue_remaining')
                        print(f"[{datetime.now().strftime('%H:%M:%S')}] [STATUS] Queue remaining: {queue_remaining}")
                
                except asyncio.TimeoutError:
                    # Print summary every 15 seconds
                    if asyncio.get_event_loop().time() - last_summary >= 15:
                        print(f"\n--- Summary (T+{asyncio.get_event_loop().time() - start_time:.0f}s) ---")
                        for i, pid in enumerate(prompt_ids, 1):
                            stats = generation_progress[pid]
                            status = "DONE" if stats['completed'] else "RUNNING" if stats['progress_updates'] > 0 else "QUEUED"
                            print(f"  Gen #{i}: {status} | {stats['messages']} msgs | {stats['progress_updates']} progress updates")
                        print()
                        last_summary = asyncio.get_event_loop().time()
                    continue
                
                except Exception as e:
                    print(f"[ERROR] {e}")
                    continue
                
                # Check if all completed
                if all(gen['completed'] for gen in generation_progress.values()):
                    print(f"\n[SUCCESS] All generations completed!")
                    break
            
            print(f"\n[WS] Monitoring ended")
            
    except Exception as e:
        print(f"[ERROR] WebSocket error: {e}")
    
    return generation_progress


async def main():
    print("="*80)
    print("SHARED CLIENT ID TEST - Real Solution")
    print("="*80)
    print("Testing: Use ONE client_id for ALL generations\n")
    
    async with aiohttp.ClientSession() as session:
        # Queue 3 generations with SHARED client_id
        prompt_ids = []
        
        for i in range(3):
            prompt_id = await queue_generation_with_shared_id(
                session,
                f"Test image #{i+1}",
                gen_num=i+1,
                seed=50000 + i * 1000
            )
            prompt_ids.append(prompt_id)
            
            # Start them 3 seconds apart
            if i < 2:
                await asyncio.sleep(3)
        
        # Monitor with ONE WebSocket
        results = await monitor_with_shared_client_id(prompt_ids, duration=90)
        
        # Final analysis
        print(f"\n{'='*80}")
        print(f"FINAL RESULTS")
        print(f"{'='*80}\n")
        
        for i, prompt_id in enumerate(prompt_ids, 1):
            stats = results[prompt_id]
            print(f"Generation #{i} [{prompt_id[:8]}...]:")
            print(f"  Completed: {'YES' if stats['completed'] else 'NO'}")
            print(f"  Messages received: {stats['messages']}")
            print(f"  Progress updates: {stats['progress_updates']}")
        
        all_completed = all(gen['completed'] for gen in results.values())
        all_got_messages = all(gen['messages'] > 0 for gen in results.values())
        
        print(f"\n{'='*80}")
        print(f"TEST RESULT")
        print(f"{'='*80}")
        print(f"All Completed: {'PASS' if all_completed else 'FAIL'}")
        print(f"All Received Messages: {'PASS' if all_got_messages else 'FAIL'}")
        
        if all_completed and all_got_messages:
            print(f"\n[SUCCESS] THE SHARED CLIENT_ID APPROACH WORKS!")
            print(f"Solution: Use one persistent client_id for the entire bot session.")
            print(f"This allows ONE WebSocket to receive messages for ALL generations.")
            return True
        else:
            print(f"\n[FAILURE] Shared client_id approach failed")
            return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)

