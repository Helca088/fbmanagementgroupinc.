import firebase_admin
from firebase_admin import credentials, messaging
from .models import DeviceToken
import traceback
import os
import json

# Initialize once, at import time
if not firebase_admin._apps:
    cred_json = os.environ.get("FIREBASE_CREDENTIALS_JSON")
    if not cred_json:
        raise RuntimeError("FIREBASE_CREDENTIALS_JSON environment variable is not set")
    cred = credentials.Certificate(json.loads(cred_json))
    firebase_admin.initialize_app(cred)



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