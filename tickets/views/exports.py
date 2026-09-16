"""
Ticket reporting & export views.

Provides Excel (.xlsx) and PDF exports for:
    - Raw ticket listings
    - Outlet summaries
    - Department summaries
    - Technician workload / performance
    - Concern-type summaries
    - A combined dashboard report

All exports respect the same query-string filters used by their
corresponding report pages (start, end, department, outlet, concern).
"""

from datetime import datetime
from io import BytesIO

from django.db.models import Count, F, Q
from django.http import HttpResponse
from django.utils import timezone

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from tickets.models import (
    Outlet,
    Technician,
    Ticket,
    TicketAdditionalAssignmentLog,
    TicketAssignmentLog,
    TicketStatusLog,
)
from tickets.views import get_filtered_tickets


# =============================================================================
# CONSTANTS
# =============================================================================

# Brand / theme colors used across Excel + PDF exports.
COLOR_PRIMARY = "2563EB"      # Blue   – tickets / dashboard summary
COLOR_INDIGO = "4F46E5"       # Indigo – departments, technicians, concerns
COLOR_NAVY = "0F3554"         # Navy   – outlets
COLOR_GREEN = "059669"        # Green  – dashboard: outlets table
COLOR_AMBER = "D97706"        # Amber  – dashboard: concerns table
COLOR_VIOLET = "7C3AED"       # Violet – dashboard: technicians table

GRID_LIGHT = "E5E7EB"
GRID_LIGHTER = "F8FAFC"

PAGE_MARGIN = 30


def _as_hex(color):
    """Normalize a bare hex string ('4F46E5') for reportlab, which requires
    a leading '#' — unlike openpyxl, which requires the opposite. The color
    constants above are stored bare so they work directly with openpyxl;
    this is applied only at the reportlab call sites.
    """
    return color if color.startswith("#") else f"#{color}"


# =============================================================================
# SHARED HELPERS — FILTERING
# =============================================================================

def get_export_tickets(request):
    """Return tickets filtered by the basic ticket-list filters.

    Used by the raw ticket export only. Report-page exports use
    ``get_filtered_tickets`` (imported from tickets.views) instead, so
    that their totals always match what's shown on screen.
    """
    tickets = Ticket.objects.all()

    start = request.GET.get("start", "").strip()
    end = request.GET.get("end", "").strip()
    department = request.GET.get("department", "").strip()
    outlet = request.GET.get("outlet", "").strip()

    if start and end:
        tickets = tickets.filter(created_at__date__range=[start, end])
    elif start:
        tickets = tickets.filter(created_at__date__gte=start)
    elif end:
        tickets = tickets.filter(created_at__date__lte=end)

    if department:
        tickets = tickets.filter(department__name=department)
    if outlet:
        tickets = tickets.filter(outlet_id=outlet)

    return tickets


def get_request_filters(request):
    """Pull the common report filters out of the query string."""
    return {
        "start": request.GET.get("start", "").strip(),
        "end": request.GET.get("end", "").strip(),
        "department": request.GET.get("department", "").strip(),
        "outlet": request.GET.get("outlet", "").strip(),
    }


def build_filename(request, base_name, extension):
    """Build a download filename like '<Outlet>_<base_name>.<ext>'.

    Falls back to the department name, then to a generic name, mirroring
    the priority used throughout the report pages: outlet > department > none.
    """
    filters = get_request_filters(request)

    if filters["outlet"]:
        outlet_obj = Outlet.objects.filter(id=filters["outlet"]).first()
        prefix = outlet_obj.name if outlet_obj else "Outlet"
    elif filters["department"]:
        prefix = filters["department"]
    else:
        return f"{base_name}.{extension}"

    return f"{prefix}_{base_name}.{extension}".replace(" ", "_")


def build_filter_summary(request, include_outlet_label=True):
    """Human-readable one-line summary of the active filters, e.g.

        'Outlet: Downtown | Department: Kitchen | Date: 2026-01-01 to 2026-01-31'
    """
    filters = get_request_filters(request)
    parts = []

    if filters["outlet"]:
        outlet_obj = Outlet.objects.filter(id=filters["outlet"]).first()
        if outlet_obj:
            parts.append(f"Outlet: {outlet_obj.name}")
    elif include_outlet_label:
        parts.append("Outlet: All Outlets")

    parts.append(f"Department: {filters['department'] or 'All Departments'}")
    parts.append(f"Date: {filters['start'] or 'All'} to {filters['end'] or 'All'}")

    return " | ".join(parts)


# =============================================================================
# SHARED HELPERS — EXCEL STYLING
# =============================================================================

def style_excel_sheet(ws, title, headers):
    """Add a merged title row (row 1) and a styled header row (row 3)."""
    ws.merge_cells(start_row=1, start_column=1, end_row=1, end_column=len(headers))

    title_cell = ws.cell(row=1, column=1, value=title)
    title_cell.font = Font(bold=True, size=16)
    title_cell.alignment = Alignment(horizontal="center")

    style_header_row(ws, row=3, headers=headers, fill_color=COLOR_PRIMARY)


