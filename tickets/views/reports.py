from datetime import datetime, timedelta

from django.shortcuts import render
from django.template.loader import render_to_string
from django.http import HttpResponse, JsonResponse
from django.db.models import (
    Count,
    Q,
    Avg,
    F,
)
from django.utils import timezone

from tickets.models import (
    Ticket,
    Technician,
    TicketStatusLog,
    TicketAssignmentLog,
    TicketAdditionalAssignmentLog,
    Outlet,
    Department,
    ConcernType
)


# ============================================================
# COMMON FILTER
# ============================================================

def get_filtered_tickets(request):

    tickets = Ticket.objects.all()

    start = request.GET.get("start", "").strip()
    end = request.GET.get("end", "").strip()
    department = request.GET.get("department", "").strip()
    outlet = request.GET.get("outlet", "").strip()
    status = request.GET.get("status", "").strip()   # NEW

    # DATE
    if start and end:

        tickets = tickets.filter(
            created_at__date__range=[start, end]
        )

    elif start:

        tickets = tickets.filter(
            created_at__date__gte=start
        )

    elif end:

        tickets = tickets.filter(
            created_at__date__lte=end
        )

    # DEPARTMENT
    if department:

        tickets = tickets.filter(
            department__name=department
        )

    # OUTLET
    if outlet:

        tickets = tickets.filter(
            outlet_id=outlet
        )

    # STATUS
    if status:
        tickets = tickets.filter(
            status=status
        )

    return tickets


# ============================================================
# COMMON REPORT CONTEXT
# ============================================================

def report_common_context(request):

    return {

        "context_outlets":
            Outlet.objects.all().order_by("name"),

        "context_departments":
            Department.objects.all().order_by("name"),

        "context_concerns":
            ConcernType.objects.all().order_by("name"),

        "selected_start":
            request.GET.get("start", ""),

        "selected_end":
            request.GET.get("end", ""),

        "selected_department":
            request.GET.get("department", ""),

        "selected_outlet":
            request.GET.get("outlet", ""),

        "selected_concern":
            request.GET.get("concern", ""),

        "selected_status":
            request.GET.get("status", ""),   # NEW
    }


# ============================================================
# DASHBOARD
# ============================================================

# ============================================================
# DASHBOARD
# ============================================================

