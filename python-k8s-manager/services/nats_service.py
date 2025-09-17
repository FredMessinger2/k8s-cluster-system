import asyncio
import nats
import json
import threading
import time
from typing import Optional, Dict, Any
from concurrent.futures import ThreadPoolExecutor

class NatsService:
    """Service for NATS messaging"""
    
    def __init__(self, nats_url: str = "nats://nats-service:4222"):
        self.nats_url = nats_url
        self.nc: Optional[nats.NATS] = None
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self.executor = ThreadPoolExecutor(max_workers=2)
        self._running = False
    
    def start(self) -> bool:
        """Start NATS service in background thread"""
        try:
            # Start event loop in separate thread
            self._running = True
            self.executor.submit(self._run_async_loop)
            
            # Wait a moment for connection
            time.sleep(2)
            return self.nc is not None
            
        except Exception as e:
            print(f"Failed to start NATS service: {e}")
            return False
    
    def _run_async_loop(self):
        """Run asyncio event loop in thread"""
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        
        try:
            self.loop.run_until_complete(self._connect_and_run())
        except Exception as e:
            print(f"NATS async loop error: {e}")
        finally:
            self.loop.close()
    
    async def _connect_and_run(self):
        """Connect to NATS and keep connection alive"""
        try:
            self.nc = await nats.connect(servers=[self.nats_url])
            print(f"Connected to NATS at {self.nats_url}")
            
            # Set up subscriptions
            await self._setup_subscriptions()
            
            # Keep connection alive
            while self._running:
                await asyncio.sleep(1)
                
        except Exception as e:
            print(f"NATS connection error: {e}")
        finally:
            if self.nc:
                await self.nc.close()
    
    async def _setup_subscriptions(self):
        """Set up NATS subscriptions"""
        try:
            # Subscribe to commands
            await self.nc.subscribe("k8s.commands", cb=self._handle_command)
            
            # Subscribe to events
            await self.nc.subscribe("k8s.events", cb=self._handle_event)
            
            print("NATS subscriptions established")
            
        except Exception as e:
            print(f"Error setting up NATS subscriptions: {e}")
    
    async def _handle_command(self, msg):
        """Handle command messages"""
        try:
            command = msg.data.decode()
            print(f"Received command: {command}")
            
            response = {"source": "python-k8s-manager", "command": command, "status": "acknowledged"}
            
            if msg.reply:
                await self.nc.publish(msg.reply, json.dumps(response).encode())
                
        except Exception as e:
            print(f"Error handling command: {e}")
    
    async def _handle_event(self, msg):
        """Handle event messages"""
        try:
            data = msg.data.decode()
            print(f"Received event: {data}")
        except Exception as e:
            print(f"Error handling event: {e}")
    
    def publish_sync(self, subject: str, data: Dict[str, Any]) -> bool:
        """Publish message synchronously (thread-safe)"""
        if not self.nc or not self.loop:
            print("NATS not connected")
            return False
        
        try:
            # Schedule coroutine in the event loop
            future = asyncio.run_coroutine_threadsafe(
                self._publish_async(subject, data), 
                self.loop
            )
            future.result(timeout=5)  # Wait max 5 seconds
            return True
            
        except Exception as e:
            print(f"Error publishing to NATS: {e}")
            return False
    
    async def _publish_async(self, subject: str, data: Dict[str, Any]):
        """Async publish helper"""
        message = json.dumps(data).encode()
        await self.nc.publish(subject, message)
    
    def stop(self):
        """Stop NATS service"""
        print("Stopping NATS service...")
        self._running = False
        if self.executor:
            self.executor.shutdown(wait=True)
