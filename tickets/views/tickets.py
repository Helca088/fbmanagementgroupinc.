from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse, HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from tickets.models import (
    Ticket,
    TicketAttachment,
    Section,
    ConcernType,
    TicketStatusLog,
)
from tickets.form import TicketForm
from reportlab.pdfgen import canvas
from tickets.websocket import (
    notify_ticket_update,
    notify_ticket_delete,
)
import os

@login_required(login_url='login')
def home(request):


    if request.method == "POST":

        title = request.POST.get('title')
        message = request.POST.get('message')
        section_id = request.POST.get('section')
        section = Section.objects.get(id=section_id)
        concern_id = request.POST.get('concern_type')
        concern = ConcernType.objects.get(id=concern_id)    

        ticket = Ticket.objects.create(
              
            user=request.user,
            email=request.user.email,
            outlet=request.user.userprofile.outlet,
            message=message,
            section=section,
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
        
        return redirect('home')
    
    tickets = Ticket.objects.filter(
        user=request.user
    ).order_by('-created_at')

    sections = Section.objects.all()
    concerns = ConcernType.objects.all()

    return render(request, 'home.html', {
        'tickets': tickets,
        'sections': sections,
        'concerns': concerns
    })

def create_ticket(request):
    if request.method == "POST":
        form = TicketForm(request.POST, request.FILES)

        if form.is_valid():
            ticket = form.save()

            

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

def delete_ticket(request, id):

    ticket = get_object_or_404(Ticket, id=id)

    ticket_id = ticket.id
    ticket.delete()

    notify_ticket_delete(ticket_id)

    return redirect('admin_dashboard')

@require_POST
def update_status(request, id):
    ticket = get_object_or_404(Ticket, id=id)
    old_status = ticket.status
    new_status = request.POST.get("status")
    reason = request.POST.get ("reason", "")
    ticket.status = new_status
    ticket.save()

    TicketStatusLog.objects.create(
        ticket = ticket,
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