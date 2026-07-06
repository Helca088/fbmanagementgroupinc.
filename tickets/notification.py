from firebase_admin import messaging
from .models import DeviceToken

def send_push(user, title, body, data=None):
    tokens = DeviceToken.objects.filter(user=user)

    print(f"Found {tokens.count()} tokens for {user.username}")

    if not tokens.exists():
        print("No tokens found.")
        return

    for device in tokens:
        try:
            print("Sending to:", device.token)

            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                token=device.token,
                data=data or {},
            )

            response = messaging.send(message)
            print("Firebase response:", response)

        except Exception as e:
            print("❌ Error sending notification")
            print(e)