import os
import json
from django.apps import AppConfig
import firebase_admin
from firebase_admin import credentials


class TicketsConfig(AppConfig):
    name = "tickets"

    def ready(self):
        # Import signals
        import tickets.signals

        # Skip if Firebase is already initialized
        if firebase_admin._apps:
            return

        cred_json = os.environ.get("FIREBASE_CREDENTIALS_JSON")

        # Skip Firebase if credentials are not available
        if not cred_json:
            print("⚠️ FIREBASE_CREDENTIALS_JSON not found. Skipping Firebase initialization.")
            return

        cred = credentials.Certificate(json.loads(cred_json))
        firebase_admin.initialize_app(cred)