from django.shortcuts import render
from django.db.models import Count, F, Q
from django.utils import timezone
from tickets.models import (
    Ticket,
    Technician,
    TicketStatusLog,
    TicketAssignmentLog,
    Outlet,
)

def reports(request):
    
    tickets = Ticket.objects.all()

    start = request.GET.get("start")
    end = request.GET.get("end")
    department =request.GET.get("department")
    outlet = request.GET.get("outlet")

    if start and end:
        tickets = tickets.filter(
        created_at__date__range=[start, end]
        )

    if department:
        tickets = tickets.filter(department__name=department)

    if outlet:
        tickets = tickets.filter(outlet_id=outlet)

    overdue = tickets.filter(
        deadline__lt=timezone.now()
         ).exclude( 
        status__in=["resolved", "cancelled"]  
        ).count()
    resolved_on_time = tickets.filter(
        status="resolved",
        resolve_at__lte=F("deadline")
        ).count()
    
    reopened_total = TicketStatusLog.objects.filter(
        old_status="resolved"
        ).values("ticket").distinct().count()

    technician_stats = []

    technicians = Technician.objects.all()

    if department:
        technicians = technicians.filter(department__name=department)

    for tech in technicians:

        current_assigned = tickets.filter(
            Q(assigned_to=tech) |
            Q(additional_technicians=tech)
        ).distinct().count()

        total_assigned = TicketAssignmentLog.objects.filter(
            new_technician=tech,
            ticket__in=tickets
        ).count()

        resolved = TicketStatusLog.objects.filter(
            technician=tech,
            new_status="resolved",
            ticket__in=tickets
        ).count()

        resolved_on_time = tickets.filter(
            Q(assigned_to=tech) |
            Q(additional_technicians=tech),
            status="resolved",
            resolve_at__lte=F("deadline")
        ).distinct().count()

        reopened = TicketStatusLog.objects.filter(
            technician=tech,
            old_status="resolved"
        ).count()

        technician_stats.append({
            "name": tech.full_name,
            "current_assigned": current_assigned,
            "total_assigned": total_assigned,
            "resolved": resolved,
            "resolved_on_time": resolved_on_time,
            "reopened": reopened,
    })

    outlet_summary = (
            tickets.values(
                "outlet__name"
            )
            .annotate(
                total=Count("id"),
                pending=Count(
                    "id",
                    filter=Q(status="pending")
                ),
                progress=Count(
                    "id",
                    filter=Q(status="progress")
                ),
                resolved=Count(
                    "id",
                    filter=Q(status="resolved")
                ),
                cancelled=Count(
                    "id",
                    filter=Q(status="cancelled")
                ),
            )
            .order_by("outlet__name")
        )

    concerns_per_outlet = (
            tickets.values(
                "outlet__name",
                "concern_type__name"
            )
            .annotate(
                total=Count("id")
            )
            .order_by(
                "outlet__name",
                "-total"
            )
        )
    
    context = {
        "concerns_per_outlet": concerns_per_outlet,
        "outlet_summary": outlet_summary,
        "context_outlets": Outlet.objects.all(),
        "reopened_total": reopened_total,
        "tickets": tickets,
        "total": tickets.count(),
        "pending": tickets.filter(status="pending").count(),
        "progress": tickets.filter(status="progress").count(),
        "resolved": tickets.filter(status="resolved").count(),
        "cancelled": tickets.filter(status="cancelled").count(),
        "overdue": overdue,
        "resolved_on_time": resolved_on_time,
        "technician_stats": technician_stats,

        "departments": tickets.values(
            "department__name"
        ).annotate(
            total=Count("id")
        ).order_by("-total"),

        "concerns": tickets.values(
            "concern_type__name"
        ).annotate(
            total=Count("id")
        ).order_by("-total"),

        "outlets": tickets.values(
            "outlet",
            "outlet__name"
        ).annotate(
            total=Count("id")
        ).order_by("-total"),
    }   

    return render(
        request,
        "reports.html",
        context
    )     