def reports(request):

    tickets = get_filtered_tickets(request)

    sort = request.GET.get("sort", "name").strip()
    concern_sort = request.GET.get("concern_sort", "name").strip()
    outlet_sort = request.GET.get("outlet_sort", "name").strip()
    technician_sort = request.GET.get("technician_sort", "name").strip()
    concerns_outlet_sort = request.GET.get(
        "concerns_outlet_sort",
        "outlet"
    ).strip()
    chart_sort = request.GET.get("chart_sort", "-total")

    # ============================================================
    # BASIC COUNTS
    # ============================================================

    total = tickets.count()
    pending = tickets.filter(status="pending").count()
    progress = tickets.filter(status="progress").count()
    resolved = tickets.filter(status="resolved").count()
    cancelled = tickets.filter(status="cancelled").count()

    # ============================================================
    # OVERDUE
    # ============================================================

    overdue = tickets.filter(
        deadline__lt=timezone.now()
    ).exclude(
        status__in=["resolved", "cancelled"]
    ).count()

    # ============================================================
    # RESOLVED ON TIME
    # ============================================================

    resolved_on_time = tickets.filter(
        status="resolved",
        resolve_at__isnull=False,
        deadline__isnull=False,
        resolve_at__lte=F("deadline")
    ).count()

    # ============================================================
    # REOPENED
    # ============================================================

    reopened_total = (
        TicketStatusLog.objects
        .filter(old_status="resolved", ticket__in=tickets)
        .values("ticket")
        .distinct()
        .count()
    )

    # ============================================================
    # TECHNICIAN STATISTICS
    # ============================================================

    technician_stats = []
    technician_performance = []

    technicians = (
        Technician.objects
        .select_related("department")
        .all()
        .order_by("full_name")
    )

    selected_department = request.GET.get("department", "").strip()

    if selected_department:
        technicians = technicians.filter(
            department__name=selected_department
        )

    for tech in technicians:

        assigned_tickets = tickets.filter(
            Q(assigned_to=tech) |
            Q(additional_technicians=tech)
        ).distinct()

        assigned_total = assigned_tickets.count()

        current_assigned = assigned_tickets.exclude(
            status__in=["resolved", "cancelled"]
        ).count()

        primary_total = (
            TicketAssignmentLog.objects
            .filter(new_technician=tech, ticket__in=tickets)
            .count()
        )

        additional_total = (
            TicketAdditionalAssignmentLog.objects
            .filter(technician=tech, action="added", ticket__in=tickets)
            .count()
        )

        total_assigned = primary_total + additional_total

        open_count = assigned_tickets.filter(status="pending").count()
        progress_count = assigned_tickets.filter(status="progress").count()
        resolved_count = assigned_tickets.filter(status="resolved").count()

        resolved_on_time_tech = assigned_tickets.filter(
            status="resolved",
            resolve_at__isnull=False,
            deadline__isnull=False,
            resolve_at__lte=F("deadline")
        ).count()

        reopened = (
            TicketStatusLog.objects
            .filter(technician=tech, old_status="resolved", ticket__in=tickets)
            .values("ticket")
            .distinct()
            .count()
        )

        tech_overdue = assigned_tickets.filter(
            deadline__lt=timezone.now()
        ).exclude(
            status__in=["resolved", "cancelled"]
        ).count()

        resolved_tickets = assigned_tickets.filter(
            status="resolved",
            resolve_at__isnull=False,
            created_at__isnull=False
        )

        resolution_seconds = [
            (ticket.resolve_at - ticket.created_at).total_seconds()
            for ticket in resolved_tickets
        ]

        average_days = (
            sum(resolution_seconds) / len(resolution_seconds) / 86400
            if resolution_seconds else 0
        )

        resolution_rate = (
            (resolved_count / assigned_total) * 100
            if assigned_total else 0
        )

        department_name = (
            tech.department.name if tech.department else "—"
        )

        technician_stats.append({
            "id": tech.id,
            "name": tech.full_name,
            "department": department_name,
            "total": assigned_total,
            "current_assigned": current_assigned,
            "total_assigned": total_assigned,
            "open": open_count,
            "progress": progress_count,
            "resolved": resolved_count,
            "resolved_on_time": resolved_on_time_tech,
            "reopened": reopened,
        })

        technician_performance.append({
            "id": tech.id,
            "name": tech.full_name,
            "department": department_name,
            "average_days": round(average_days, 1),
            "overdue": tech_overdue,
            "resolution_rate": round(resolution_rate, 1),
            "resolved": resolved_count,
            "resolved_on_time": resolved_on_time_tech,
            "reopened": reopened,
        })

  
    # ============================================================
    # SORT TECHNICIAN CHART
    # ============================================================
    if chart_sort == "name":
        technician_stats.sort(
            key=lambda x: (x["name"] or "").lower()
        )

    elif chart_sort == "-name":
        technician_stats.sort(
            key=lambda x: (x["name"] or "").lower(),
            reverse=True
        )

    elif chart_sort == "total":
        technician_stats.sort(
            key=lambda x: x["total_assigned"]
        )

    elif chart_sort == "-total":
        technician_stats.sort(
            key=lambda x: x["total_assigned"],
            reverse=True
        )

    elif chart_sort == "open":
        technician_stats.sort(
            key=lambda x: x["open"]
        )

    elif chart_sort == "-open":
        technician_stats.sort(
            key=lambda x: x["open"],
            reverse=True
        )

    elif chart_sort == "progress":
        technician_stats.sort(
            key=lambda x: x["progress"]
        )

    elif chart_sort == "-progress":
        technician_stats.sort(
            key=lambda x: x["progress"],
            reverse=True
        )

    elif chart_sort == "resolved":
        technician_stats.sort(
            key=lambda x: x["resolved"]
        )

    elif chart_sort == "-resolved":
        technician_stats.sort(
            key=lambda x: x["resolved"],
            reverse=True
        )

    elif chart_sort == "reopened":
        technician_stats.sort(
            key=lambda x: x["reopened"]
        )

    elif chart_sort == "-reopened":
        technician_stats.sort(
            key=lambda x: x["reopened"],
            reverse=True
        )

        

    # ============================================================
    # TECHNICIAN SUMMARY SORT
    # ============================================================

    # ============================================================
    # TECHNICIAN SUMMARY
    # ============================================================

    technician_summary = []

    technicians = (
        Technician.objects
        .select_related("department")
        .all()
        .order_by("full_name")
    )

    if selected_department:
        technicians = technicians.filter(
            department__name=selected_department
        )

    for tech in technicians:

        # Tickets currently/previously assigned to this technician
        assigned_tickets = tickets.filter(
            Q(assigned_to=tech) |
            Q(additional_technicians=tech)
        ).distinct()

        # Current assigned = not resolved/cancelled
        current_assigned = assigned_tickets.exclude(
            status__in=["resolved", "cancelled"]
        ).count()

        # Total assigned from assignment logs
        primary_total = (
            TicketAssignmentLog.objects
            .filter(
                new_technician=tech,
                ticket__in=tickets
            )
            .count()
        )

        additional_total = (
            TicketAdditionalAssignmentLog.objects
            .filter(
                technician=tech,
                action="added",
                ticket__in=tickets
            )
            .count()
        )

        total_assigned = primary_total + additional_total

        # Resolved
        resolved = assigned_tickets.filter(
            status="resolved"
        ).count()

        # Resolved on time
        resolved_on_time = assigned_tickets.filter(
            status="resolved",
            resolve_at__isnull=False,
            deadline__isnull=False,
            resolve_at__lte=F("deadline")
        ).count()

        # Reopened
        reopened = (
            TicketStatusLog.objects
            .filter(
                technician=tech,
                old_status="resolved",
                ticket__in=tickets
            )
            .values("ticket")
            .distinct()
            .count()
        )

        technician_summary.append({
            "id": tech.id,
            "name": tech.full_name,
            "department": (
                tech.department.name
                if tech.department
                else "—"
            ),
            "current_assigned": current_assigned,
            "total_assigned": total_assigned,
            "resolved": resolved,
            "resolved_on_time": resolved_on_time,
            "reopened": reopened,
        })

    # ============================================================
    # SORT TECHNICIAN SUMMARY TABLE
    # ============================================================

    if technician_sort == "name":

        technician_summary.sort(
            key=lambda x: (x["name"] or "").lower()
        )

    elif technician_sort == "-name":

        technician_summary.sort(
            key=lambda x: (x["name"] or "").lower(),
            reverse=True
        )

    elif technician_sort == "current_assigned":

        technician_summary.sort(
            key=lambda x: x["current_assigned"]
        )

    elif technician_sort == "-current_assigned":

        technician_summary.sort(
            key=lambda x: x["current_assigned"],
            reverse=True
        )

    elif technician_sort == "total_assigned":

        technician_summary.sort(
            key=lambda x: x["total_assigned"]
        )

    elif technician_sort == "-total_assigned":

        technician_summary.sort(
            key=lambda x: x["total_assigned"],
            reverse=True
        )

    elif technician_sort == "resolved":

        technician_summary.sort(
            key=lambda x: x["resolved"]
        )

    elif technician_sort == "-resolved":

        technician_summary.sort(
            key=lambda x: x["resolved"],
            reverse=True
        )

    elif technician_sort == "resolved_on_time":

        technician_summary.sort(
            key=lambda x: x["resolved_on_time"]
        )

    elif technician_sort == "-resolved_on_time":

        technician_summary.sort(
            key=lambda x: x["resolved_on_time"],
            reverse=True
        )

    elif technician_sort == "reopened":

        technician_summary.sort(
            key=lambda x: x["reopened"]
        )

    elif technician_sort == "-reopened":

        technician_summary.sort(
            key=lambda x: x["reopened"],
            reverse=True
        )

    else:

        technician_summary.sort(
            key=lambda x: (x["name"] or "").lower()
        )

    # ============================================================
    # DEPARTMENTS
    # ============================================================

    departments = list(
        tickets
        .values(
            "department",
            "department__name"
        )
        .annotate(
            total=Count("id"),
            open=Count("id", filter=Q(status="pending")),
            progress=Count("id", filter=Q(status="progress")),
            resolved=Count("id", filter=Q(status="resolved")),
            cancelled=Count("id", filter=Q(status="cancelled")),
        )
    )

    if chart_sort == "name":
        departments.sort(
            key=lambda x: (x["department__name"] or "").lower()
        )

    elif chart_sort == "-name":
        departments.sort(
            key=lambda x: (x["department__name"] or "").lower(),
            reverse=True
        )

    elif chart_sort == "total":
        departments.sort(key=lambda x: x["total"])

    elif chart_sort == "-total":
        departments.sort(key=lambda x: x["total"], reverse=True)

    elif chart_sort == "open":
        departments.sort(key=lambda x: x["open"], reverse=True)

    elif chart_sort == "progress":
        departments.sort(key=lambda x: x["progress"], reverse=True)

    elif chart_sort == "resolved":
        departments.sort(key=lambda x: x["resolved"], reverse=True)

    # ============================================================
    # DEPARTMENT PERFORMANCE
    # ============================================================

    department_performance = []

    for department in departments:

        department_tickets = tickets.filter(
            department_id=department["department"]
        )

        resolved_tickets = department_tickets.filter(
            status="resolved",
            resolve_at__isnull=False,
            created_at__isnull=False
        )

        resolution_seconds = [
            (ticket.resolve_at - ticket.created_at).total_seconds()
            for ticket in resolved_tickets
        ]

        average_days = (
            sum(resolution_seconds) / len(resolution_seconds) / 86400
            if resolution_seconds else 0
        )

        department_overdue = department_tickets.filter(
            deadline__lt=timezone.now()
        ).exclude(
            status__in=["resolved", "cancelled"]
        ).count()

        total_count = department_tickets.count()
        resolved_count = department_tickets.filter(status="resolved").count()

        resolution_rate = (
            resolved_count / total_count * 100 if total_count else 0
        )

        department_performance.append({
            "name": department["department__name"],
            "average_days": round(average_days, 1),
            "overdue": department_overdue,
            "resolution_rate": round(resolution_rate, 1),
        })

    # ============================================================
    # CONCERNS
    # ============================================================

    concerns = list(
    tickets
    .values(
        "concern_type_id",
        "concern_type__name",
        "department__name"
    )
    .annotate(
        total=Count("id"),
        open=Count("id", filter=Q(status="pending")),
        progress=Count("id", filter=Q(status="progress")),
        resolved=Count("id", filter=Q(status="resolved")),
        cancelled=Count("id", filter=Q(status="cancelled")),
    )
)

    if chart_sort == "name":
        concerns.sort(
            key=lambda x: (x["concern_type__name"] or "").lower()
        )

    elif chart_sort == "-name":
        concerns.sort(
            key=lambda x: (x["concern_type__name"] or "").lower(),
            reverse=True
        )

    elif chart_sort == "total":
        concerns.sort(
            key=lambda x: x["total"]
        )

    elif chart_sort == "-total":
        concerns.sort(
            key=lambda x: x["total"],
            reverse=True
        )

    elif chart_sort == "pending":
        concerns.sort(
            key=lambda x: x["open"],
            reverse=True
        )

    elif chart_sort == "progress":
        concerns.sort(
            key=lambda x: x["progress"],
            reverse=True
        )

    elif chart_sort == "resolved":
        concerns.sort(
            key=lambda x: x["resolved"],
            reverse=True
        )

    # ============================================================
    # CONCERN PERFORMANCE
    # ============================================================

    concern_performance = []

    concern_ids = (
        tickets.values_list("concern_type_id", flat=True).distinct()
    )

    for concern_id in concern_ids:

        if not concern_id:
            continue

        concern = (
            ConcernType.objects
            .select_related("department")
            .filter(id=concern_id)
            .first()
        )

        if not concern:
            continue

        concern_tickets = tickets.filter(concern_type_id=concern_id)

        resolved_tickets = concern_tickets.filter(
            status="resolved",
            resolve_at__isnull=False,
            created_at__isnull=False
        )

        resolution_seconds = [
            (ticket.resolve_at - ticket.created_at).total_seconds()
            for ticket in resolved_tickets
        ]

        average_days = (
            sum(resolution_seconds) / len(resolution_seconds) / 86400
            if resolution_seconds else 0
        )

        concern_overdue = concern_tickets.filter(
            deadline__lt=timezone.now()
        ).exclude(
            status__in=["resolved", "cancelled"]
        ).count()

        total_count = concern_tickets.count()
        resolved_count = concern_tickets.filter(status="resolved").count()

        resolution_rate = (
            resolved_count / total_count * 100 if total_count else 0
        )

        concern_performance.append({
            "id": concern.id,
            "name": concern.name,
            "department_name": (
                concern.department.name if concern.department else "—"
            ),
            "average_days": round(average_days, 1),
            "overdue": concern_overdue,
            "resolution_rate": round(resolution_rate, 1),
        })

    concern_performance.sort(key=lambda x: x["name"].lower())

    # ============================================================
    # OUTLETS
    # ============================================================


    outlets = list(
    tickets
    .values(
        "outlet",
        "outlet__name"
    )
    .annotate(
        total=Count("id")
    )
)

    if chart_sort == "name":
        outlets.sort(
            key=lambda x: (x["outlet__name"] or "").lower()
        )

    elif chart_sort == "-name":
        outlets.sort(
            key=lambda x: (x["outlet__name"] or "").lower(),
            reverse=True
        )

    elif chart_sort == "total":
        outlets.sort(
            key=lambda x: x["total"]
        )

    elif chart_sort == "-total":
        outlets.sort(
            key=lambda x: x["total"],
            reverse=True
        )

    # ============================================================
    # OUTLET SUMMARY
    # ============================================================

    # ============================================================
    # OUTLET SUMMARY
    # ============================================================

    outlet_summary = (
        tickets
        .values("outlet__name")
        .annotate(
            total=Count("id"),
            pending=Count("id", filter=Q(status="pending")),
            progress=Count("id", filter=Q(status="progress")),
            resolved=Count("id", filter=Q(status="resolved")),
            cancelled=Count("id", filter=Q(status="cancelled")),
        )
    )

    if outlet_sort == "name":
        outlet_summary = outlet_summary.order_by(
            "outlet__name"
        )

    elif outlet_sort == "-name":
        outlet_summary = outlet_summary.order_by(
            "-outlet__name"
        )

    elif outlet_sort == "total":
        outlet_summary = outlet_summary.order_by("total")

    elif outlet_sort == "-total":
        outlet_summary = outlet_summary.order_by("-total")

    elif outlet_sort == "pending":
        outlet_summary = outlet_summary.order_by("pending")

    elif outlet_sort == "-pending":
        outlet_summary = outlet_summary.order_by("-pending")

    elif outlet_sort == "progress":
        outlet_summary = outlet_summary.order_by("progress")

    elif outlet_sort == "-progress":
        outlet_summary = outlet_summary.order_by("-progress")

    elif outlet_sort == "resolved":
        outlet_summary = outlet_summary.order_by("resolved")

    elif outlet_sort == "-resolved":
        outlet_summary = outlet_summary.order_by("-resolved")

    elif outlet_sort == "cancelled":
        outlet_summary = outlet_summary.order_by("cancelled")

    elif outlet_sort == "-cancelled":
        outlet_summary = outlet_summary.order_by("-cancelled")

    else:
        outlet_summary = outlet_summary.order_by(
            "outlet__name"
        )

    # ============================================================
    # CONCERNS PER OUTLET
    # ============================================================

    concerns_per_outlet = (
        tickets
        .values(
            "outlet__name",
            "concern_type__name"
        )
        .annotate(
            total=Count("id")
        )
    )

    if concerns_outlet_sort == "outlet":
        concerns_per_outlet = concerns_per_outlet.order_by(
            "outlet__name"
        )

    elif concerns_outlet_sort == "-outlet":
        concerns_per_outlet = concerns_per_outlet.order_by(
            "-outlet__name"
        )

    elif concerns_outlet_sort == "concern":
        concerns_per_outlet = concerns_per_outlet.order_by(
            "concern_type__name"
        )

    elif concerns_outlet_sort == "-concern":
        concerns_per_outlet = concerns_per_outlet.order_by(
            "-concern_type__name"
        )

    elif concerns_outlet_sort == "total":
        concerns_per_outlet = concerns_per_outlet.order_by(
            "total"
        )

    elif concerns_outlet_sort == "-total":
        concerns_per_outlet = concerns_per_outlet.order_by(
            "-total"
        )

    else:
        concerns_per_outlet = concerns_per_outlet.order_by(
            "outlet__name"
        )


    # ============================================================
    # DEPARTMENT SUMMARY  (clickable column sorting)
    # ============================================================

    department_summary = (
        tickets
        .values("department__name")
        .annotate(
            total=Count("id"),
            pending=Count("id", filter=Q(status="pending")),
            progress=Count("id", filter=Q(status="progress")),
            resolved=Count("id", filter=Q(status="resolved")),
            cancelled=Count("id", filter=Q(status="cancelled")),
        )
    )

    if sort == "department":
        department_summary = department_summary.order_by("department__name")

    elif sort == "-department":
        department_summary = department_summary.order_by("-department__name")

    elif sort == "total":
        department_summary = department_summary.order_by("total")

    elif sort == "-total":
        department_summary = department_summary.order_by("-total")

    elif sort == "pending":
        department_summary = department_summary.order_by("pending")

    elif sort == "-pending":
        department_summary = department_summary.order_by("-pending")

    elif sort == "progress":
        department_summary = department_summary.order_by("progress")

    elif sort == "-progress":
        department_summary = department_summary.order_by("-progress")

    elif sort == "resolved":
        department_summary = department_summary.order_by("resolved")

    elif sort == "-resolved":
        department_summary = department_summary.order_by("-resolved")

    elif sort == "cancelled":
        department_summary = department_summary.order_by("cancelled")

    elif sort == "-cancelled":
        department_summary = department_summary.order_by("-cancelled")

    else:
        department_summary = department_summary.order_by("department__name")

    # ============================================================
    # CONCERN SUMMARY  (built here so it can be sorted)
    # ============================================================

    # ============================================================
    # CONCERN SUMMARY
    # ============================================================

    concern_summary = (
        tickets
        .values(
            "concern_type__name",
            "department__name"
        )
        .annotate(
            total=Count("id"),
            pending=Count("id", filter=Q(status="pending")),
            progress=Count("id", filter=Q(status="progress")),
            resolved=Count("id", filter=Q(status="resolved")),
            cancelled=Count("id", filter=Q(status="cancelled")),
        )
    )

    if concern_sort == "name":
        concern_summary = concern_summary.order_by(
        "concern_type__name"
        )

    elif concern_sort == "-name":
        concern_summary = concern_summary.order_by(
            "-concern_type__name"
        )

    elif concern_sort == "department":
        concern_summary = concern_summary.order_by(
            "department__name"
        )

    elif concern_sort == "-department":
        concern_summary = concern_summary.order_by(
            "-department__name"
        )

    elif concern_sort == "total":
        concern_summary = concern_summary.order_by("total")

    elif concern_sort == "-total":
        concern_summary = concern_summary.order_by("-total")

    elif concern_sort == "pending":
        concern_summary = concern_summary.order_by("pending")

    elif concern_sort == "-pending":
        concern_summary = concern_summary.order_by("-pending")

    elif concern_sort == "progress":
        concern_summary = concern_summary.order_by("progress")

    elif concern_sort == "-progress":
        concern_summary = concern_summary.order_by("-progress")

    elif concern_sort == "resolved":
        concern_summary = concern_summary.order_by("resolved")

    elif concern_sort == "-resolved":
        concern_summary = concern_summary.order_by("-resolved")

    elif concern_sort == "cancelled":
        concern_summary = concern_summary.order_by("cancelled")

    elif concern_sort == "-cancelled":
        concern_summary = concern_summary.order_by("-cancelled")

    else:
        concern_summary = concern_summary.order_by(
            "concern_type__name"
        )

    # ============================================================
    # CONTEXT
    # ============================================================

    context = {

        "sort": sort,
        "chart_sort": chart_sort,
        "department_summary": department_summary,
        "concern_summary": concern_summary,
        "outlet_sort": outlet_sort,
        "technician_sort": technician_sort,
        "concerns_outlet_sort": concerns_outlet_sort,

        **report_common_context(request),

        "context_departments": Department.objects.all().order_by("name"),
        "context_concerns": ConcernType.objects.all().order_by("name"),
        "selected_concern": request.GET.get("concern", ""),

        "tickets": tickets.order_by("-created_at"),
        "total": total,
        "pending": pending,
        "progress": progress,
        "resolved": resolved,
        "cancelled": cancelled,
        "overdue": overdue,
        "resolved_on_time": resolved_on_time,
        "reopened_total": reopened_total,

        "technician_stats": technician_stats,
        "technician_performance": technician_performance,
        "technician_summary": technician_summary,
        "technician_count": len(technician_stats),

        "departments": departments,
        "department_performance": department_performance,

        "concerns": concerns,
        "concern_performance": concern_performance,

        "outlets": outlets,
        "outlet_summary": outlet_summary,
        "concerns_per_outlet": concerns_per_outlet,
    }

   # ============================================================
    # AJAX SORT RESPONSE
    # ============================================================

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":

        # -------------------------
        # CONCERN SUMMARY
        # -------------------------

        if "concern_sort" in request.GET:

            html = render_to_string(
                "reports/partials/concern_rows.html",
                {
                    "concern_summary": concern_summary,
                },
                request=request,
            )

            return JsonResponse({
                "table": "concern",
                "html": html,
            })

        # -------------------------
        # DEPARTMENT SUMMARY
        # -------------------------

        if "sort" in request.GET:

            html = render_to_string(
                "reports/partials/department_rows.html",
                {
                    "department_summary": department_summary,
                },
                request=request,
            )

            return JsonResponse({
                "table": "department",
                "html": html,
            })

        # -------------------------
        # OUTLET SUMMARY
        # -------------------------

        if "outlet_sort" in request.GET:

            html = render_to_string(
                "reports/partials/outlet_rows.html",
                {
                    "outlet_summary": outlet_summary,
                },
                request=request,
            )

            return JsonResponse({
                "table": "outlet",
                "html": html,
            })
        # -------------------------
        # TECHNICIAN SUMMARY
        # -------------------------

        if "technician_sort" in request.GET:

            html = render_to_string(
                "reports/partials/technician_rows.html",
                {
                    "technician_summary": technician_summary,
                },
                request=request,
            )

            return JsonResponse({
                "table": "technician",
                "html": html,
            })

        # -------------------------
        # CONCERNS BY OUTLET
        # -------------------------

        if "concerns_outlet_sort" in request.GET:

            html = render_to_string(
                "reports/partials/concerns_outlet_rows.html",
                {
                    "concerns_per_outlet": concerns_per_outlet,
                },
                request=request,
            )

            return JsonResponse({
                "table": "concerns_outlet",
                "html": html,
            })


    # ============================================================
    # NORMAL PAGE RESPONSE
    # ============================================================

    return render(
        request,
        "reports/reports.html",
        context
    )


