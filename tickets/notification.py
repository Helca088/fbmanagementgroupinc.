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

                webpush=messaging.WebpushConfig(
                fcm_options=messaging.WebpushFCMOptions(
                link=data.get("url") if data and "url" in data else "https://fbmanagement.onrender.com/home/"
        )
    )
            )

            messaging.send(message)

        except Exception as e:
            print(f"Invalid token: {device.token}")
            print(e)

            
            device.delete()