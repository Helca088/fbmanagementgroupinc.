from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .util import serialize_ticket

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
    async_to_sync(channel_layer.group_send)(
        f"user_{ticket.user.id}",
        payload,
    )


def notify_ticket_delete(ticket_id):

    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        "tickets",
        {
            "type": "ticket_delete",
            "data": {"id": ticket_id},
        },
    )