from firebase_admin import messaging
from firebase_admin._messaging_utils import UnregisteredError
from .models import DeviceToken
import traceback

def send_push(user, title, body, data=None):
    tokens = DeviceToken.objects.filter(user=user)

    print("=" * 50)
    print("Sending to:", user.username)
    print("Token count:", tokens.count())

    if not tokens.exists():
        print("❌ No tokens found")
        return

    for device in tokens:
        print("Using token:", device.token[:40])

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
            print("✅ SUCCESS:", response)

        except UnregisteredError:
            print("❌ Invalid token, deleting")
            device.delete()

        except Exception:
            print("❌ SEND FAILED")
            traceback.print_exc()