from django.shortcuts import render, redirect, get_object_or_404
from tickets.notification import send_push
from django.contrib.auth.models import User
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from tickets.models import (
    Ticket,
    TicketAttachment,
    Department,
    ConcernType,
    TicketStatusLog,
    Technician,
)
from tickets.form import TicketForm
from reportlab.pdfgen import canvas
from tickets.websocket import (
    notify_ticket_update,
    notify_ticket_delete,
)
import os
from datetime import timedelta
from django.utils import timezone
from django.db.models import Q

def get_technicians(request):
    department_id = request.GET.get("department")

    technicians = Technician.objects.filter(
        department_id=department_id
    )

    data = [
        {
            "id": tech.id,
            "name": tech.full_name,
        }
        for tech in technicians
    ]

    return JsonResponse(data, safe=False)

@login_required
def test_push_view(request):
    send_push(request.user, "Test Notification", "This is a real test push")
    return HttpResponse("Push attempted — check Render logs.")

@login_required(login_url='login')
def home(request):


    if request.method == "POST":

        title = request.POST.get('title')
        message = request.POST.get('message')
        department_id = request.POST.get('department')
        department = Department.objects.get(id=department_id)
        concern_id = request.POST.get('concern_type')
        concern = ConcernType.objects.get(id=concern_id)    

        ticket = Ticket.objects.create(
              
            user=request.user,
            created_by=request.user,
            email=request.user.email,
            outlet=request.user.userprofile.outlet,
            message=message,
            department=department,
            concern_type=concern
        )

        files = request.FILES.getlist('files')

        for f in files:
            TicketAttachment.objects.create(
                ticket=ticket,
                file=f
            )
        
        print("Sending WS for ticket", ticket.id)
        notify_ticket_update(ticket, action="create")
        admins = User.objects.filter(is_staff=True)

        print("Admins:", list(admins.values_list("username", flat=True)))
        print("Reached notification department")
        
        for admin in admins:
            print(f"Sending notification to {admin.username}")
            send_push(
        user=admin,
        title="New Ticket",
        body=f"{ticket.user.username} created Ticket #{ticket.id}",
        data={
            "url": "https://fbmanagement.onrender.com/admin/tickets/ticket/"
        }
    )
            
        return redirect('home')
    
    cutoff = timezone.now() - timedelta(days=7)

    tickets = (
        Ticket.objects.filter(
            outlet=request.user.userprofile.outlet
        )
        .filter(
            Q(status__iexact="resolved", resolve_at__gte=cutoff) |
            ~Q(status__iexact="resolved")
        )
        .order_by("-created_at")
    )

    departments = Department.objects.all()
    concerns = ConcernType.objects.all()

    return render(request, 'home.html', {
        'tickets': tickets,
        'departments': departments,
        'concerns': concerns
    })

def create_ticket(request):
    if request.method == "POST":
        form = TicketForm(request.POST, request.FILES)

        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.created_by = request.user
            ticket.save()
            form.save_m2m()

        if ticket.assigned_to:
         send_push(
        user=ticket.assigned_to.user,
        title="New Ticket Assigned",
        body=f"Ticket #{ticket.id} has been assigned to you.",
        data={
            "ticket_id": str(ticket.id),
            "url": f"/ticket/{ticket.id}/"
        }
    )
            

        return redirect('admin_dashboard')

    else:
        form = TicketForm()

    return render(request, 'create_ticket.html', {'form': form})

def edit_ticket(request, id):

    ticket = get_object_or_404(Ticket, id=id)

    if request.method == "POST":
        form = TicketForm(request.POST, request.FILES, instance=ticket)
        if form.is_valid():
            form.save()
            return redirect('admin_dashboard')

    else:
        form = TicketForm(instance=ticket)   

    return render(request, 'edit_ticket.html', {'form': form, 'ticket': ticket})

@require_POST
def delete_ticket(request, id):

    ticket = get_object_or_404(Ticket, id=id)

    notify_ticket_delete(ticket)

    ticket.delete()

    return JsonResponse({"success": True})

@login_required
@require_POST
def update_status(request, id):
    ticket = get_object_or_404(Ticket, id=id)
    old_status = ticket.status
    new_status = request.POST.get("status")
    reason = request.POST.get ("reason", "")
    ticket.status = new_status
    ticket.save()

    if ticket.user:
        send_push(
        user=ticket.user,
        title="Ticket Updated",
        body=f"Your ticket #{ticket.id} is now {ticket.status}.",
        data={
            "ticket_id": str(ticket.id),
            "url": f"/ticket/{ticket.id}/"
        }
    )
        
    TicketStatusLog.objects.create(
        ticket = ticket,
        created_by=request.user,
        old_status = old_status,
        new_status = new_status,
        technician = ticket.assigned_to,
        reasons = reason
    ) 

    return JsonResponse({"success": True, "status": ticket.status})

@require_POST
def update_priority(request, id):
    ticket = get_object_or_404(Ticket, id=id)

    priority = request.POST.get("priority")

    if priority not in ["Low", "Medium", "High"]:
        return JsonResponse({"error": "Invalid priority"}, status=400)

    ticket.priority = priority
    ticket.save()

    return JsonResponse({
        "id": ticket.id,
        "priority": ticket.priority
    })

def download_ticket(request, ticket_id):

    ticket = Ticket.objects.get(id=ticket_id)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="ticket_{ticket.id}.pdf"'

    p = canvas.Canvas(response)

    p.drawString(100, 800, f"Ticket ID: {ticket.id}")
    p.drawString(100, 780, f"Title: {ticket.title}")
    p.drawString(100, 760, f"Message: {ticket.message}")
    p.drawString(100, 740, f"Email: {ticket.email}")
    p.drawString(100, 720, f"Status: {ticket.status}")

    if ticket.attachment:
        filename = os.path.basename(ticket.attachment.path)
        p.drawString(
            100,
            680,
            f"Attachment: {filename}"
        )
    p.showPage()
    p.save()

    return response