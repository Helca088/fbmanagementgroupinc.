from django.http import HttpResponse
from django.utils import timezone
from django.db.models import Count, F
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from openpyxl import Workbook

from tickets.models import (
    Ticket,
    Technician,
    TicketStatusLog,
    TicketAssignmentLog,
)

def export_pdf(request):

    tickets = Ticket.objects.all()

    start = request.GET.get("start")
    end = request.GET.get("end")
    department = request.GET.get("department")

    if start and end:
        tickets = tickets.filter(
            created_at__date__range=[start, end])
        
    if department:
        tickets = tickets.filter(department__name =department)

    overdue = tickets.filter(
        deadline__lt=timezone.now()
    ).exclude(
        status="resolved"
    ).count()

    resolved_on_time = tickets.filter(
        status="resolved",
        resolve_at__lte=F("deadline")
    ).count()

    reopened = TicketStatusLog.objects.filter(
        old_status="resolved",
        ticket__in=tickets
    ).count()

    response = HttpResponse(
        content_type="application/pdf"
    )

    filename = "ticket_report.pdf"

    if department:
        filename = f"{department.lower()}_ticket_report.pdf"

    response["Content-Disposition"] = (
        f'attachment; filename="{filename}"'
    )

    doc = SimpleDocTemplate(response)

    styles = getSampleStyleSheet()

    elements = []

    # =====================
    # TITLE
    # =====================

    elements.append(
        Paragraph("Ticket Management Report", styles["Title"])
    )

    elements.append(
        Paragraph(
            f"Generated: {timezone.now().strftime('%Y-%m-%d %H:%M')}",
            styles["Normal"]
        )
    )

    elements.append(Spacer(1, 20))

    # =====================
    # SUMMARY
    # =====================

    elements.append(
        Paragraph("Summary", styles["Heading2"])
    )

    summary_data = [
        ["Metric", "Total"],
        ["Total Tickets", tickets.count()],
        ["Pending", tickets.filter(status="pending").count()],
        ["In Progress", tickets.filter(status="progress").count()],
        ["Resolved", tickets.filter(status="resolved").count()],
        ["Overdue", overdue],
        ["Resolved On Time", resolved_on_time],
        ["Reopened", reopened],
    ]

    summary_table = Table(summary_data)

    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
    ]))

    elements.append(summary_table)

    elements.append(Spacer(1, 20))

    # =====================
    # DEPARTMENTS
    # =====================

    departments = tickets.values(
        "department__name"
    ).annotate(
        total=Count("id")
    )

    elements.append(
        Paragraph("Departments", styles["Heading2"])
    )

    dept_data = [["Department", "Total"]]

    for d in departments:
        dept_data.append([
            d["department__name"] or "N/A",
            d["total"]
        ])

    dept_table = Table(dept_data)

    dept_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("GRID", (0,0), (-1,-1), 1, colors.black),
    ]))

    elements.append(dept_table)

    elements.append(Spacer(1, 20))

    # =====================
    # CONCERNS
    # =====================

    concerns = tickets.values(
        "concern_type__name"
    ).annotate(
        total=Count("id")
    )

    elements.append(
        Paragraph("Concerns", styles["Heading2"])
    )

    concern_data = [["Concern", "Total"]]

    for c in concerns:
        concern_data.append([
            c["concern_type__name"] or "N/A",
            c["total"]
        ])

    concern_table = Table(concern_data)

    concern_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("GRID", (0,0), (-1,-1), 1, colors.black),
    ]))

    elements.append(concern_table)

    elements.append(PageBreak())

    # =====================
    # TECHNICIANS
    # =====================

    elements.append(
        Paragraph("Technician Performance", styles["Heading2"])
    )

    tech_data = [[
        "Technician",
        "Current Assigned",
        "Total Assigned",
        "Resolved",
        "On Time",
        "Reopened"
    ]]

    technicians = Technician.objects.all()

    if department:
        technicians = technicians.filter(department__name=department)

    for tech in technicians:

        current_assigned = tickets.filter(
            assigned_to=tech
        ).count()

        total_assigned = TicketAssignmentLog.objects.filter(
            new_technician=tech,
            ticket__in=tickets
        ).count()

        resolved = tickets.filter(
            assigned_to=tech,
            status="resolved"
        ).count()

        on_time = tickets.filter(
            assigned_to=tech,
            status="resolved",
            resolve_at__lte=F("deadline")
        ).count()

        reopened = TicketStatusLog.objects.filter(
            ticket__assigned_to=tech,
            old_status="resolved"
        ).count()

        tech_data.append([
            tech.full_name,
            current_assigned,
            total_assigned,
            resolved,
            on_time,
            reopened,
        ])

    tech_table = Table(tech_data)

    tech_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("GRID", (0,0), (-1,-1), 1, colors.black),
    ]))

    elements.append(tech_table)

    elements.append(Spacer(1, 20))

    # =====================
    # TICKET DETAILS
    # =====================

    elements.append(
        Paragraph("Ticket Details", styles["Heading2"])
    )

    ticket_data = [[
        "ID",
        "Outlet",
        "Department",
        "Concern",
        "Status",
        "Technician"
    ]]

    for ticket in tickets:

        ticket_data.append([
            str(ticket.id),
            ticket.outlet,
            ticket.department.name if ticket.department else "",
            ticket.concern_type.name if ticket.concern_type else "",
            ticket.status,
            (
                ticket.assigned_to.full_name
                if ticket.assigned_to else ""
            )
        ])

    ticket_table = Table(
        ticket_data,
        colWidths=[40, 120, 80, 80, 60, 60]
    )

    ticket_table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("FONTSIZE", (0,0), (-1,-1), 8),
    ]))

    elements.append(ticket_table)

    doc.build(elements)

    return response

