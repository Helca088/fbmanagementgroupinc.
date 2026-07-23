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
        When(status="pending", then=0),
        When(status="progress", then=1),
        When(status="resolved", then=2),
        When(status="cancelled", then=3),
        default=99,
        output_field=IntegerField(),
    )
).order_by("status_order", "-created_at")
    data = []
    for ticket in tickets:

        attachments = [
            request.build_absolute_uri(a.file.url)
            for a in ticket.attachments.all()
        ]
        data.append({
            "id": ticket.id,
            "outlet_ticket_no": ticket.outlet_ticket_no,
            
            "title": ticket.title or "",
            "message": ticket.message or "",
            "user": ticket.user.username if ticket.user else "",

            "outlet": ticket.outlet.name if ticket.outlet else "",
            "outlet_id": ticket.outlet.pk if ticket.outlet else None,

            "department": ticket.department.name if ticket.department else "",
            "department_slug": slugify(ticket.department.name) if ticket.department else "",

            "concern_type": ticket.concern_type.name if ticket.concern_type else "",

            "status": ticket.status,
            "priority": ticket.priority,

            "assigned_to": (
                ticket.assigned_to.full_name
                if ticket.assigned_to else ""
            ),

            "created_at": ticket.created_at.strftime("%Y-%m-%d %H:%M"),

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
            "ticket_age": ticket.ticket_age(),

            "created_by": ticket.created_by.username if ticket.created_by else "Unknown",
            "created_by_role": "Admin" if ticket.created_by and ticket.created_by.is_staff else "Employee",

            "attachment_url": (
                ticket.attachment.url
                if ticket.attachment else ""
            ),

            "attachments": attachments,  
        })
    return JsonResponse(data, safe=False)

def get_concerns(request):

    department_id = request.GET.get("department")

    concerns = ConcernType.objects.filter(department_id=department_id)

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