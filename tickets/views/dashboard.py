from django.shortcuts import render
from django.db.models import Case, When, IntegerField, Q
from tickets.models import Ticket

def admin_dashboard(request):

    tickets = Ticket.objects.annotate(
        status_order=Case(
            When(status="Pending", then=0),
            When(status="Open", then=1),
            When(status="Resolved", then=2),
            default=99,
            output_field=IntegerField(),
        )
    ).order_by("status_order", "-created_at")

    q = request.GET.get("q")

    if q:
        tickets = tickets.filter(
            Q(title__icontains=q) |
            Q(message__icontains=q) |
            Q(status__icontains=q) |
            Q(department__name__icontains=q)
        )

    return render(request, "admin.html", {
        "tickets": tickets,
        "total_tickets": tickets.count(),
        "open_tickets": tickets.filter(status="Open").count(),
        "resolved_tickets": tickets.filter(status="Resolved").count(),
    })