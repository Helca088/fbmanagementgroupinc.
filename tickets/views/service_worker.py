from django.http import HttpResponse
from django.template.loader import render_to_string


def employee_sw(request):
    content = render_to_string("tickets/sw/employee-sw.js")
    response = HttpResponse(
        content,
        content_type="application/javascript"
    )
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    return response


def admin_sw(request):
    content = render_to_string("tickets/sw/admin-sw.js")
    response = HttpResponse(
        content,
        content_type="application/javascript"
    )
    response["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    return response