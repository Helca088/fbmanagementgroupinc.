# apps.py
from django.apps import AppConfig
import firebase_admin
from firebase_admin import credentials

class TicketsConfig(AppConfig):
    name = "tickets"

    def ready(self):
        if not firebase_admin._apps:
            cred = credentials.Certificate("serviceAccountKey.json")
            firebase_admin.initialize_app(cred)