def style_header_row(ws, row, fill_color, headers=None):
    """Apply bold/white/filled/centered styling to an existing header row.

    If ``headers`` is given, the header text is written first; otherwise
    the row is assumed to already contain header values (e.g. via
    ``ws.append(...)``).
    """
    fill = PatternFill("solid", fgColor=fill_color)
    font = Font(bold=True, color="FFFFFF")
    alignment = Alignment(horizontal="center", vertical="center")

    if headers is not None:
        for col, header in enumerate(headers, start=1):
            ws.cell(row=row, column=col, value=header)

    for cell in ws[row]:
        cell.fill = fill
        cell.font = font
        cell.alignment = alignment


def auto_width(ws, max_width=50, padding=3):
    """Resize every column in ``ws`` to fit its longest value."""
    for column_cells in ws.columns:
        length = max(
            (len(str(cell.value)) for cell in column_cells if cell.value),
            default=0,
        )
        column_letter = get_column_letter(column_cells[0].column)
        ws.column_dimensions[column_letter].width = min(length + padding, max_width)


def new_workbook_response(filename):
    """Return an empty HttpResponse pre-configured as an .xlsx download."""
    response = HttpResponse(
        content_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


# =============================================================================
# SHARED HELPERS — PDF STYLING
# =============================================================================

def get_pdf_styles():
    """Base ReportLab stylesheet plus a couple of report-specific variants."""
    styles = getSampleStyleSheet()

    styles.add(
        ParagraphStyle(
            "ReportTitle",
            parent=styles["Title"],
            fontSize=18,
            alignment=TA_CENTER,
            spaceAfter=15,
        ),
        alias="report_title",
    )

    styles.add(
        ParagraphStyle(
            "ReportSubtitle",
            parent=styles["Normal"],
            fontSize=9,
            textColor=colors.HexColor("#64748B"),
            spaceAfter=10,
        ),
        alias="report_subtitle",
    )

    return styles


def new_pdf_document(response):
    """Standard landscape A4 document with consistent margins."""
    return SimpleDocTemplate(
        response,
        pagesize=landscape(A4),
        rightMargin=PAGE_MARGIN,
        leftMargin=PAGE_MARGIN,
        topMargin=PAGE_MARGIN,
        bottomMargin=PAGE_MARGIN,
    )


def build_table_style(header_color, font_size=9, zebra=True, padding=7):
    """A TableStyle covering the header row, grid, and (optionally) zebra rows.

    Used as the base style for every report table; callers can extend the
    returned command list with ``TableStyle(build_table_style(...).getCommands() + [...])``
    if a table needs extra formatting.
    """
    header_color = _as_hex(header_color)

    commands = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(header_color)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor(_as_hex(GRID_LIGHT))),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), padding),
        ("BOTTOMPADDING", (0, 0), (-1, -1), padding),
    ]
    if zebra:
        commands.append((
            "ROWBACKGROUNDS", (0, 1), (-1, -1),
            [colors.white, colors.HexColor(_as_hex(GRID_LIGHTER))],
        ))
    return TableStyle(commands)


def build_pdf_table(data, col_widths, header_color, **style_kwargs):
    """Convenience wrapper: a Table with the standard report styling applied."""
    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(build_table_style(header_color, **style_kwargs))
    return table


def new_pdf_response(filename):
    """Return an empty HttpResponse pre-configured as a .pdf download."""
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def add_pdf_header(elements, styles, title, subtitle=None, filter_summary=None):
    """Append the standard title / generated-at / filter-summary block."""
    elements.append(Paragraph(title, styles["report_title"]))

    if subtitle:
        elements.append(Paragraph(subtitle, styles["report_subtitle"]))
    else:
        generated = timezone.now().strftime("%B %d, %Y %I:%M %p")
        elements.append(Paragraph(f"Generated: {generated}", styles["Normal"]))

    if filter_summary:
        elements.append(Paragraph(filter_summary, styles["Normal"]))

    elements.append(Spacer(1, 15))


# =============================================================================
# RAW TICKET EXPORT
# =============================================================================

TICKET_EXPORT_HEADERS = ["Outlet", "Created", "Department", "Concern Type", "Message"]


def _ticket_export_row(ticket):
    return [
        ticket.outlet.name if ticket.outlet else "",
        ticket.created_at.strftime("%Y-%m-%d %H:%M") if ticket.created_at else "",
        ticket.department.name if ticket.department else "",
        ticket.concern_type.name if ticket.concern_type else "",
        ticket.message or "",
    ]


def export_tickets_excel(request):
    """Export the raw, unaggregated ticket list to Excel."""
    tickets = get_export_tickets(request).order_by("-created_at")

    wb = Workbook()
    ws = wb.active
    ws.title = "Tickets"

    style_excel_sheet(ws, "FB Management - Ticket Report", TICKET_EXPORT_HEADERS)

    for row_offset, ticket in enumerate(tickets):
        row = row_offset + 4
        for col, value in enumerate(_ticket_export_row(ticket), start=1):
            ws.cell(row=row, column=col, value=value)

    auto_width(ws)

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    response = HttpResponse(
        output.getvalue(),
        content_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    )
    response["Content-Disposition"] = 'attachment; filename="tickets_report.xlsx"'
    return response


