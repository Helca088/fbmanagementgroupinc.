def serialize_ticket(ticket):
    return {
        "id": ticket.id,
        "title": ticket.title or "",
        "message": ticket.message or "",
        "status": ticket.status.strip(),
        "user": ticket.user.username if ticket.user else "",
        "section": ticket.section.name if ticket.section else "",
        "concern_type": ticket.concern_type.name if ticket.concern_type else "",
        "priority": ticket.priority,
        "assigned_to": (
            ticket.assigned_to.full_name
            if ticket.assigned_to else ""
        ),
        "scheduled_date": (
            str(ticket.scheduled_date)
            if ticket.scheduled_date else ""
        ),
        "scheduled_time": (
            str(ticket.scheduled_time)
            if ticket.scheduled_time else ""
        ),
        "admin_note": ticket.admin_note or "",
        "deadline": (
            ticket.deadline.strftime("%Y-%m-%d %H:%M")
            if ticket.deadline else ""
        ),
        "is_overdue": ticket.is_overdue,
        "created_at": ticket.created_at.isoformat(),
        "outlet": str(ticket.outlet) if ticket.outlet else "",
        "outlet_id": ticket.outlet_id,
    }
