#!/usr/bin/env python3
"""
NATS Metrics Subscriber - Listen to k8s.metrics messages
Run this to see real-time metrics published by the Java K8s manager
"""

import asyncio
import nats
import json
import signal
import sys
from datetime import datetime

class NatsMetricsSubscriber:
    def __init__(self, nats_url="nats://localhost:4222"):
        self.nats_url = nats_url
        self.nc = None
        self.running = True
        
    async def connect(self):
        """Connect to NATS server"""
        try:
            self.nc = await nats.connect(servers=[self.nats_url])
            print(f"Connected to NATS at {self.nats_url}")
            return True
        except Exception as e:
            print(f"Failed to connect to NATS: {e}")
            return False
    
    async def message_handler(self, msg):
        """Handle incoming metrics messages"""
        try:
            # Parse JSON message
            data = json.loads(msg.data.decode())
            timestamp = datetime.now().strftime("%H:%M:%S")
            
            print(f"\n[{timestamp}] METRICS MESSAGE:")
            print("-" * 40)
            print(f"Subject: {msg.subject}")
            
            # Pretty print the metrics data
            if isinstance(data, dict):
                for key, value in data.items():
                    if key == "timestamp":
                        # Convert timestamp to readable format
                        dt = datetime.fromtimestamp(value / 1000)
                        print(f"{key:>15}: {dt.strftime('%Y-%m-%d %H:%M:%S')}")
                    else:
                        print(f"{key:>15}: {value}")
            else:
                print(f"Data: {data}")
                
        except json.JSONDecodeError:
            # Handle non-JSON messages
            data = msg.data.decode()
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"\n[{timestamp}] RAW MESSAGE:")
            print("-" * 40)
            print(f"Subject: {msg.subject}")
            print(f"Data: {data}")
        except Exception as e:
            print(f"Error processing message: {e}")
    
    async def subscribe_to_metrics(self):
        """Subscribe to k8s.metrics topic"""
        try:
            await self.nc.subscribe("k8s.metrics", cb=self.message_handler)
            print("Subscribed to k8s.metrics topic")
            print("Waiting for messages... (Ctrl+C to exit)")
            print("=" * 50)
            
            # Keep the subscriber running
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            print(f"Error subscribing: {e}")
    
    async def subscribe_to_all_topics(self):
        """Subscribe to multiple topics for debugging"""
        topics = [
            "k8s.metrics",
            "k8s.events", 
            "app.status",
            "k8s.commands"
        ]
        
        try:
            for topic in topics:
                await self.nc.subscribe(topic, cb=self.message_handler)
                print(f"Subscribed to {topic}")
            
            print("\nListening to all topics... (Ctrl+C to exit)")
            print("=" * 50)
            
            while self.running:
                await asyncio.sleep(1)
                
        except Exception as e:
            print(f"Error subscribing to topics: {e}")
    
    def stop(self):
        """Stop the subscriber"""
        self.running = False
    
    async def close(self):
        """Close NATS connection"""
        if self.nc:
            await self.nc.close()
            print("\nNATS connection closed")

async def main():
    # Default to port-forwarded NATS (you'll need to port-forward NATS service)
    nats_url = "nats://localhost:4222"
    
    print("K8s Metrics NATS Subscriber")
    print("=" * 30)
    print(f"Connecting to NATS at: {nats_url}")
    print("Note: Make sure to port-forward NATS service:")
    print("  kubectl port-forward svc/nats-service 4222:4222")
    print()
    
    subscriber = NatsMetricsSubscriber(nats_url)
    
    # Setup signal handler for graceful shutdown
    def signal_handler():
        print("\nShutting down...")
        subscriber.stop()
    
    # Handle Ctrl+C
    if sys.platform != "win32":
        loop = asyncio.get_event_loop()
        for sig in [signal.SIGINT, signal.SIGTERM]:
            loop.add_signal_handler(sig, signal_handler)
    
    try:
        # Connect to NATS
        if not await subscriber.connect():
            return
        
        # Ask user what to subscribe to
        print("Choose subscription mode:")
        print("1. Only k8s.metrics (default)")
        print("2. All topics (k8s.metrics, k8s.events, app.status, k8s.commands)")
        
        try:
            choice = input("Enter choice (1 or 2): ").strip()
        except KeyboardInterrupt:
            choice = "1"
        
        if choice == "2":
            await subscriber.subscribe_to_all_topics()
        else:
            await subscriber.subscribe_to_metrics()
            
    except KeyboardInterrupt:
        pass
    finally:
        await subscriber.close()

if __name__ == "__main__":
    # Create requirements.txt reminder
    print("Required packages: nats-py")
    print("Install with: pip install nats-py")
    print()
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExited by user")