def export_tickets_pdf(request):
    """Export the raw, unaggregated ticket list to PDF."""
    tickets = get_export_tickets(request).order_by("-created_at")

    response = new_pdf_response("tickets_report.pdf")
    document = new_pdf_document(response)
    styles = get_pdf_styles()

    elements = [
        Paragraph("FB Management — Ticket Report", styles["report_title"]),
        Spacer(1, 10),
    ]

    data = [TICKET_EXPORT_HEADERS] + [_ticket_export_row(t) for t in tickets]
    table = build_pdf_table(
        data,
        col_widths=[100, 100, 100, 130, 300],
        header_color=COLOR_PRIMARY,
        font_size=8,
    )
    elements.append(table)

    document.build(elements)
    return response


# =============================================================================
# OUTLET REPORT
# =============================================================================

def get_outlet_report_data(request):
    """Outlet-level ticket totals and per-outlet concern breakdowns."""
    tickets = get_filtered_tickets(request)

    outlet_summary = (
        tickets.values("outlet__name")
        .annotate(
            total=Count("id"),
            pending=Count("id", filter=Q(status="pending")),
            progress=Count("id", filter=Q(status="progress")),
            resolved=Count("id", filter=Q(status="resolved")),
            cancelled=Count("id", filter=Q(status="cancelled")),
        )
        .order_by("outlet__name")
    )

    concerns_per_outlet = (
        tickets.values("outlet__name", "concern_type__name")
        .annotate(total=Count("id"))
        .order_by("outlet__name", "-total")
    )

    return outlet_summary, concerns_per_outlet


def export_outlets_pdf(request):
    outlet_summary, concerns_per_outlet = get_outlet_report_data(request)

    response = new_pdf_response(build_filename(request, "outlet_report", "pdf"))
    doc = new_pdf_document(response)
    styles = get_pdf_styles()

    elements = []
    add_pdf_header(
        elements, styles, "Outlet Report",
        filter_summary=build_filter_summary(request, include_outlet_label=False) or None,
    )

    # --- Outlets table -------------------------------------------------
    elements.append(Paragraph("Outlets", styles["Heading2"]))
    elements.append(Paragraph("Ticket summary by outlet", styles["Normal"]))
    elements.append(Spacer(1, 10))

    outlet_data = [["Outlet", "Total", "Pending", "Progress", "Resolved", "Cancelled"]]
    for row in outlet_summary:
        outlet_data.append([
            row["outlet__name"] or "N/A",
            row["total"], row["pending"], row["progress"],
            row["resolved"], row["cancelled"],
        ])
    elements.append(build_pdf_table(outlet_data, [180, 80, 80, 80, 80, 80], COLOR_NAVY))
    elements.append(Spacer(1, 30))

    # --- Concerns per outlet table --------------------------------------
    elements.append(Paragraph("Concerns per Outlet", styles["Heading2"]))
    elements.append(Paragraph("Ticket concerns grouped by outlet", styles["Normal"]))
    elements.append(Spacer(1, 10))

    concern_data = [["Outlet", "Concern", "Total"]]
    for row in concerns_per_outlet:
        concern_data.append([
            row["outlet__name"] or "N/A",
            row["concern_type__name"] or "N/A",
            row["total"],
        ])
    elements.append(build_pdf_table(concern_data, [220, 300, 100], COLOR_NAVY))

    doc.build(elements)
    return response


def export_outlets_excel(request):
    outlet_summary, concerns_per_outlet = get_outlet_report_data(request)

    wb = Workbook()

    ws1 = wb.active
    ws1.title = "Outlets"
    ws1.append(["Outlet", "Total", "Pending", "Progress", "Resolved", "Cancelled"])
    for row in outlet_summary:
        ws1.append([
            row["outlet__name"] or "N/A",
            row["total"], row["pending"], row["progress"],
            row["resolved"], row["cancelled"],
        ])

    ws2 = wb.create_sheet("Concerns per Outlet")
    ws2.append(["Outlet", "Concern", "Total"])
    for row in concerns_per_outlet:
        ws2.append([
            row["outlet__name"] or "N/A",
            row["concern_type__name"] or "N/A",
            row["total"],
        ])

    for ws, widths in ((ws1, [25, 12, 12, 12, 12, 12]), (ws2, [25, 35, 12])):
        style_header_row(ws, row=1, fill_color=COLOR_NAVY)
        for col, width in zip("ABCDEF", widths):
            ws.column_dimensions[col].width = width
        ws.freeze_panes = "A2"

    response = new_workbook_response(build_filename(request, "outlet_report", "xlsx"))
    wb.save(response)
    return response


# =============================================================================
# DEPARTMENT REPORT
# =============================================================================

