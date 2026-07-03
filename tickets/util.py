def serialize_ticket(ticket):
    return {
        "id": ticket.id,
        "title": ticket.title or "",
        "message": ticket.message or "",
        "status": ticket.status.strip(),
        "user": getattr(ticket.user, "username", str(ticket.user)),
        "section": ticket.section.name if ticket.section else "",
        "concern_type": ticket.concern_type.name if ticket.concern_type else "",
        "scheduled_date": str(ticket.scheduled_date) if ticket.scheduled_date else None,
        "scheduled_time": str(ticket.scheduled_time) if ticket.scheduled_time else None,
        "admin_note": ticket.admin_note or "",
        "created_at": ticket.created_at.isoformat(),
        "attachment": bool(ticket.attachment),
        "outlet": ticket.outlet.name if ticket.outlet else "",
        "outlet_id": ticket.outlet_id,
    }