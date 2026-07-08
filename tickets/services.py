from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

def notify_ticket_update(ticket):

    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        "tickets",
        {
            "type":"ticket_update",
            "action":"update",
            "data":{
                "id":ticket.id,
                "status":ticket.status,
                "priority":ticket.priority,
                "assigned_to":ticket.assigned_to.full_name if ticket.assigned_to else "",
                "scheduled_date":str(ticket.scheduled_date or ""),
                "scheduled_time":str(ticket.scheduled_time or ""),
                "admin_note":ticket.admin_note or "",
                "deadline":ticket.deadline.strftime("%Y-%m-%d %H:%M") if ticket.deadline else "",
                "is_overdue":ticket.is_overdue,
            }
        }
    )

    async_to_sync(channel_layer.group_send)(
        f"user_{ticket.user.id}",
        {
            "type":"ticket_update",
            "action":"update",
            "data":{
                "id":ticket.id,
                "status":ticket.status,
                "priority":ticket.priority,
                "assigned_to":ticket.assigned_to.full_name if ticket.assigned_to else "",
                "scheduled_date":str(ticket.scheduled_date or ""),
                "scheduled_time":str(ticket.scheduled_time or ""),
                "admin_note":ticket.admin_note or "",
                "deadline":ticket.deadline.strftime("%Y-%m-%d %H:%M") if ticket.deadline else "",
                "is_overdue":ticket.is_overdue,
            }
        }
    )