def get_department_report_data(request):
    """Aggregate ticket counts and resolution performance per department."""
    tickets = get_filtered_tickets(request).select_related(
        "department", "outlet", "concern_type"
    )

    departments = {}

    for ticket in tickets:
        if not ticket.department:
            continue

        data = departments.setdefault(ticket.department.name, {
            "total": 0, "open": 0, "progress": 0, "resolved": 0,
            "overdue": 0, "resolution_times": [],
        })

        data["total"] += 1

        if ticket.status == "pending":
            data["open"] += 1
        elif ticket.status == "progress":
            data["progress"] += 1
        elif ticket.status == "resolved":
            data["resolved"] += 1

        if ticket.is_overdue:
            data["overdue"] += 1

        if ticket.status == "resolved" and ticket.resolve_at and ticket.created_at:
            seconds = (ticket.resolve_at - ticket.created_at).total_seconds()
            data["resolution_times"].append(seconds / 86400)

    for data in departments.values():
        times = data["resolution_times"]
        data["avg_resolution_time"] = sum(times) / len(times) if times else 0
        data["resolution_rate"] = (data["resolved"] / data["total"] * 100) if data["total"] else 0

    return departments


def export_departments_excel(request):
    departments = get_department_report_data(request)

    wb = Workbook()

    ws1 = wb.active
    ws1.title = "Departments"
    ws1.append(["Department", "Total", "Open", "In Progress", "Resolved"])
    for name in sorted(departments):
        d = departments[name]
        ws1.append([name, d["total"], d["open"], d["progress"], d["resolved"]])

    ws2 = wb.create_sheet("Department Performance")
    ws2.append(["Department", "Avg. Resolution Time", "Overdue", "Resolution Rate"])
    for name in sorted(departments):
        d = departments[name]
        ws2.append([
            name,
            round(d["avg_resolution_time"], 1),
            d["overdue"],
            round(d["resolution_rate"], 1) / 100,
        ])

    style_header_row(ws1, row=1, fill_color=COLOR_INDIGO)
    for col, width in zip("ABCDE", [25, 12, 12, 15, 12]):
        ws1.column_dimensions[col].width = width
    ws1.freeze_panes = "A2"

    style_header_row(ws2, row=1, fill_color=COLOR_INDIGO)
    for col, width in zip("ABCD", [25, 25, 12, 18]):
        ws2.column_dimensions[col].width = width
    ws2.freeze_panes = "A2"
    for row in range(2, ws2.max_row + 1):
        ws2.cell(row=row, column=4).number_format = "0.0%"

    response = new_workbook_response(build_filename(request, "department_report", "xlsx"))
    wb.save(response)
    return response


def export_departments_pdf(request):
    departments = get_department_report_data(request)

    response = new_pdf_response(build_filename(request, "department_report", "pdf"))
    document = new_pdf_document(response)
    styles = get_pdf_styles()

    elements = []
    add_pdf_header(
        elements, styles, "FB Management — Department Report",
        filter_summary=build_filter_summary(request) or None,
    )

    # --- Departments table -----------------------------------------------
    elements.append(Paragraph("Departments", styles["Heading2"]))
    elements.append(Paragraph("Ticket summary by department", styles["Normal"]))
    elements.append(Spacer(1, 10))

    department_data = [["Department", "Total", "Open", "In Progress", "Resolved"]]
    for name in sorted(departments):
        d = departments[name]
        department_data.append([name, d["total"], d["open"], d["progress"], d["resolved"]])
    elements.append(build_pdf_table(department_data, [230, 80, 80, 100, 80], COLOR_INDIGO))
    elements.append(Spacer(1, 30))

    # --- Performance table -------------------------------------------------
    elements.append(Paragraph("Department Performance", styles["Heading2"]))
    elements.append(Paragraph("Resolution performance by department", styles["Normal"]))
    elements.append(Spacer(1, 10))

    performance_data = [["Department", "Avg. Resolution Time", "Overdue", "Resolution Rate"]]
    for name in sorted(departments):
        d = departments[name]
        performance_data.append([
            name,
            f'{d["avg_resolution_time"]:.1f} days',
            d["overdue"],
            f'{d["resolution_rate"]:.1f}%',
        ])
    elements.append(build_pdf_table(performance_data, [230, 180, 100, 150], COLOR_INDIGO))

    document.build(elements)
    return response


# =============================================================================
# TECHNICIAN REPORT
# =============================================================================

