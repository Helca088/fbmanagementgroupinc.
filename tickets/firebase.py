import os
import firebase_admin
from firebase_admin import credentials

def init_firebase():
    if not firebase_admin._apps:
        path = os.environ.get("FIREBASE_SERVICE_ACCOUNT")

        if not path:
            raise Exception("FIREBASE_SERVICE_ACCOUNT is not set in environment variables")

        cred = credentials.Certificate(path)
        firebase_admin.initialize_app(cred) 