from django.urls import path, include

from tickets.views.exports import (
    export_tickets_pdf,
    export_tickets_excel,
    export_outlets_pdf,
    export_outlets_excel,
    export_departments_excel,
    export_departments_pdf,
    export_technicians_pdf,
    export_technicians_excel,
    export_concerns_excel,
    export_concerns_pdf,
    export_reports_pdf,
    export_reports_excel,
)

from. import views

urlpatterns = [      
    path("", views.index),
    path("home/", views.home, name="home"),
    path("admin_dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path('login/', views.email_login, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('ticket/<int:ticket_id>/pdf/', views.download_ticket, name='download_ticket'),
    path('attachment/<int:pk>/download/', views.download_attachment, name='download-attachment'),
    path('ticket/<int:id>/status/', views.update_status, name='update_status'),
    path("ticket/<int:id>/priority/", views.update_priority, name="update_priority"),
    path('api/tickets/', views.ticket_api, name='ticket_api'),
    path(
    "save-fcm-token/",
    views.save_fcm_token,
    name="save_fcm_token"
    ),
    path('create/', views.create_ticket, name='create_ticket'),
    path('edit/<int:id>/', views.edit_ticket, name='edit_ticket'),
    path('delete-ticket/<int:id>/', views.delete_ticket, name='delete_ticket'),
    path("get-concerns/", views.get_concerns, name="get_concerns"),
    #NEW 7/27
    path("store/logs/", views.store_logs, name="store_logs"),
    #8/11
    path("reports/", views.reports, name="reports"),
    path("reports/tickets/", views.report_tickets, name="report_tickets"),
    path("reports/outlets/", views.report_outlets, name="report_outlets"),
    path("reports/departments/", views.report_departments, name="report_departments"),
    path("reports/technicians/", views.report_technicians, name="report_technicians"),
    path("reports/concerns/", views.report_concerns, name="report_concerns"),
    path(
    "reports/tickets/export/pdf/",
    export_tickets_pdf,
    name="export_tickets_pdf"
    ),

    path(
        "reports/tickets/export/excel/",
        export_tickets_excel,
        name="export_tickets_excel"
    ),
    path(
    "reports/outlets/export/pdf/",
    export_outlets_pdf,
    name="export_outlets_pdf"
    ),

    path(
        "reports/outlets/export/excel/",
        export_outlets_excel,
        name="export_outlets_excel"
    ),
    path(
    "reports/departments/export/pdf/",
    export_departments_pdf,
    name="export_departments_pdf",
    ),

    path(
        "reports/departments/export/excel/",
        export_departments_excel,
        name="export_departments_excel",
    ),
    path(
    "reports/technicians/export/pdf/",
    export_technicians_pdf,
    name="export_technicians_pdf",
    ),

    path(
        "reports/technicians/export/excel/",
        export_technicians_excel,
        name="export_technicians_excel",
    ),
    path(
    "reports/concerns/export/pdf/",
    export_concerns_pdf,
    name="export_concerns_pdf"
    ),

    path(
        "reports/concerns/export/excel/",
    export_concerns_excel,
        name="export_concerns_excel"
    ),
    path(
    "reports/export/pdf/",
    export_reports_pdf,
    name="export_reports_pdf"
    ),

    path(
        "reports/export/excel/",
        export_reports_excel,
        name="export_reports_excel"
    ),
        
    path('test-push/', views.test_push_view, name='test_push'),
    path(
        "get-technicians/",
        views.get_technicians,
        name="get-technicians",
    ),
]