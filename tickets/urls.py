from django.urls import path

from. import views

urlpatterns = [ 
    path("", views.home, name="home"), 
    path("admin_dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path('login/', views.email_login, name='login'),
    path('ticket/<int:ticket_id>/pdf/', views.download_ticket, name='download_ticket'),
    path('ticket/<int:pk>/download/', views.download_attachment, name='ticket-download'),
    path('ticket/<int:id>/status/', views.update_status, name='update_status'),
    path('api/tickets/', views.ticket_api, name='ticket_api'),
    path('create/', views.create_ticket, name='create_ticket'),
    path('edit/<int:id>/', views.edit_ticket, name='edit_ticket'),
    path('delete-ticket/<int:id>/', views.delete_ticket, name='delete_ticket'),
    path("get-concerns/", views.get_concerns, name="get_concerns")
]