def export_excel(request):

    tickets = Ticket.objects.all()

    start = request.GET.get("start")
    end = request.GET.get("end")
    department =request.GET.get("department")

    if start and end:
        tickets = tickets.filter(
            created_at__date__range=[start, end])
    if department:
        tickets = tickets.filter(department__name=department)

    wb = Workbook()

    # =====================
    # SUMMARY
    # =====================

    ws = wb.active
    ws.title = "Summary"

    overdue = tickets.filter(
        deadline__lt=timezone.now()
    ).exclude(
        status="resolved"
    ).count()

    resolved_on_time = tickets.filter(
        status="resolved",
        resolve_at__lte=F("deadline")
    ).count()

    reopened = TicketStatusLog.objects.filter(
        old_status="resolved",
        ticket__in=tickets
    ).count()

    ws.append(["Metric", "Total"])
    ws.append(["Total Tickets", tickets.count()])
    ws.append(["Pending", tickets.filter(status="pending").count()])
    ws.append(["In Progress", tickets.filter(status="progress").count()])
    ws.append(["Resolved", tickets.filter(status="resolved").count()])
    ws.append(["Overdue", overdue])
    ws.append(["Resolved On Time", resolved_on_time])
    ws.append(["Reopened", reopened])

    # =====================
    # TICKETS
    # =====================

    ws2 = wb.create_sheet("Tickets")

    ws2.append([
        "ID",
        "Outlet",
        "Department",
        "Concern",
        "Status",
        "Technician",
        "Created",
        "Deadline"
    ])

    for ticket in tickets:
        ws2.append([
        ticket.id,
        ticket.outlet.name if ticket.outlet else "",
        ticket.department.name if ticket.department else "",
        ticket.concern_type.name if ticket.concern_type else "",
        ticket.status,
        ticket.assigned_to.full_name if ticket.assigned_to else "",
        ticket.created_at.strftime("%Y-%m-%d %H:%M"),
        ticket.deadline.strftime("%Y-%m-%d %H:%M") if ticket.deadline else ""
    ])

    # =====================
    # DEPARTMENTS
    # =====================

    ws3 = wb.create_sheet("Departments")

    ws3.append(["Department", "Total"])

    departments = tickets.values(
        "department__name"
    ).annotate(
        total=Count("id")
    )

    for d in departments:
        ws3.append([
            d["department__name"],
            d["total"]
        ])

    # =====================
    # CONCERNS
    # =====================

    ws4 = wb.create_sheet("Concerns")

    ws4.append(["Concern", "Total"])

    concerns = tickets.values(
        "concern_type__name"
    ).annotate(
        total=Count("id")
    )

    for c in concerns:
        ws4.append([
            c["concern_type__name"],
            c["total"]
        ])

    # =====================
    # TECHNICIANS
    # =====================

    ws5 = wb.create_sheet("Technicians")

    ws5.append([
        "Technician",
        "Current Assigned",
        "Total Assigned",
        "Resolved",
        "On Time",
        "Reopened"
    ])

    technicians = Technician.objects.all()

    if department:
     technicians = technicians.filter(department__name=department)

    for tech in technicians:

        current_assigned = tickets.filter(
            assigned_to=tech
        ).count()

        total_assigned =TicketAssignmentLog.objects.filter(
            new_technician=tech,
            ticket__in=tickets
        ).count()

        resolved = tickets.filter(
            assigned_to=tech,
            status="resolved"
        ).count()

        on_time = tickets.filter(
            assigned_to=tech,
            status="resolved",
            resolve_at__lte=F("deadline")
        ).count()

        reopened = TicketStatusLog.objects.filter(
            ticket__assigned_to=tech,
            old_status="resolved"
        ).count()

        ws5.append([
            tech.full_name,
            current_assigned,
            total_assigned,
            resolved,
            on_time,
            reopened
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    filename = "ticket_report.xlsx"

    if department:
        filename = f"{department.lower()}_ticket_report.xlsx"



    response["Content-Disposition"] = (
    f'attachment; filename="{filename}"'
    )

    wb.save(response)

    return response