from datetime import datetime, timedelta

from django.shortcuts import render
from django.http import HttpResponse
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
    concern = request.GET.get("concern", "").strip()
    status = request.GET.get("status", "").strip()

    # ========================================================
    # DATE
    # ========================================================

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

    # ========================================================
    # DEPARTMENT
    # ========================================================

    if department:

        tickets = tickets.filter(
            department__name=department
        )

    # ========================================================
    # OUTLET
    # ========================================================

    if outlet:

        tickets = tickets.filter(
            outlet_id=outlet
        )

    # ========================================================
    # CONCERN TYPE
    # ========================================================

    if concern:

        tickets = tickets.filter(
            concern_type_id=concern
        )

    # ========================================================
    # STATUS
    # ========================================================

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

        # ----------------------------------------------------
        # SELECTED FILTERS
        # ----------------------------------------------------

        "selected_start":
            request.GET.get("start", "").strip(),

        "selected_end":
            request.GET.get("end", "").strip(),

        "selected_department":
            request.GET.get("department", "").strip(),

        "selected_outlet":
            request.GET.get("outlet", "").strip(),

        "selected_concern":
            request.GET.get("concern", "").strip(),

        "selected_status":
            request.GET.get("status", "").strip(),
    }


# ============================================================
# DASHBOARD
# ============================================================

