import json
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import login_required
from ..models import DeviceToken
from django.http import JsonResponse
from django.shortcuts import render
from django.db.models import Case, When, IntegerField
from django.utils.text import slugify
from ..models import (
    Ticket,
    ConcernType,
)
@login_required
def ticket_api(request):
    if request.user.is_staff:
        tickets = Ticket.objects.all()
    else:
        tickets = Ticket.objects.filter(user=request.user)

    tickets = tickets.annotate(
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

            "outlet": ticket.outlet,

            "message": ticket.message,
            "user": ticket.user.username if ticket.user else "N/A",

            "section": ticket.section.name if ticket.section else "N/A",
            "section_slug": slugify(ticket.section.name) if ticket.section else "",

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

            "deadline": (
                ticket.deadline.strftime("%Y-%m-%d %H:%M")
                if ticket.deadline else ""
            ),

            "ticket_age": ticket.ticket_age,

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

@require_POST
@login_required
def save_fcm_token(request):
    try:
        data = json.loads(request.body)
        token = data.get("token")

        if not token:
            return JsonResponse(
                {"success": False, "message": "Token is required"},
                status=400
            )

        DeviceToken.objects.update_or_create(
            token=token,
            defaults={
                "user": request.user
            }
        )

        return JsonResponse({
            "success": True
        })

    except Exception as e:
        return JsonResponse(
            {
                "success": False,
                "message": str(e)
            },
            status=500
        )