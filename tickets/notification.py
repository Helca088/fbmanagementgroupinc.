from firebase_admin import messaging

from .models import DeviceToken

def send_push(user, title, body, data=None):
    tokens = DeviceToken.objects.filter(user=user)

    if not tokens.exists():
        return

    for device in tokens:
        try:
            message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=body,
                ),
                token=device.token,
                data=data or {},
            )

            messaging.send(message)

        except Exception as e:
            print(f"Invalid token: {device.token}")
            print(e)

            
            device.delete()