def reports(request):

    tickets = get_filtered_tickets(request)

    # ============================================================
    # BASIC COUNTS
    # ============================================================

    total = tickets.count()

    pending = tickets.filter(
        status="pending"
    ).count()

    progress = tickets.filter(
        status="progress"
    ).count()

    resolved = tickets.filter(
        status="resolved"
    ).count()

    cancelled = tickets.filter(
        status="cancelled"
    ).count()

    # ============================================================
    # OVERDUE
    # ============================================================

    overdue = tickets.filter(
        deadline__lt=timezone.now()
    ).exclude(
        status__in=[
            "resolved",
            "cancelled"
        ]
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
        .filter(
            old_status="resolved",
            ticket__in=tickets
        )
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

    selected_department = request.GET.get(
        "department",
        ""
    ).strip()

    if selected_department:

        technicians = technicians.filter(
            department__name=selected_department
        )

    for tech in technicians:

        # ========================================================
        # ASSIGNED TICKETS
        # ========================================================

        assigned_tickets = tickets.filter(
            Q(assigned_to=tech) |
            Q(additional_technicians=tech)
        ).distinct()

        assigned_total = assigned_tickets.count()

        # ========================================================
        # CURRENT WORKLOAD
        # ========================================================

        current_assigned = assigned_tickets.exclude(
            status__in=[
                "resolved",
                "cancelled"
            ]
        ).count()

        # ========================================================
        # PRIMARY ASSIGNMENTS
        # ========================================================

        primary_total = (
            TicketAssignmentLog.objects
            .filter(
                new_technician=tech,
                ticket__in=tickets
            )
            .count()
        )

        # ========================================================
        # ADDITIONAL ASSIGNMENTS
        # ========================================================

        additional_total = (
            TicketAdditionalAssignmentLog.objects
            .filter(
                technician=tech,
                action="added",
                ticket__in=tickets
            )
            .count()
        )

        total_assigned = (
            primary_total +
            additional_total
        )

        # ========================================================
        # STATUS
        # ========================================================

        open_count = assigned_tickets.filter(
            status="pending"
        ).count()

        progress_count = assigned_tickets.filter(
            status="progress"
        ).count()

        resolved_count = assigned_tickets.filter(
            status="resolved"
        ).count()

        # ========================================================
        # RESOLVED ON TIME
        # ========================================================

        resolved_on_time_tech = assigned_tickets.filter(
            status="resolved",
            resolve_at__isnull=False,
            deadline__isnull=False,
            resolve_at__lte=F("deadline")
        ).count()

        # ========================================================
        # REOPENED
        # ========================================================

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

        # ========================================================
        # OVERDUE
        # ========================================================

        tech_overdue = assigned_tickets.filter(
            deadline__lt=timezone.now()
        ).exclude(
            status__in=[
                "resolved",
                "cancelled"
            ]
        ).count()

        # ========================================================
        # AVERAGE RESOLUTION TIME
        # ========================================================

        resolved_tickets = assigned_tickets.filter(
            status="resolved",
            resolve_at__isnull=False,
            created_at__isnull=False
        )

        resolution_seconds = []

        for ticket in resolved_tickets:

            duration = (
                ticket.resolve_at -
                ticket.created_at
            ).total_seconds()

            resolution_seconds.append(
                duration
            )

        if resolution_seconds:

            average_days = (
                sum(resolution_seconds)
                / len(resolution_seconds)
                / 86400
            )

        else:

            average_days = 0

        # ========================================================
        # RESOLUTION RATE
        # ========================================================

        if assigned_total:

            resolution_rate = (
                resolved_count /
                assigned_total
            ) * 100

        else:

            resolution_rate = 0

        department_name = (
            tech.department.name
            if tech.department
            else "—"
        )

        # ========================================================
        # TABLE 1
        # ========================================================

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

        # ========================================================
        # TABLE 2
        # ========================================================

        technician_performance.append({

            "id":
                tech.id,

            "name":
                tech.full_name,

            "department":
                department_name,

            "average_days":
                round(
                    average_days,
                    1
                ),

            "overdue":
                tech_overdue,

            "resolution_rate":
                round(
                    resolution_rate,
                    1
                ),

            "resolved":
                resolved_count,

            "resolved_on_time":
                resolved_on_time_tech,

            "reopened":
                reopened,
        })

    # ============================================================
    # DEPARTMENTS
    # ============================================================

    departments = (
        tickets
        .values(
            "department",
            "department__name"
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

            cancelled=Count(
                "id",
                filter=Q(status="cancelled")
            ),
        )
        .order_by(
            "department__name"
        )
    )

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

        resolution_seconds = []

        for ticket in resolved_tickets:

            duration = (
                ticket.resolve_at -
                ticket.created_at
            ).total_seconds()

            resolution_seconds.append(
                duration
            )

        if resolution_seconds:

            average_days = (
                sum(resolution_seconds)
                / len(resolution_seconds)
                / 86400
            )

        else:

            average_days = 0

        department_overdue = department_tickets.filter(
            deadline__lt=timezone.now()
        ).exclude(
            status__in=[
                "resolved",
                "cancelled"
            ]
        ).count()

        total_count = department_tickets.count()

        resolved_count = department_tickets.filter(
            status="resolved"
        ).count()

        resolution_rate = (
            resolved_count /
            total_count *
            100
            if total_count
            else 0
        )

        department_performance.append({

            "name":
                department["department__name"],

            "average_days":
                round(
                    average_days,
                    1
                ),

            "overdue":
                department_overdue,

            "resolution_rate":
                round(
                    resolution_rate,
                    1
                ),
        })

    # ============================================================
    # CONCERNS
    # ============================================================

    concerns = (
        tickets
        .values(
            "concern_type_id",
            "concern_type__name",
            "department__name"
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

            cancelled=Count(
                "id",
                filter=Q(status="cancelled")
            ),
        )
        .order_by(
            "concern_type__name"
        )
    )

    # ============================================================
    # CONCERN PERFORMANCE
    # ============================================================

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

        concern = (
            ConcernType.objects
            .select_related("department")
            .filter(id=concern_id)
            .first()
        )

        if not concern:
            continue

        concern_tickets = tickets.filter(
            concern_type_id=concern_id
        )

        resolved_tickets = concern_tickets.filter(
            status="resolved",
            resolve_at__isnull=False,
            created_at__isnull=False
        )

        resolution_seconds = []

        for ticket in resolved_tickets:

            duration = (
                ticket.resolve_at -
                ticket.created_at
            ).total_seconds()

            resolution_seconds.append(
                duration
            )

        if resolution_seconds:

            average_days = (
                sum(resolution_seconds)
                / len(resolution_seconds)
                / 86400
            )

        else:

            average_days = 0

        # Active overdue tickets
        concern_overdue = concern_tickets.filter(
            deadline__lt=timezone.now()
        ).exclude(
            status__in=[
                "resolved",
                "cancelled"
            ]
        ).count()

        total_count = concern_tickets.count()

        resolved_count = concern_tickets.filter(
            status="resolved"
        ).count()

        resolution_rate = (
            resolved_count /
            total_count *
            100
            if total_count
            else 0
        )

        concern_performance.append({

            "id":
                concern.id,

            "name":
                concern.name,

            "department_name":
                (
                    concern.department.name
                    if concern.department
                    else "—"
                ),

            "average_days":
                round(
                    average_days,
                    1
                ),

            "overdue":
                concern_overdue,

            "resolution_rate":
                round(
                    resolution_rate,
                    1
                ),

        })

    concern_performance.sort(
        key=lambda x: x["name"].lower()
    )

    # ============================================================
    # OUTLETS
    # ============================================================

    outlets = (
        tickets
        .values(
            "outlet",
            "outlet__name"
        )
        .annotate(
            total=Count("id")
        )
        .order_by("-total")
    )

    # ============================================================
    # OUTLET SUMMARY
    # ============================================================

    outlet_summary = (
        tickets
        .values(
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
        .order_by(
            "outlet__name"
        )
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
        .order_by(
            "outlet__name",
            "-total"
        )
    )

    # ============================================================
    # CONTEXT
    # ============================================================

    context = {

        # --------------------------------------------------------
        # FILTERS
        # --------------------------------------------------------
        "department_summary":
        tickets
        .values(
            "department__name"
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
        .order_by("department__name"),


    "concern_summary":
        tickets
        .values(
            "concern_type__name",
            "department__name"
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
        .order_by(
            "concern_type__name"
        ),

        **report_common_context(request),

        "context_departments":
            Department.objects.all().order_by("name"),

        "context_concerns":
            ConcernType.objects.all().order_by("name"),

        "selected_concern":
            request.GET.get(
                "concern",
                ""
            ),

        # --------------------------------------------------------
        # MAIN COUNTERS
        # --------------------------------------------------------

        "tickets":
            tickets.order_by("-created_at"),

        "total":
            total,

        "pending":
            pending,

        "progress":
            progress,

        "resolved":
            resolved,

        "cancelled":
            cancelled,

        "overdue":
            overdue,

        "resolved_on_time":
            resolved_on_time,

        "reopened_total":
            reopened_total,

        # --------------------------------------------------------
        # TECHNICIANS
        # --------------------------------------------------------

        "technician_stats":
            technician_stats,

        "technician_performance":
            technician_performance,

        "technician_count":
            len(technician_stats),

        # --------------------------------------------------------
        # DEPARTMENTS
        # --------------------------------------------------------

        "departments":
            departments,

        "department_performance":
            department_performance,

        # --------------------------------------------------------
        # CONCERNS
        # --------------------------------------------------------

        "concerns":
            concerns,

        "concern_performance":
            concern_performance,

        # --------------------------------------------------------
        # OUTLETS
        # --------------------------------------------------------

        "outlets":
            outlets,

        "outlet_summary":
            outlet_summary,

        "concerns_per_outlet":
            concerns_per_outlet,
    }

    return render(
        request,
        "reports/reports.html",
        context
    )

    # ==========================================
    # TECHNICIANS
    # ==========================================

    technician_stats = []

    technicians = Technician.objects.all()

    department = request.GET.get(
        "department",
        ""
    ).strip()

    if department:

        technicians = technicians.filter(
            department__name=department
        )

    for tech in technicians:

        current_assigned = tickets.filter(
            Q(assigned_to=tech) |
            Q(additional_technicians=tech)
        ).distinct().count()

        primary_total = TicketAssignmentLog.objects.filter(
            new_technician=tech,
            ticket__in=tickets
        ).count()

        additional_total = TicketAdditionalAssignmentLog.objects.filter(
            technician=tech,
            action="added",
            ticket__in=tickets
        ).count()

        total_assigned = (
            primary_total +
            additional_total
        )

        resolved = tickets.filter(
            Q(assigned_to=tech) |
            Q(additional_technicians=tech),
            status="resolved"
        ).distinct().count()

        tech_on_time = tickets.filter(
            Q(assigned_to=tech) |
            Q(additional_technicians=tech),
            status="resolved",
            resolve_at__lte=F("deadline")
        ).distinct().count()

        reopened = TicketStatusLog.objects.filter(
            technician=tech,
            old_status="resolved",
            ticket__in=tickets
        ).count()

        technician_stats.append({

            "name": tech.full_name,

            "current_assigned":
                current_assigned,

            "total_assigned":
                total_assigned,

            "resolved":
                resolved,

            "resolved_on_time":
                tech_on_time,

            "reopened":
                reopened,
        })

    # ==========================================
    # OUTLET SUMMARY
    # ==========================================

    outlet_summary = (
        tickets
        .values("outlet__name")
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

    # ==========================================
    # CONCERNS PER OUTLET
    # ==========================================

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
            "outlet__name",
            "-total"
        )
    )

    # ==========================================
    # CONTEXT
    # ==========================================

    context = {

        **report_common_context(request),

        "tickets": tickets,

        "total":
            tickets.count(),

        "pending":
            tickets.filter(
                status="pending"
            ).count(),

        "progress":
            tickets.filter(
                status="progress"
            ).count(),

        "resolved":
            tickets.filter(
                status="resolved"
            ).count(),

        "cancelled":
            tickets.filter(
                status="cancelled"
            ).count(),

        "overdue":
            overdue,

        "resolved_on_time":
            resolved_on_time,

        "reopened_total":
            reopened_total,

        "technician_stats":
            technician_stats,

        "departments":
            tickets
            .values("department__name")
            .annotate(
                total=Count("id")
            )
            .order_by("-total"),

        "concerns":
            tickets
            .values("concern_type__name")
            .annotate(
                total=Count("id")
            )
            .order_by("-total"),

        "outlets":
            tickets
            .values(
                "outlet",
                "outlet__name"
            )
            .annotate(
                total=Count("id")
            )
            .order_by("-total"),

        "outlet_summary":
            outlet_summary,

        "concerns_per_outlet":
            concerns_per_outlet,
    }

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

    context = {

        **report_common_context(request),

        "tickets":
            tickets.order_by("-created_at"),

        "total":
            tickets.count(),

        "report_departments":
            Department.objects.all().order_by("name"),
    }

    return render(
        request,
        "reports/tickets.html",
        context
    )


# ============================================================
# OUTLETS
# ============================================================

# ============================================================
# OUTLETS
# ============================================================

def report_outlets(request):

    tickets = get_filtered_tickets(request)

    # ========================================================
    # OUTLET SUMMARY
    # ========================================================

    outlet_summary = (
        tickets
        .values("outlet__name")
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

    # ========================================================
    # CONCERNS PER OUTLET
    # ========================================================

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
            "outlet__name",
            "-total"
        )
    )

    # ========================================================
    # CONTEXT
    # ========================================================

    context = {

        **report_common_context(request),

        "outlet_summary":
            outlet_summary,

        "concerns_per_outlet":
            concerns_per_outlet,

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

    departments = (
        tickets
        .values(
            "department",
            "department__name"
        )
        .annotate(

            # TOTAL
            total=Count("id"),

            # OPEN / PENDING
            open=Count(
                "id",
                filter=Q(status="pending")
            ),

            # IN PROGRESS
            progress=Count(
                "id",
                filter=Q(status="progress")
            ),

            # RESOLVED
            resolved=Count(
                "id",
                filter=Q(status="resolved")
            ),
        )
        .order_by("department__name")
    )

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

            "total":
                assigned_total,

            "current_assigned":
                current_assigned,

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
    # CONTEXT
    # ========================================================

    context = {

        **report_common_context(request),

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
    # SORT PERFORMANCE
    # =====================================================

    concern_performance.sort(
        key=lambda x: x["name"].lower()
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
    }


    return render(
        request,
        "reports/concerns.html",
        context
    )