def get_technician_report_data(request):
    """Workload and performance metrics for each technician.

    Returns a tuple of (workload_rows, performance_rows) — two parallel
    lists of dicts, one entry per technician.
    """
    tickets = get_filtered_tickets(request)
    technicians = Technician.objects.all().order_by("full_name")

    department = request.GET.get("department", "").strip()
    if department:
        technicians = technicians.filter(department__name=department)

    now = timezone.now()
    workload_rows = []
    performance_rows = []

    for tech in technicians:
        assigned = tickets.filter(
            Q(assigned_to=tech) | Q(additional_technicians=tech)
        ).distinct()

        total = assigned.count()
        pending = assigned.filter(status="pending").count()
        progress = assigned.filter(status="progress").count()
        resolved = assigned.filter(status="resolved").count()
        cancelled = assigned.filter(status="cancelled").count()

        overdue = assigned.filter(deadline__lt=now).exclude(
            status__in=["resolved", "cancelled"]
        ).count()

        total_assigned = (
            TicketAssignmentLog.objects.filter(
                new_technician=tech, ticket__in=tickets
            ).count()
            + TicketAdditionalAssignmentLog.objects.filter(
                technician=tech, action="added", ticket__in=tickets
            ).count()
        )

        resolution_days = [
            (t.resolve_at - t.created_at).total_seconds() / 86400
            for t in assigned.filter(
                status="resolved", resolve_at__isnull=False, created_at__isnull=False
            )
        ]
        average_days = round(sum(resolution_days) / len(resolution_days), 1) if resolution_days else 0

        resolution_rate = round((resolved / total * 100), 1) if total else 0

        on_time = assigned.filter(
            status="resolved", resolve_at__isnull=False,
            deadline__isnull=False, resolve_at__lte=F("deadline"),
        ).count()

        reopened = TicketStatusLog.objects.filter(
            technician=tech, old_status="resolved", ticket__in=tickets
        ).count()

        name = tech.full_name or "Unnamed Technician"

        workload_rows.append({
            "name": name, "total": total, "open": pending, "progress": progress,
            "resolved": resolved, "cancelled": cancelled, "total_assigned": total_assigned,
        })

        performance_rows.append({
            "name": name, "average_days": average_days, "overdue": overdue,
            "resolution_rate": resolution_rate, "on_time": on_time,
            "reopened": reopened, "total": total, "resolved": resolved,
        })

    return workload_rows, performance_rows


def export_technicians_pdf(request):
    workload_rows, performance_rows = get_technician_report_data(request)

    response = new_pdf_response(build_filename(request, "technician_report", "pdf"))
    doc = new_pdf_document(response)
    styles = get_pdf_styles()

    elements = []
    add_pdf_header(
        elements, styles, "FB Management — Technician Report",
        filter_summary=build_filter_summary(request),
    )

    # --- Workload table ----------------------------------------------------
    elements.append(Paragraph("Technician Workload", styles["Heading2"]))
    elements.append(Paragraph(
        "Ticket volume and current workload by technician.", styles["Normal"]
    ))
    elements.append(Spacer(1, 10))

    workload_data = [["Technician", "Total", "Pending", "In Progress", "Resolved", "Cancelled"]]
    for tech in workload_rows:
        workload_data.append([
            tech["name"], tech["total"], tech["open"],
            tech["progress"], tech["resolved"], tech["cancelled"],
        ])
    elements.append(build_pdf_table(
        workload_data, [190, 70, 80, 100, 80, 80], COLOR_INDIGO, padding=8
    ))
    elements.append(Spacer(1, 25))

    # --- Performance table ---------------------------------------------------
    elements.append(Paragraph("Technician Performance", styles["Heading2"]))
    elements.append(Paragraph(
        "Resolution performance and efficiency by technician.", styles["Normal"]
    ))
    elements.append(Spacer(1, 10))

    performance_data = [
        ["Technician", "Avg. Resolution Time", "Overdue", "Resolution Rate", "On Time", "Reopened"]
    ]
    for tech in performance_rows:
        performance_data.append([
            tech["name"], f'{tech["average_days"]} days', tech["overdue"],
            f'{tech["resolution_rate"]:.1f}%', tech["on_time"], tech["reopened"],
        ])
    elements.append(build_pdf_table(
        performance_data, [170, 125, 75, 100, 70, 75], COLOR_INDIGO, padding=8
    ))

    doc.build(elements)
    return response


def export_technicians_excel(request):
    workload_rows, performance_rows = get_technician_report_data(request)

    wb = Workbook()

    ws1 = wb.active
    ws1.title = "Technician Workload"
    ws1.append([
        "Technician", "Total", "Pending", "In Progress",
        "Resolved", "Cancelled", "Total Assignments",
    ])
    for tech in workload_rows:
        ws1.append([
            tech["name"], tech["total"], tech["open"], tech["progress"],
            tech["resolved"], tech["cancelled"], tech["total_assigned"],
        ])

    ws2 = wb.create_sheet("Technician Performance")
    ws2.append([
        "Technician", "Avg. Resolution Time (Days)", "Overdue",
        "Resolution Rate", "On Time", "Reopened", "Total", "Resolved",
    ])
    for tech in performance_rows:
        ws2.append([
            tech["name"], tech["average_days"], tech["overdue"],
            tech["resolution_rate"], tech["on_time"], tech["reopened"],
            tech["total"], tech["resolved"],
        ])

    thin_border = Border(bottom=Side(style="thin", color=GRID_LIGHT))
    for ws in (ws1, ws2):
        style_header_row(ws, row=1, fill_color=COLOR_INDIGO)
        for cell in ws[1]:
            cell.border = thin_border
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions

    auto_width(ws1, max_width=35)
    auto_width(ws2, max_width=35)

    # Prepend a title row above the header/data.
    ws1.insert_rows(1, 2)
    ws1["A1"] = "FB Management — Technician Report"
    ws1["A1"].font = Font(bold=True, size=16)
    ws1.merge_cells(start_row=1, start_column=1, end_row=1, end_column=7)

    ws2.insert_rows(1, 2)
    ws2["A1"] = "FB Management — Technician Performance"
    ws2["A1"].font = Font(bold=True, size=16)
    ws2.merge_cells(start_row=1, start_column=1, end_row=1, end_column=8)

    response = new_workbook_response(build_filename(request, "technician_report", "xlsx"))
    wb.save(response)
    return response


