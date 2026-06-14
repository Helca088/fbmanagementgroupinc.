from channels.generic.websocket import AsyncWebsocketConsumer
import json

class TicketConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        try:
            self.group_name = "tickets"

            await self.channel_layer.group_add(
                self.group_name,
                self.channel_name
            )

            await self.accept()

            print("🔥 WS CONNECTED SUCCESSFULLY")

        except Exception as e:
            print("❌ CONNECT ERROR:", e)
            await self.close()

    async def disconnect(self, close_code):
        try:
            await self.channel_layer.group_discard(
                "tickets",
                self.channel_name
            )
            print("⚠️ WS DISCONNECTED")
        except Exception as e:
            print("❌ DISCONNECT ERROR:", e)

    async def ticket_update(self, event):
       try:
           print("🔥 EVENT RECEIVED IN CONSUMER:", event)

           await self.send(text_data=json.dumps({
            "action": event.get("action", "create"),
            "data": event["data"]
        }))

       except Exception as e:
        print("❌ SEND ERROR:", e)

    async def ticket_delete(self, event):
        print("Delete receive:", event)
        await self.send(text_data=json.dumps({
        "action": "delete",
        "data": event["data"]
    }))
        
    async def disconnect(self, close_code):
        print("WS CLOSED:", close_code)

        await self.channel_layer.group_discard(
        "tickets",
            self.channel_name
    )