# ============================================================
# TICKETS
# ============================================================

def report_tickets(request):
    tickets = get_filtered_tickets(request)

    # ============================================================
    # TICKET SORTING
    # ============================================================

    sort = request.GET.get("sort", "-created_at").strip()

    allowed_sorts = {
        "outlet": "outlet__name",
        "-outlet": "-outlet__name",

        "created": "created_at",
        "-created": "-created_at",

        "department": "department__name",
        "-department": "-department__name",

        "concern": "concern_type__name",
        "-concern": "-concern_type__name",

        "message": "message",
        "-message": "-message",
    }

    # Prevent invalid sort values
    order_by = allowed_sorts.get(sort, "-created_at")

    tickets = tickets.order_by(order_by)

    context = {
        **report_common_context(request),

        "tickets": tickets,
        "total": tickets.count(),

        "report_departments": Department.objects.all().order_by("name"),

        # Keep selected sort for the template
        "selected_sort": sort,
    }

    return render(request, "reports/tickets.html", context)


# ============================================================
# OUTLETS
# ============================================================

# ============================================================
# OUTLETS
# ============================================================

def report_outlets(request):

    tickets = get_filtered_tickets(request)
    sort = request.GET.get("sort", "-total").strip()

    # ========================================================
    # OUTLET SUMMARY
    # ========================================================

    outlet_summary = (
    tickets
    .values("outlet__name")
    .annotate(
        total=Count("id"),
        pending=Count("id", filter=Q(status="pending")),
        progress=Count("id", filter=Q(status="progress")),
        resolved=Count("id", filter=Q(status="resolved")),
        cancelled=Count("id", filter=Q(status="cancelled")),
    )
    )

    if sort == "name":
        outlet_summary = outlet_summary.order_by("outlet__name")

    elif sort == "-name":
        outlet_summary = outlet_summary.order_by("-outlet__name")

    elif sort == "total":
        outlet_summary = outlet_summary.order_by("total")

    elif sort == "-total":
        outlet_summary = outlet_summary.order_by("-total")

    elif sort == "pending":
        outlet_summary = outlet_summary.order_by("-pending")

    elif sort == "progress":
        outlet_summary = outlet_summary.order_by("-progress")

    elif sort == "resolved":
        outlet_summary = outlet_summary.order_by("-resolved")

    elif sort == "cancelled":
        outlet_summary = outlet_summary.order_by("-cancelled")

    # ========================================================
    # CONCERNS PER OUTLET
    # ========================================================

   # ============================================================
    # CONCERNS PER OUTLET
    # ============================================================

    concern_outlet_sort = request.GET.get(
        "concern_outlet_sort",
        "outlet"
    ).strip()

    concern_outlet_sort_options = {
        "outlet": "outlet__name",
        "-outlet": "-outlet__name",

        "concern": "concern_type__name",
        "-concern": "-concern_type__name",

        "total": "total",
        "-total": "-total",
    }

    concern_outlet_order = concern_outlet_sort_options.get(
        concern_outlet_sort,
        "outlet__name"
    )

    concerns_per_outlet = (
        tickets
        .values(
            "outlet__name",
            "concern_type__name"
        )
        .annotate(
            total=Count("id")
        )
        .order_by(
            concern_outlet_order
        )
    )

    # ========================================================
    # CONTEXT
    # ========================================================

    context = {

        **report_common_context(request),

        "sort": sort,

        "outlet_summary":
            outlet_summary,

        "concerns_per_outlet":
            concerns_per_outlet,

        "context_concerns_per_outlet": concerns_per_outlet,
        "concern_outlet_sort": concern_outlet_sort,

        "total":
            tickets.count(),
    }

    return render(
        request,
        "reports/outlets.html",
        context
    )


