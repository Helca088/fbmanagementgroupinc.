from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .util import serialize_ticket
from .models import UserProfile

def notify_ticket_update(ticket, action="update"):

    channel_layer = get_channel_layer()

    payload = {
        "type": "ticket_update",
        "action": action,
        "data": serialize_ticket(ticket),
    }

    # Send to all admin dashboards
    async_to_sync(channel_layer.group_send)(
        "tickets",
        payload,
    )

    # Send only to the ticket owner
    profiles = UserProfile.objects.filter(outlet=ticket.outlet)

    for profile in profiles:
        async_to_sync(channel_layer.group_send)(
            f"user_{profile.user.id}",
            payload,
        )

def notify_ticket_delete(ticket):

    channel_layer = get_channel_layer()

    payload = {
        "type": "ticket_delete",
        "action": "delete",
        "data": {
            "id": ticket.id,
        },
    }

    # Admin dashboard
    async_to_sync(channel_layer.group_send)(
        "tickets",
        payload,
    )

    # Ticket owner
    profiles = UserProfile.objects.filter(outlet=ticket.outlet)

    for profile in profiles:
        async_to_sync(channel_layer.group_send)(
            f"user_{profile.user.id}",
            payload,
        )