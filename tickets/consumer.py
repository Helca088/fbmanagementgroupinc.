from channels.generic.websocket import AsyncWebsocketConsumer
import json

class TicketConsumer(AsyncWebsocketConsumer):

    async def connect(self):
        try:
            user = self.scope["user"]

            await self.accept()

            if user.is_staff:
                await self.channel_layer.group_add(
                    "tickets",
                    self.channel_name
                )
                print("🔥 Admin joined tickets")

            if user.is_authenticated:
                await self.channel_layer.group_add(
                    f"user_{user.id}",
                    self.channel_name
                )
                print(f"🔥 User joined user_{user.id}")

        except Exception as e:
            print("❌ CONNECT ERROR:", e)
            await self.close()  

    async def ticket_update(self, event):
       try:
           print("🔥 EVENT RECEIVED IN CONSUMER:", event)

           await self.send(text_data=json.dumps({
            "action": event.get("action", "update"),
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
        user = self.scope["user"]

        if user.is_staff:
            await self.channel_layer.group_discard(
                "tickets",
                self.channel_name
            )

        if user.is_authenticated:
            await self.channel_layer.group_discard(
                f"user_{user.id}",
                self.channel_name
            )

        print("WS CLOSED:", close_code)