# =============================================================================
# CONCERN REPORT
# =============================================================================

def get_concern_report_data(request):
    """Per-concern-type ticket totals and resolution performance.

    Unlike the other report data functions, this one builds its own
    queryset directly from ``Ticket`` (rather than ``get_filtered_tickets``)
    because the Concern report page supports an extra ``concern`` filter.
    """
    filters = get_request_filters(request)
    selected_concern = request.GET.get("concern", "").strip()

    tickets = Ticket.objects.all()

    if filters["start"]:
        try:
            start_date = datetime.strptime(filters["start"], "%Y-%m-%d").date()
            tickets = tickets.filter(created_at__date__gte=start_date)
        except ValueError:
            pass

    if filters["end"]:
        try:
            end_date = datetime.strptime(filters["end"], "%Y-%m-%d").date()
            tickets = tickets.filter(created_at__date__lte=end_date)
        except ValueError:
            pass

    if filters["department"]:
        tickets = tickets.filter(department__name=filters["department"])
    if filters["outlet"]:
        tickets = tickets.filter(outlet_id=filters["outlet"])
    if selected_concern:
        tickets = tickets.filter(concern_type_id=selected_concern)

    concern_summary = (
        tickets.values("concern_type_id", "concern_type__name", "department__name")
        .annotate(
            total=Count("id"),
            open=Count("id", filter=Q(status="pending")),
            progress=Count("id", filter=Q(status="progress")),
            resolved=Count("id", filter=Q(status="resolved")),
        )
        .order_by("concern_type__name")
    )

    performance = []

    for row in concern_summary:
        concern_id = row["concern_type_id"]
        if not concern_id:
            continue

        concern_tickets = tickets.filter(concern_type_id=concern_id)
        resolved_tickets = concern_tickets.filter(
            status="resolved", resolve_at__isnull=False, created_at__isnull=False
        )

        resolution_days = [
            (t.resolve_at - t.created_at).total_seconds() / 86400
            for t in resolved_tickets
        ]
        average_days = round(sum(resolution_days) / len(resolution_days), 1) if resolution_days else 0

        overdue = concern_tickets.filter(
            deadline__isnull=False, resolve_at__isnull=False,
            resolve_at__lte=F("deadline"), status="resolved",
        ).count()

        total_count = concern_tickets.count()
        resolved_count = resolved_tickets.count()
        resolution_rate = round(resolved_count / total_count * 100, 1) if total_count else 0

        performance.append({
            "name": row["concern_type__name"],
            "department": row["department__name"] or "—",
            "total": row["total"],
            "open": row["open"],
            "progress": row["progress"],
            "resolved": row["resolved"],
            "average_days": average_days,
            "overdue": overdue,
            "resolution_rate": resolution_rate,
        })

    return performance, filters["start"], filters["end"], filters["department"], filters["outlet"], selected_concern


def export_concerns_pdf(request):
    concerns, start, end, department, outlet, _concern = get_concern_report_data(request)

    response = new_pdf_response("concern_report.pdf")
    document = new_pdf_document(response)
    styles = get_pdf_styles()

    elements = [
        Paragraph("FB MANAGEMENT GROUP INC.", styles["report_title"]),
        Paragraph("Concern Report", styles["Heading2"]),
        Spacer(1, 10),
        Paragraph(
            f"Start: {start or 'All'} &nbsp;&nbsp;&nbsp; "
            f"End: {end or 'All'} &nbsp;&nbsp;&nbsp; "
            f"Department: {department or 'All'} &nbsp;&nbsp;&nbsp; "
            f"Outlet: {outlet or 'All'}",
            styles["Normal"],
        ),
        Spacer(1, 15),
    ]

    # --- Summary table -------------------------------------------------
    summary_data = [["Concern", "Department", "Total", "Open", "In Progress", "Resolved"]]
    for row in concerns:
        summary_data.append([
            row["name"] or "—", row["department"] or "—",
            str(row["total"]), str(row["open"]), str(row["progress"]), str(row["resolved"]),
        ])
    if len(summary_data) == 1:
        summary_data.append(["No data", "", "", "", "", ""])

    elements.append(Paragraph("Concern Summary", styles["Heading2"]))
    elements.append(build_pdf_table(
        summary_data, [150, 110, 70, 70, 90, 70], COLOR_INDIGO, font_size=8
    ))
    elements.append(Spacer(1, 20))

    # --- Performance table -----------------------------------------------
    performance_data = [["Concern", "Avg. Resolution Time", "Overdue", "Resolution Rate"]]
    for row in concerns:
        days = row["average_days"]
        performance_data.append([
            row["name"] or "—",
            f'{days} day{"s" if days != 1 else ""}',
            str(row["overdue"]),
            f'{row["resolution_rate"]:.1f}%',
        ])
    if len(performance_data) == 1:
        performance_data.append(["No data", "", "", ""])

    elements.append(Paragraph("Concern Performance", styles["Heading2"]))
    elements.append(build_pdf_table(
        performance_data, [220, 180, 100, 150], COLOR_INDIGO, font_size=8, zebra=False
    ))

    document.build(elements)
    return response


