from firebase_admin import messaging
from .models import DeviceToken
import traceback


def send_push(user, title, body, data=None):
    tokens = DeviceToken.objects.filter(user=user)

    print(f"Found {tokens.count()} tokens")

    if not tokens.exists():
        return "No tokens"

    for device in tokens:
        try:
            message = messaging.Message(
                token=device.token,
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                data=data or {},
            )

            response = messaging.send(message)
            print("SUCCESS:", response)
            return response

        except Exception:
            traceback.print_exc()
            raise