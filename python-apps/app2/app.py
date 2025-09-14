import asyncio
import nats
import json
import os
from datetime import datetime

class PythonK8sApp:
    def __init__(self, app_name):
        self.app_name = app_name
        self.nc = None
        
    async def connect_nats(self):
        self.nc = await nats.connect(
            servers=[os.getenv("NATS_URL", "nats://nats-service:4222")]
        )
        print(f"{self.app_name} connected to NATS")
        
    async def subscribe_to_messages(self):
        await self.nc.subscribe("k8s.events", cb=self.message_handler)
        await self.nc.subscribe(f"app.{self.app_name}", cb=self.direct_handler)
        
    async def message_handler(self, msg):
        data = json.loads(msg.data.decode())
        print(f"{self.app_name} received: {data}")
        # Process the message
        
    async def direct_handler(self, msg):
        data = json.loads(msg.data.decode())
        print(f"{self.app_name} direct message: {data}")
        
    async def publish_status(self):
        while True:
            status = {
                "app": self.app_name,
                "timestamp": datetime.now().isoformat(),
                "status": "running"
            }
            await self.nc.publish("app.status", json.dumps(status).encode())
            await asyncio.sleep(30)
            
    async def run(self):
        await self.connect_nats()
        await self.subscribe_to_messages()
        await self.publish_status()

if __name__ == "__main__":
    app = PythonK8sApp(os.getenv("APP_NAME", "app1"))
    asyncio.run(app.run())
