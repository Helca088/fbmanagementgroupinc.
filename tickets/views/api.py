from django.http import JsonResponse
from django.shortcuts import render
from django.db.models import Case, When, IntegerField

from ..models import (
    Ticket,
    ConcernType,
)

def ticket_api(request):
    tickets = Ticket.objects.annotate(
    status_order=Case(
        When(status='Pending', then=0),
        When(status='Open', then=1),
        When(status='Resolved', then=2),
        default=99,
        output_field=IntegerField(),
    )
).order_by('status_order', '-created_at')
    data = []
    for ticket in tickets:

        attachments = [
            request.build_absolute_uri(a.file.url)
            for a in ticket.attachments.all()
        ]
        data.append({
            "id": ticket.id,
            "title": ticket.title,
            "message": ticket.message,
            "user": ticket.user.username if ticket.user else "N/A",
            "section": ticket.section.name if ticket.section else "N/A",
            "concern_type": ticket.concern_type.name if ticket.concern_type else "N/A",
            "status": ticket.status,
            "priority": ticket.priority,
            "assigned_to": (
            ticket.assigned_to.full_name
            if ticket.assigned_to else ""
            ),
            "created_at": ticket.created_at.strftime("%Y-%m-%d %H:%M"),
            "attachments": attachments,
            "scheduled_date": ticket.scheduled_date.strftime("%Y-%m-%d") if ticket.scheduled_date else "",
            "scheduled_time": ticket.scheduled_time.strftime("%H:%M") if ticket.scheduled_time else "",
            "admin_note": ticket.admin_note or "",
            "deadline": (ticket.deadline.strftime("%Y-%m-%d %H:%M")if ticket.deadline else ""),
            "is_overdue": ticket.is_overdue,  
        })
    return JsonResponse(data, safe=False)

def get_concerns(request):

    section_id = request.GET.get("section")

    concerns = ConcernType.objects.filter(section_id=section_id)

    return render(
     request, "partials/concern_options.html",
     {
         "concerns": concerns
     }
 )   