# ============================================================
# DEPARTMENTS
# ============================================================

def report_departments(request):

    tickets = get_filtered_tickets(request)
    sort = request.GET.get("sort", "-total").strip() 

    departments = (
        tickets
        .values(
            "department",
            "department__name"
        )
        .annotate(
            total=Count("id"),
            open=Count("id", filter=Q(status="pending")),
            progress=Count("id", filter=Q(status="progress")),
            resolved=Count("id", filter=Q(status="resolved")),
        )
    )

    if sort == "name":
        departments = departments.order_by("department__name")

    elif sort == "-name":
        departments = departments.order_by("-department__name")

    elif sort == "total":
        departments = departments.order_by("total")

    elif sort == "-total":
        departments = departments.order_by("-total")

    elif sort == "open":
        departments = departments.order_by("open")

    elif sort == "-open":
        departments = departments.order_by("-open")

    elif sort == "progress":
        departments = departments.order_by("progress")

    elif sort == "-progress":
        departments = departments.order_by("-progress")

    elif sort == "resolved":
        departments = departments.order_by("resolved")

    elif sort == "-resolved":
        departments = departments.order_by("-resolved")

    else:
        departments = departments.order_by("department__name")

    # ========================================================
    # DEPARTMENT PERFORMANCE
    # ========================================================

    department_performance = []

    for department in departments:

        department_name = department["department__name"]

        department_tickets = tickets.filter(
            department_id=department["department"]
        )

        # ----------------------------------------------------
        # RESOLVED TICKETS
        # ----------------------------------------------------

        resolved_tickets = department_tickets.filter(
            status="resolved",
            resolve_at__isnull=False,
            created_at__isnull=False
        )

        # ----------------------------------------------------
        # AVERAGE RESOLUTION TIME
        # ----------------------------------------------------

        resolution_times = []

        for ticket in resolved_tickets:

            if ticket.resolve_at and ticket.created_at:

                duration = (
                    ticket.resolve_at -
                    ticket.created_at
                ).total_seconds()

                resolution_times.append(duration)

        if resolution_times:

            average_seconds = (
                sum(resolution_times) /
                len(resolution_times)
            )

            average_days = average_seconds / 86400

        else:

            average_days = 0

        # ----------------------------------------------------
        # OVERDUE
        # ----------------------------------------------------

        overdue = department_tickets.filter(
            deadline__lt=timezone.now()
        ).exclude(
            status__in=[
                "resolved",
                "cancelled"
            ]
        ).count()

        # ----------------------------------------------------
        # RESOLUTION RATE
        # ----------------------------------------------------

        total_count = department_tickets.count()

        resolved_count = department_tickets.filter(
            status="resolved"
        ).count()

        if total_count:

            resolution_rate = (
                resolved_count /
                total_count
            ) * 100

        else:

            resolution_rate = 0

        # ----------------------------------------------------
        # ADD TO PERFORMANCE
        # ----------------------------------------------------

        department_performance.append({

            "name":
                department_name,

            "average_days":
                round(average_days, 1),

            "overdue":
                overdue,

            "resolution_rate":
                round(resolution_rate, 1),

        })

    # ========================================================
    # CONTEXT
    # ========================================================

    context = {

        **report_common_context(request),

        "sort": sort,

        "departments":
            departments,

        "department_performance":
            department_performance,
    }

    return render(
        request,
        "reports/departments.html",
        context
    )


