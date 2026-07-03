from django.shortcuts import render
from django.db.models import Count, F
from django.utils import timezone
from tickets.models import (
    Ticket,
    Technician,
    TicketStatusLog,
    TicketAssignmentLog,
)

def reports(request):
    
    tickets = Ticket.objects.all()

    start = request.GET.get("start")
    end = request.GET.get("end")
    department =request.GET.get("department")

    if start and end:
        tickets = tickets.filter(
        created_at__date__range=[start, end]
        )

    if department:
        tickets = tickets.filter(section__name=department)

    overdue = tickets.filter(
        deadline__lt=timezone.now()
         ).exclude( 
        status="resolved"
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
        technicians = technicians.filter(section__name=department)

    for tech in technicians:

        current_assigned = tickets.filter(
            assigned_to=tech
        ).count()

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
            assigned_to=tech,
            status="resolved",
            resolve_at__lte=F("deadline")
        ).count()

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

    context = {
        "reopened_total": reopened_total,
        "tickets": tickets,
        "total": tickets.count(),
        "pending": tickets.filter(status="pending").count(),
        "progress": tickets.filter(status="progress").count(),
        "resolved": tickets.filter(status="resolved").count(),
        "overdue": overdue,
        "resolved_on_time": resolved_on_time,
        "technician_stats": technician_stats,

        "departments": tickets.values(
            "section__name"
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
