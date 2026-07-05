from django.urls import path, include

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
    path(
    "reports/",
    views.reports,
    name="reports"
    ),
    path(
    "reports/export/pdf/",
    views.export_pdf,
    name="export_pdf"
    ),

    path(
    "reports/export/excel/",
    views.export_excel,
    name="export_excel"
    ),
]