def export_concerns_excel(request):
    concerns, *_ = get_concern_report_data(request)

    wb = Workbook()

    ws1 = wb.active
    ws1.title = "Concern Summary"
    ws1.append(["Concern", "Department", "Total", "Open", "In Progress", "Resolved"])
    for row in concerns:
        ws1.append([
            row["name"] or "—", row["department"] or "—",
            row["total"], row["open"], row["progress"], row["resolved"],
        ])
    style_header_row(ws1, row=1, fill_color=COLOR_INDIGO)
    for col, width in zip("ABCDEF", [35, 25, 12, 12, 15, 12]):
        ws1.column_dimensions[col].width = width

    ws2 = wb.create_sheet("Concern Performance")
    ws2.append(["Concern", "Avg. Resolution Time", "Overdue", "Resolution Rate"])
    for row in concerns:
        days = row["average_days"]
        ws2.append([
            row["name"] or "—",
            f'{days} day{"s" if days != 1 else ""}',
            row["overdue"],
            row["resolution_rate"] / 100,
        ])
    style_header_row(ws2, row=1, fill_color=COLOR_INDIGO)
    for col, width in zip("ABCD", [35, 25, 12, 20]):
        ws2.column_dimensions[col].width = width
    for cell in ws2["D"][1:]:
        cell.number_format = "0.0%"

    response = new_workbook_response("concern_report.xlsx")
    wb.save(response)
    return response


# =============================================================================
# DASHBOARD / COMBINED SUMMARY REPORT
# =============================================================================

def get_dashboard_summary(tickets):
    """Top-line ticket counts used at the head of the dashboard report."""
    return {
        "total": tickets.count(),
        "pending": tickets.filter(status="pending").count(),
        "progress": tickets.filter(status="progress").count(),
        "resolved": tickets.filter(status="resolved").count(),
        "cancelled": tickets.filter(status="cancelled").count(),
        "overdue": tickets.filter(deadline__lt=timezone.now())
            .exclude(status__in=["resolved", "cancelled"]).count(),
        "resolved_on_time": tickets.filter(
            status="resolved", resolve_at__isnull=False,
            deadline__isnull=False, resolve_at__lte=F("deadline"),
        ).count(),
        "reopened": TicketStatusLog.objects.filter(
            old_status="resolved", ticket__in=tickets
        ).values("ticket").distinct().count(),
    }


def get_dashboard_breakdowns(tickets):
    """Department / outlet / concern breakdowns for the dashboard report."""
    departments = (
        tickets.values("department__name")
        .annotate(
            total=Count("id"),
            pending=Count("id", filter=Q(status="pending")),
            progress=Count("id", filter=Q(status="progress")),
            resolved=Count("id", filter=Q(status="resolved")),
            cancelled=Count("id", filter=Q(status="cancelled")),
        )
        .order_by("department__name")
    )

    outlets = (
        tickets.values("outlet__name")
        .annotate(
            total=Count("id"),
            pending=Count("id", filter=Q(status="pending")),
            progress=Count("id", filter=Q(status="progress")),
            resolved=Count("id", filter=Q(status="resolved")),
            cancelled=Count("id", filter=Q(status="cancelled")),
        )
        .order_by("outlet__name")
    )

    concerns = (
        tickets.values("concern_type__name")
        .annotate(total=Count("id"))
        .order_by("-total")
    )

    return departments, outlets, concerns


def get_dashboard_technicians(request, tickets):
    """Simplified technician summary (current load, totals, resolved, reopened)."""
    technicians = Technician.objects.all().order_by("full_name")

    department = request.GET.get("department", "").strip()
    if department:
        technicians = technicians.filter(department__name=department)

    rows = []
    for tech in technicians:
        assigned = tickets.filter(
            Q(assigned_to=tech) | Q(additional_technicians=tech)
        ).distinct()

        current_assigned = assigned.exclude(status__in=["resolved", "cancelled"]).count()

        total_assigned = (
            TicketAssignmentLog.objects.filter(
                new_technician=tech, ticket__in=tickets
            ).count()
            + TicketAdditionalAssignmentLog.objects.filter(
                technician=tech, action="added", ticket__in=tickets
            ).count()
        )

        resolved_count = assigned.filter(status="resolved").count()

        reopened = TicketStatusLog.objects.filter(
            technician=tech, old_status="resolved", ticket__in=tickets
        ).values("ticket").distinct().count()

        rows.append([
            tech.full_name or "Unnamed Technician",
            current_assigned, total_assigned, resolved_count, reopened,
        ])

    return rows


