from django.utils.text import slugify

def serialize_ticket(ticket):
    return {
        "id": ticket.id,
        "title": ticket.title or "",
        "message": ticket.message or "",
        "status": ticket.status,
        "user": ticket.user.username if ticket.user else "",

        "department": ticket.department.name if ticket.department else "",
        "department_slug": slugify(ticket.department.name) if ticket.department else "",

        "concern_type": (
            ticket.concern_type.name
            if ticket.concern_type else ""
        ),

        "priority": ticket.priority,

        "assigned_to": (
            ticket.assigned_to.full_name
            if ticket.assigned_to else ""
        ),

        "scheduled_date": (
            ticket.scheduled_date.strftime("%Y-%m-%d")
            if ticket.scheduled_date else ""
        ),

        "scheduled_time": (
            ticket.scheduled_time.strftime("%H:%M")
            if ticket.scheduled_time else ""
        ),

        "admin_note": ticket.admin_note or "",

        "deadline": (
            ticket.deadline.strftime("%Y-%m-%d %H:%M")
            if ticket.deadline else ""
        ),

        "is_overdue": ticket.is_overdue,

        "created_at": ticket.created_at.strftime("%Y-%m-%d %H:%M"),

        # IMPORTANT
        "outlet": ticket.outlet.name if ticket.outlet else "",
        "outlet_id": ticket.outlet.pk if ticket.outlet else None,

        "ticket_age": ticket.ticket_age(),

        "attachment_url": (
            ticket.attachment.url
            if ticket.attachment else ""
        ),
    }