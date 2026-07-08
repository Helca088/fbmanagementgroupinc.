# apps.py
import os
import json
from django.apps import AppConfig
import firebase_admin
from firebase_admin import credentials


class TicketsConfig(AppConfig):
    name = "tickets"

    def ready(self):

        if not firebase_admin._apps:
            cred_json = os.environ.get("FIREBASE_CREDENTIALS_JSON")
            if not cred_json:
                raise RuntimeError("FIREBASE_CREDENTIALS_JSON environment variable is not set")
            cred = credentials.Certificate(json.loads(cred_json))
            firebase_admin.initialize_app(cred) 