# ============================================================
# TECHNICIANS
# ============================================================

def report_technicians(request):

    tickets = get_filtered_tickets(request)

    # ========================================================
    # FILTER
    # ========================================================

    department = request.GET.get(
        "department",
        ""
    ).strip()

    sort = request.GET.get("sort", "-total").strip()

    performance_sort = request.GET.get(
        "performance_sort",
        "name"
    ).strip()

    # IMPORTANT:
    # Get ALL technicians first.
    # This means technicians will still appear even
    # if they currently have zero tickets.
    technicians = (
        Technician.objects
        .select_related("department")
        .all()
        .order_by("full_name")
    )

    # Filter technicians only when a department
    # was actually selected.
    if department:

        technicians = technicians.filter(
            department__name=department
        )

    # ========================================================
    # DATA
    # ========================================================

    technician_stats = []
    technician_performance = []

    for tech in technicians:

        # ====================================================
        # ASSIGNED TICKETS
        # ====================================================

        assigned_tickets = tickets.filter(
            Q(assigned_to=tech) |
            Q(additional_technicians=tech)
        ).distinct()

        # ====================================================
        # CURRENT WORKLOAD
        # ====================================================

        current_assigned = assigned_tickets.exclude(
            status__in=[
                "resolved",
                "cancelled",
            ]
        ).count()

        # ====================================================
        # TOTAL PRIMARY ASSIGNMENTS
        # ====================================================

        primary_total = (
            TicketAssignmentLog.objects
            .filter(
                new_technician=tech,
                ticket__in=tickets,
            )
            .count()
        )

        # ====================================================
        # TOTAL ADDITIONAL ASSIGNMENTS
        # ====================================================

        additional_total = (
            TicketAdditionalAssignmentLog.objects
            .filter(
                technician=tech,
                action="added",
                ticket__in=tickets,
            )
            .count()
        )

        # ====================================================
        # TOTAL ASSIGNED
        # ====================================================

        total_assigned = (
            primary_total +
            additional_total
        )

        # ====================================================
        # OPEN
        # ====================================================

        open_count = assigned_tickets.filter(
            status="pending"
        ).count()

        # ====================================================
        # IN PROGRESS
        # ====================================================

        progress_count = assigned_tickets.filter(
            status="progress"
        ).count()

        # ====================================================
        # RESOLVED
        # ====================================================

        resolved_count = assigned_tickets.filter(
            status="resolved"
        ).count()

        # ====================================================
        # RESOLVED ON TIME
        # ====================================================

        resolved_on_time = assigned_tickets.filter(
            status="resolved",
            resolve_at__isnull=False,
            deadline__isnull=False,
            resolve_at__lte=F("deadline"),
        ).count()

        # ====================================================
        # REOPENED
        # ====================================================

        reopened = (
            TicketStatusLog.objects
            .filter(
                technician=tech,
                old_status="resolved",
                ticket__in=tickets,
            )
            .values("ticket")
            .distinct()
            .count()
        )

        # ====================================================
        # OVERDUE
        # ====================================================

        overdue = assigned_tickets.filter(
            deadline__lt=timezone.now()
        ).exclude(
            status__in=[
                "resolved",
                "cancelled",
            ]
        ).count()

        # ====================================================
        # AVERAGE RESOLUTION TIME
        # ====================================================

        resolved_tickets = assigned_tickets.filter(
            status="resolved",
            resolve_at__isnull=False,
            created_at__isnull=False,
        )

        resolution_seconds = []

        for ticket in resolved_tickets:

            if ticket.resolve_at and ticket.created_at:

                duration = (
                    ticket.resolve_at -
                    ticket.created_at
                ).total_seconds()

                resolution_seconds.append(duration)

        if resolution_seconds:

            average_seconds = (
                sum(resolution_seconds) /
                len(resolution_seconds)
            )

            average_days = (
                average_seconds /
                86400
            )

        else:

            average_days = 0

        # ====================================================
        # RESOLUTION RATE
        # ====================================================

        assigned_total = assigned_tickets.count()

        if assigned_total > 0:

            resolution_rate = (
                resolved_count /
                assigned_total
            ) * 100

        else:

            resolution_rate = 0

        # ====================================================
        # TABLE 1
        # TECHNICIAN WORKLOAD
        # ====================================================

        technician_stats.append({

            "id":
                tech.id,

            "name":
                tech.full_name,

            "department":
                tech.department.name
                if tech.department
                else "—",

            # This is the Total shown in the table.
            "total":
                assigned_total,

            "current_assigned":
                current_assigned,

            # Assignment-log total.
            # Kept separately because this is
            # a different metric.
            "total_assigned":
                total_assigned,

            "open":
                open_count,

            "progress":
                progress_count,

            "resolved":
                resolved_count,

        })

        # ====================================================
        # TABLE 2
        # TECHNICIAN PERFORMANCE
        # ====================================================

        technician_performance.append({

            "id":
                tech.id,

            "name":
                tech.full_name,

            "department":
                tech.department.name
                if tech.department
                else "—",

            "average_days":
                round(
                    average_days,
                    1
                ),

            "overdue":
                overdue,

            "resolution_rate":
                round(
                    resolution_rate,
                    1
                ),

            "resolved":
                resolved_count,

            "resolved_on_time":
                resolved_on_time,

            "reopened":
                reopened,

        })

    # ========================================================
    # SORT — TECHNICIAN WORKLOAD
    # ========================================================

    technician_stats_sort_map = {

        "name":
            lambda x: x["name"].lower(),

        "-name":
            lambda x: x["name"].lower(),

        "department":
            lambda x: x["department"].lower(),

        "-department":
            lambda x: x["department"].lower(),

        "total":
            lambda x: x["total"],

        "-total":
            lambda x: x["total"],

        "current":
            lambda x: x["current_assigned"],

        "-current":
            lambda x: x["current_assigned"],

        "open":
            lambda x: x["open"],

        "-open":
            lambda x: x["open"],

        "progress":
            lambda x: x["progress"],

        "-progress":
            lambda x: x["progress"],

        "resolved":
            lambda x: x["resolved"],

        "-resolved":
            lambda x: x["resolved"],
    }

    if sort in technician_stats_sort_map:

        technician_stats.sort(
            key=technician_stats_sort_map[sort],
            reverse=sort.startswith("-")
        )

    # ========================================================
    # SORT — TECHNICIAN PERFORMANCE
    # ========================================================

    technician_performance_sort_map = {

        "name":
            lambda x: x["name"].lower(),

        "-name":
            lambda x: x["name"].lower(),

        "department":
            lambda x: x["department"].lower(),

        "-department":
            lambda x: x["department"].lower(),

        "days":
            lambda x: x["average_days"],

        "-days":
            lambda x: x["average_days"],

        "overdue":
            lambda x: x["overdue"],

        "-overdue":
            lambda x: x["overdue"],

        "rate":
            lambda x: x["resolution_rate"],

        "-rate":
            lambda x: x["resolution_rate"],

        "resolved":
            lambda x: x["resolved"],

        "-resolved":
            lambda x: x["resolved"],

        "ontime":
            lambda x: x["resolved_on_time"],

        "-ontime":
            lambda x: x["resolved_on_time"],

        "reopened":
            lambda x: x["reopened"],

        "-reopened":
            lambda x: x["reopened"],
    }

    if performance_sort in technician_performance_sort_map:

        technician_performance.sort(
            key=technician_performance_sort_map[
                performance_sort
            ],
            reverse=performance_sort.startswith("-")
        )

    # ========================================================
    # CONTEXT
    # ========================================================

    context = {

        **report_common_context(request),

        "sort":
            sort,

        "performance_sort":
            performance_sort,

        # TABLE 1
        "technician_stats":
            technician_stats,

        # TABLE 2
        "technician_performance":
            technician_performance,

        # Useful totals
        "technician_count":
            len(technician_stats),

        "total_technicians":
            technicians.count(),
    }

    return render(
        request,
        "reports/technicians.html",
        context
    )
