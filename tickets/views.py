from django.shortcuts import render, redirect, get_object_or_404
from .form import TicketForm
import os
from django.http import JsonResponse, HttpResponse, FileResponse, Http404
from reportlab.pdfgen import canvas
from .models import Section, Ticket, ConcernType
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.views.decorators.http import require_POST
from django.db.models import Q

@require_POST
def update_status(request, id):
    ticket = get_object_or_404(Ticket, id=id)
    new_status = request.POST.get("status")
    ticket.status = new_status
    ticket.save()

    notify_ticket_update(ticket, action="update")  

    return JsonResponse({"success": True, "status": ticket.status})

def notify_ticket_delete(ticket_id):
    print("Sending delete:", ticket_id)

    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        "tickets",
        {
            "type": "ticket_delete",
            "data": {
                "id": ticket_id
            }
        }
    )

def notify_ticket_update(ticket, action="create"):  
    print("🚀 SENDING EVENT:", ticket.id)

    channel_layer = get_channel_layer()

    async_to_sync(channel_layer.group_send)(
        "tickets",
        {
            "type": "ticket_update",
            "action": action,          
            "data": {
                "id": ticket.id,
                "title": ticket.title,
                "message": ticket.message,
                "user": ticket.user.username if ticket.user else "N/A",
                "section": ticket.section.name if ticket.section else "N/A",
                "concern_type": ticket.concern_type.name if ticket.concern_type else "N/A",
                "status": ticket.status,
                "created_at": ticket.created_at.strftime("%Y-%m-%d %H:%M"),
                "attachment": bool(ticket.attachment),
            }
        }
    )

def create_ticket(request):
    if request.method == "POST":
        form = TicketForm(request.POST, request.FILES)

        if form.is_valid():
            ticket = form.save()

            notify_ticket_update(ticket)

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

def ticket_api(request):
    tickets = Ticket.objects.all().order_by('-created_at')
    data = []
    for ticket in tickets:
        data.append({
            "id": ticket.id,
            "title": ticket.title,
            "message": ticket.message,
            "user": ticket.user.username if ticket.user else "N/A",
            "section": ticket.section.name if ticket.section else "N/A",
            "concern_type": ticket.concern_type.name if ticket.concern_type else "N/A",
            "status": ticket.status,
            "created_at": ticket.created_at.strftime("%Y-%m-%d %H:%M"),
            "attachment": bool(ticket.attachment),
        })
    return JsonResponse(data, safe=False)

def download_attachment(request, pk):
    ticket = Ticket.objects.get(pk=pk)

    if not ticket.attachment:
        raise Http404("No file")

    response = FileResponse(ticket.attachment.open('rb'), as_attachment=True)

    response['Content-Disposition'] = f'attachment; filename="{ticket.attachment.name.split("/")[-1]}"'
    
    return response

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

def email_login(request):

    if request.method == "POST":

        username = request.POST.get("user", "").strip()

        if not username:
            return render(request, "login.html", {
                "error": "Outlet name required"
            })

        user, created = User.objects.get_or_create(
            username=username
        )

        user.backend = "django.contrib.auth.backends.ModelBackend"
        login(request, user)

        return redirect("home")

    return render(request, "login.html")

@login_required
def home(request):

    if request.method == "POST":

        title = request.POST.get('title')
        message = request.POST.get('message')
        attachment = request.FILES.get('attachment')
        section_id = request.POST.get('section')
        section = Section.objects.get(id=section_id)
        concern_id = request.POST.get('concern_type')
        concern = ConcernType.objects.get(id=concern_id)    

        ticket = Ticket.objects.create(
            user=request.user,
            email=request.user.email,
            title=title,
            message=message,
            attachment=attachment,
            section=section,
            concern_type=concern
        )
        notify_ticket_update(ticket)
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


def admin_dashboard(request):

    tickets = Ticket.objects.all().order_by('-created_at')

    q = request.GET.get('q')

    if q:
        tickets = tickets.filter(
            Q(title__icontains=q) |
            Q(email__icontains=q) |
            Q(status__icontains=q) |
            Q(message__icontains=q) |
            Q(section__name__icontains=q) |
            Q(concern_type__name__icontains=q)|
            Q(user__username__icontains=q)
            )
        

    return render(request, 'admin.html', {
        'tickets': tickets,
        'total_tickets': tickets.count(),
        'open_tickets': tickets.filter(status='Open').count(),
        'resolved_tickets': tickets.filter(status='Resolved').count(),
    })
   