"""
WebSocket handler for ComfyUI real-time progress tracking.

Based on the working v1.4.0 implementation with persistent WebSocket connection.
"""

import asyncio
import json
import logging
import time
import uuid
from typing import Dict, Optional, Callable
import websockets
from websockets.exceptions import WebSocketException


class ComfyUIWebSocket:
    """
    Persistent WebSocket connection for ComfyUI progress tracking.
    
    Maintains a single WebSocket connection for the entire bot session,
    monitoring all concurrent generations with auto-reconnect.
    """
    
    def __init__(self, base_url: str, client_id: Optional[str] = None):
        """
        Initialize WebSocket handler.
        
        Args:
            base_url: ComfyUI base URL (http://host:port)
            client_id: Optional client ID (generated if not provided)
        """
        self.logger = logging.getLogger(__name__)
        self.base_url = base_url.rstrip('/')
        
        # Persistent client_id for entire bot session
        self.client_id = client_id or str(uuid.uuid4())
        self.logger.info(f"🤖 WebSocket client_id: {self.client_id[:8]}...")
        
        # WebSocket state
        self._websocket = None
        self._websocket_task: Optional[asyncio.Task] = None
        self._connected = False
        self._active_generations: Dict[str, dict] = {}  # prompt_id -> progress_data
        self._lock = asyncio.Lock()
        
    @property
    def connected(self) -> bool:
        """Check if WebSocket is connected."""
        return self._connected
    
    async def connect(self):
        """Start persistent WebSocket connection."""
        if self._websocket_task and not self._websocket_task.done():
            self.logger.warning("WebSocket already running")
            return
        
        # Build WebSocket URL
        ws_url = self.base_url.replace('http://', 'ws://').replace('https://', 'wss://')
        ws_url = f"{ws_url}/ws"
        
        # Start persistent monitor task
        self._websocket_task = asyncio.create_task(self._persistent_websocket_monitor(ws_url))
        
        # Wait for connection (up to 2 seconds)
        for _ in range(20):
            if self._connected:
                self.logger.info("✅ WebSocket connected successfully")
                return
            await asyncio.sleep(0.1)
        
        self.logger.warning("⚠️ WebSocket not connected after initialization - will retry automatically")
    
    async def disconnect(self):
        """Disconnect WebSocket gracefully."""
        self.logger.info("🛑 Disconnecting WebSocket...")
        
        if self._websocket_task and not self._websocket_task.done():
            self._websocket_task.cancel()
            try:
                await self._websocket_task
            except asyncio.CancelledError:
                pass
        
        self._connected = False
        self.logger.info("✅ WebSocket disconnected")
    
    async def register_generation(
        self,
        prompt_id: str,
        progress_callback: Optional[Callable] = None
    ) -> dict:
        """
        Register a new generation to track.
        
        Args:
            prompt_id: Prompt ID to track
            progress_callback: Optional callback for progress updates
            
        Returns:
            Progress data dictionary
        """
        async with self._lock:
            progress_data = {
                'prompt_id': prompt_id,
                'step_current': 0,
                'step_total': 0,
                'current_node': None,
                'completed': False,
                'cached_nodes': [],
                'last_websocket_update': time.time(),
                'progress_callback': progress_callback
            }
            self._active_generations[prompt_id] = progress_data
            self.logger.info(f"📝 Registered generation tracking: {prompt_id[:8]}...")
            return progress_data
    
    async def unregister_generation(self, prompt_id: str):
        """
        Unregister a generation (cleanup after completion).
        
        Args:
            prompt_id: Prompt ID to unregister
        """
        async with self._lock:
            if prompt_id in self._active_generations:
                del self._active_generations[prompt_id]
                self.logger.info(f"🗑️ Unregistered generation tracking: {prompt_id[:8]}...")
    
    def get_generation_data(self, prompt_id: str) -> Optional[dict]:
        """
        Get progress data for a generation.
        
        Args:
            prompt_id: Prompt ID to get data for
            
        Returns:
            Progress data dictionary or None if not found
        """
        return self._active_generations.get(prompt_id)
    
    async def _persistent_websocket_monitor(self, ws_url: str):
        """
        Persistent WebSocket that monitors ALL generations with auto-reconnect.
        
        Args:
            ws_url: WebSocket URL
        """
        retry_count = 0
        max_retries = 999  # Effectively infinite retries (bot lifetime)
        
        while retry_count < max_retries:
            try:
                full_ws_url = f"{ws_url}?clientId={self.client_id}"
                self.logger.info(f"📡 Connecting persistent WebSocket: {full_ws_url[:50]}...")
                
                async with websockets.connect(full_ws_url) as websocket:
                    self._connected = True
                    retry_count = 0  # Reset on successful connection
                    self.logger.info(f"📡 Persistent WebSocket CONNECTED")
                    
                    # Message processing loop
                    while True:
                        try:
                            message = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                            
                            if isinstance(message, str):
                                await self._process_websocket_message(message)
                        
                        except asyncio.TimeoutError:
                            continue
                        except json.JSONDecodeError as e:
                            self.logger.debug(f"Invalid JSON from WebSocket: {e}")
                            continue
                            
            except WebSocketException as e:
                self._connected = False
                retry_count += 1
                self.logger.warning(f"📡 WebSocket disconnected: {e}. Reconnecting in 5s... (attempt {retry_count})")
                await asyncio.sleep(5)
            except asyncio.CancelledError:
                self.logger.info("📡 Persistent WebSocket monitor cancelled")
                raise
            except Exception as e:
                self._connected = False
                retry_count += 1
                self.logger.error(f"📡 WebSocket error: {e}. Reconnecting in 5s... (attempt {retry_count})")
                await asyncio.sleep(5)
        
        # If we exit the loop (max retries exceeded)
        self._connected = False
        self.logger.error("📡 Persistent WebSocket disconnected - max retries exceeded")
    
    async def _process_websocket_message(self, message: str):
        """
        Process a WebSocket message.
        
        Args:
            message: Raw WebSocket message (JSON string)
        """
        try:
            data = json.loads(message)
            message_type = data.get('type')
            message_data = data.get('data', {})
            
            # Skip monitoring messages
            if message_type == 'crystools.monitor':
                return
            
            # Get prompt_id from message
            msg_prompt_id = message_data.get('prompt_id')
            
            # Find which active generation this is for
            if not msg_prompt_id or msg_prompt_id not in self._active_generations:
                return
            
            progress_data = self._active_generations[msg_prompt_id]
            
            # Handle different message types
            if message_type == 'progress':
                # Step progress (e.g., KSampler steps)
                current_step = message_data.get('value', 0)
                max_steps = message_data.get('max', 0)
                progress_data['step_current'] = current_step
                progress_data['step_total'] = max_steps
                progress_data['last_websocket_update'] = time.time()
                self.logger.info(f"📈 Progress for {msg_prompt_id[:8]}...: {current_step}/{max_steps}")
                
                # Call progress callback if provided
                if progress_data.get('progress_callback'):
                    try:
                        await progress_data['progress_callback'](progress_data)
                    except Exception as e:
                        self.logger.debug(f"Progress callback error: {e}")
            
            elif message_type == 'executing':
                # Node execution
                node_id = message_data.get('node')
                if node_id is not None:
                    progress_data['current_node'] = str(node_id)
                    progress_data['last_websocket_update'] = time.time()
                    self.logger.debug(f"🔧 Executing node {node_id} for {msg_prompt_id[:8]}...")
                else:
                    # node=None means generation completed
                    progress_data['completed'] = True
                    progress_data['last_websocket_update'] = time.time()
                    self.logger.info(f"✅ Completion detected for {msg_prompt_id[:8]}...")
                    
                    # Call progress callback for completion
                    if progress_data.get('progress_callback'):
                        try:
                            await progress_data['progress_callback'](progress_data)
                        except Exception as e:
                            self.logger.debug(f"Completion callback error: {e}")
            
            elif message_type == 'execution_cached':
                # Cached nodes
                cached_nodes = message_data.get('nodes', [])
                progress_data['cached_nodes'] = cached_nodes
                progress_data['last_websocket_update'] = time.time()
                self.logger.debug(f"💾 {len(cached_nodes)} nodes cached for {msg_prompt_id[:8]}...")
            
            elif message_type == 'execution_start':
                progress_data['last_websocket_update'] = time.time()
                self.logger.info(f"▶️ Execution started for {msg_prompt_id[:8]}...")
            
        except Exception as e:
            self.logger.error(f"Error processing WebSocket message: {e}")