def export_reports_pdf(request):
    """Combined dashboard PDF: ticket summary + department/outlet/concern/technician tables."""
    tickets = get_filtered_tickets(request)

    summary = get_dashboard_summary(tickets)
    departments, outlets, concerns = get_dashboard_breakdowns(tickets)
    technician_rows = get_dashboard_technicians(request, tickets)

    response = new_pdf_response("dashboard_report.pdf")
    doc = new_pdf_document(response)
    styles = get_pdf_styles()

    elements = []
    add_pdf_header(
        elements, styles, "FB Management — Dashboard Summary",
        subtitle=build_filter_summary(request),
    )

    # --- Ticket summary ------------------------------------------------
    elements.append(Paragraph("Ticket Summary", styles["Heading2"]))
    summary_data = [
        ["Total", "Pending", "In Progress", "Resolved", "Overdue", "On Time", "Reopened", "Cancelled"],
        [
            summary["total"], summary["pending"], summary["progress"], summary["resolved"],
            summary["overdue"], summary["resolved_on_time"], summary["reopened"], summary["cancelled"],
        ],
    ]
    table = Table(summary_data, repeatRows=1)
    table.setStyle(build_table_style(COLOR_PRIMARY, zebra=False, padding=8))
    table.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
    elements.append(table)
    elements.append(Spacer(1, 20))

    # --- Department summary ----------------------------------------------
    elements.append(Paragraph("Department Summary", styles["Heading2"]))
    department_data = [["Department", "Total", "Pending", "In Progress", "Resolved", "Cancelled"]]
    for row in departments:
        department_data.append([
            row["department__name"] or "N/A", row["total"], row["pending"],
            row["progress"], row["resolved"], row["cancelled"],
        ])
    elements.append(build_pdf_table(department_data, None, COLOR_INDIGO, font_size=8, zebra=False))
    elements.append(Spacer(1, 20))

    # --- Outlet summary ----------------------------------------------------
    elements.append(Paragraph("Outlet Summary", styles["Heading2"]))
    outlet_data = [["Outlet", "Total", "Pending", "In Progress", "Resolved", "Cancelled"]]
    for row in outlets:
        outlet_data.append([
            row["outlet__name"] or "N/A", row["total"], row["pending"],
            row["progress"], row["resolved"], row["cancelled"],
        ])
    elements.append(build_pdf_table(outlet_data, None, COLOR_GREEN, font_size=8, zebra=False))
    elements.append(Spacer(1, 20))

    # --- Concern summary ---------------------------------------------------
    elements.append(Paragraph("Concern Summary", styles["Heading2"]))
    concern_data = [["Concern", "Total"]]
    for row in concerns:
        concern_data.append([row["concern_type__name"] or "N/A", row["total"]])
    elements.append(build_pdf_table(concern_data, None, COLOR_AMBER, font_size=8, zebra=False))
    elements.append(Spacer(1, 20))

    # --- Technician summary ------------------------------------------------
    elements.append(Paragraph("Technician Summary", styles["Heading2"]))
    technician_data = [["Technician", "Current Assigned", "Total Assignments", "Resolved", "Reopened"]]
    technician_data.extend(technician_rows)
    elements.append(build_pdf_table(technician_data, None, COLOR_VIOLET, font_size=8, zebra=False))

    doc.build(elements)
    return response


def export_reports_excel(request):
    """Combined dashboard workbook: one sheet per breakdown."""
    tickets = get_filtered_tickets(request)

    summary = get_dashboard_summary(tickets)
    departments, outlets, concerns = get_dashboard_breakdowns(tickets)
    technician_rows = get_dashboard_technicians(request, tickets)

    wb = Workbook()

    ws = wb.active
    ws.title = "Summary"
    ws.append(["Metric", "Total"])
    ws.append(["Total Tickets", summary["total"]])
    ws.append(["Pending", summary["pending"]])
    ws.append(["In Progress", summary["progress"]])
    ws.append(["Resolved", summary["resolved"]])
    ws.append(["Overdue", summary["overdue"]])
    ws.append(["Resolved On Time", summary["resolved_on_time"]])
    ws.append(["Reopened", summary["reopened"]])
    ws.append(["Cancelled", summary["cancelled"]])

    ws2 = wb.create_sheet("Departments")
    ws2.append(["Department", "Total", "Pending", "In Progress", "Resolved", "Cancelled"])
    for row in departments:
        ws2.append([
            row["department__name"] or "N/A", row["total"], row["pending"],
            row["progress"], row["resolved"], row["cancelled"],
        ])

    ws3 = wb.create_sheet("Outlets")
    ws3.append(["Outlet", "Total", "Pending", "In Progress", "Resolved", "Cancelled"])
    for row in outlets:
        ws3.append([
            row["outlet__name"] or "N/A", row["total"], row["pending"],
            row["progress"], row["resolved"], row["cancelled"],
        ])

    ws4 = wb.create_sheet("Concerns")
    ws4.append(["Concern", "Total"])
    for row in concerns:
        ws4.append([row["concern_type__name"] or "N/A", row["total"]])

    ws5 = wb.create_sheet("Technicians")
    ws5.append(["Technician", "Current Assigned", "Total Assignments", "Resolved", "Reopened"])
    for row in technician_rows:
        ws5.append(row)

    for worksheet in wb.worksheets:
        style_header_row(worksheet, row=1, fill_color=COLOR_PRIMARY)
        worksheet.freeze_panes = "A2"
        auto_width(worksheet)

    output = BytesIO()
    wb.save(output)
    output.seek(0)

    response = HttpResponse(
        output.getvalue(),
        content_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    )
    response["Content-Disposition"] = 'attachment; filename="dashboard_report.xlsx"'
    return response