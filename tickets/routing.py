# yourapp/routing.py

from django.urls import path
from .consumer import TicketConsumer

websocket_urlpatterns = [
    path("ws/tickets/", TicketConsumer.as_asgi()),
]