# ============================================================
# CONCERNS
# ============================================================

def report_concerns(request):

    # =====================================================
    # FILTER VALUES
    # =====================================================

    selected_start = request.GET.get("start", "").strip()
    selected_end = request.GET.get("end", "").strip()
    selected_department = request.GET.get("department", "").strip()
    selected_outlet = request.GET.get("outlet", "").strip()
    selected_concern = request.GET.get("concern", "").strip()


    # =====================================================
    # BASE QUERY
    # =====================================================

    tickets = Ticket.objects.all()


    # =====================================================
    # DATE FILTER
    # =====================================================

    if selected_start:

        try:

            start_date = datetime.strptime(
                selected_start,
                "%Y-%m-%d"
            ).date()

            tickets = tickets.filter(
                created_at__date__gte=start_date
            )

        except ValueError:

            pass


    if selected_end:

        try:

            end_date = datetime.strptime(
                selected_end,
                "%Y-%m-%d"
            ).date()

            tickets = tickets.filter(
                created_at__date__lte=end_date
            )

        except ValueError:

            pass


    # =====================================================
    # DEPARTMENT FILTER
    # =====================================================

    if selected_department:

        tickets = tickets.filter(
            department__name=selected_department
        )


    # =====================================================
    # OUTLET FILTER
    # =====================================================

    if selected_outlet:

        tickets = tickets.filter(
            outlet_id=selected_outlet
        )


    # =====================================================
    # CONCERN FILTER
    # =====================================================

    if selected_concern:

        tickets = tickets.filter(
            concern_type_id=selected_concern
        )


    # =====================================================
    # TABLE 1 — CONCERN SUMMARY
    # =====================================================

    concerns = (
        tickets
        .values(
            "concern_type_id",
            "concern_type__name",
            "department__name",
        )
        .annotate(
            total=Count("id"),

            open=Count(
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
        )
        .order_by(
            "concern_type__name"
        )
    )


    # =====================================================
    # CONVERT FIELD NAMES FOR TEMPLATE
    # =====================================================

    concern_rows = []

    for row in concerns:

        concern_rows.append({
            "id": row["concern_type_id"],
            "name": row["concern_type__name"],
            "department_name": row["department__name"],

            "total": row["total"],
            "open": row["open"],
            "progress": row["progress"],
            "resolved": row["resolved"],
        })


    # =====================================================
    # TABLE 2 — CONCERN PERFORMANCE
    # =====================================================

    concern_performance = []


    concern_ids = (
        tickets
        .values_list(
            "concern_type_id",
            flat=True
        )
        .distinct()
    )


    for concern_id in concern_ids:

        if not concern_id:
            continue


        concern_tickets = tickets.filter(
            concern_type_id=concern_id
        )


        resolved_tickets = concern_tickets.filter(
            status="resolved",
            resolve_at__isnull=False,
            created_at__isnull=False,
        )


        # =================================================
        # RESOLUTION TIME
        # =================================================

        resolution_seconds = []


        for ticket in resolved_tickets:

            if ticket.resolve_at and ticket.created_at:

                duration = (
                    ticket.resolve_at -
                    ticket.created_at
                )

                resolution_seconds.append(
                    duration.total_seconds()
                )


        if resolution_seconds:

            average_seconds = (
                sum(resolution_seconds)
                / len(resolution_seconds)
            )

            average_days = round(
                average_seconds / 86400,
                1
            )

        else:

            average_days = 0


        # =================================================
        # OVERDUE
        #
        # IMPORTANT:
        # Use F("deadline"), not Q("deadline")
        # =================================================

        overdue = concern_tickets.filter(
            deadline__isnull=False,
            resolve_at__isnull=False,
            resolve_at__lte=F("deadline"),
            status="resolved",
        ).count()


        # =================================================
        # RESOLUTION RATE
        # =================================================

        total_count = concern_tickets.count()

        resolved_count = resolved_tickets.count()


        if total_count > 0:

            resolution_rate = round(
                (resolved_count / total_count) * 100,
                1
            )

        else:

            resolution_rate = 0


        # =================================================
        # CONCERN OBJECT
        # =================================================

        concern = ConcernType.objects.filter(
            id=concern_id
        ).select_related(
            "department"
        ).first()


        if not concern:
            continue


        concern_performance.append({

            "id": concern.id,

            "name": concern.name,

            "department_name": (
                concern.department.name
                if getattr(concern, "department", None)
                else "—"
            ),

            "average_days": average_days,

            "overdue": overdue,

            "resolution_rate": resolution_rate,

        })


    # =====================================================
    # SORT VALUES
    # =====================================================

    sort = request.GET.get(
    "sort",
    "-total"
    ).strip()

    performance_sort = request.GET.get(
    "performance_sort",
    "days"
    ).strip()


    # =====================================================
    # SORT TABLE 1 — CONCERN SUMMARY
    # =====================================================

    concern_sort_map = {
        "name": lambda x: x["name"].lower(),
        "-name": lambda x: x["name"].lower(),

        "department": lambda x: x["department_name"].lower(),
        "-department": lambda x: x["department_name"].lower(),

        "total": lambda x: x["total"],
        "-total": lambda x: x["total"],

        "open": lambda x: x["open"],
        "-open": lambda x: x["open"],

        "progress": lambda x: x["progress"],
        "-progress": lambda x: x["progress"],

        "resolved": lambda x: x["resolved"],
        "-resolved": lambda x: x["resolved"],
    }


    if sort in concern_sort_map:

        concern_rows.sort(
            key=concern_sort_map[sort],
            reverse=sort.startswith("-")
        )


    # =====================================================
    # SORT TABLE 2 — CONCERN PERFORMANCE
    # =====================================================

    performance_sort_map = {
        "name": lambda x: x["name"].lower(),
        "-name": lambda x: x["name"].lower(),

        "department": lambda x: x["department_name"].lower(),
        "-department": lambda x: x["department_name"].lower(),

        "days": lambda x: x["average_days"],
        "-days": lambda x: x["average_days"],

        "overdue": lambda x: x["overdue"],
        "-overdue": lambda x: x["overdue"],

        "rate": lambda x: x["resolution_rate"],
        "-rate": lambda x: x["resolution_rate"],
    }


    if performance_sort in performance_sort_map:

        concern_performance.sort(
            key=performance_sort_map[performance_sort],
            reverse=performance_sort.startswith("-")
        )


    # =====================================================
    # CONTEXT
    # =====================================================

    context = {

        "concerns": concern_rows,

        "concern_performance":
            concern_performance,

        "context_outlets":
            Outlet.objects.all().order_by("name"),

        "context_departments":
            Department.objects.all().order_by("name"),

        "context_concerns":
            ConcernType.objects.all().order_by("name"),

        "selected_start":
            selected_start,

        "selected_end":
            selected_end,

        "selected_department":
            selected_department,

        "selected_outlet":
            selected_outlet,

        "selected_concern":
            selected_concern,

        "sort": sort,

        "performance_sort":
            performance_sort,
    }


    return render(
        request,
        "reports/concerns.html",
        context
    )