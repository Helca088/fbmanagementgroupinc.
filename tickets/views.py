from django.shortcuts import render, redirect, get_object_or_404
from .form import TicketForm
import os
from django.http import JsonResponse, HttpResponse, FileResponse, Http404
from reportlab.pdfgen import canvas
from .models import Section, Ticket, ConcernType, TicketStatusLog, TicketAttachment
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.views.decorators.http import require_POST
from django.db.models import Q
from django.db.models import Case, When, IntegerField
from django.template.loader import get_template
from .websocket import (
    notify_ticket_update,
    notify_ticket_delete,
)

def test_template(request):
    t = get_template("admin/base_site.html")
    return HttpResponse(str(t.origin))

def get_concerns(request):

    section_id = request.GET.get("section")

    concerns = ConcernType.objects.filter(section_id=section_id)

    return render(
     request, "partials/concern_options.html",
     {
         "concerns": concerns
     }
 )   
@require_POST
def update_status(request, id):
    ticket = get_object_or_404(Ticket, id=id)
    old_status = ticket.status
    new_status = request.POST.get("status")
    ticket.status = new_status
    ticket.save()

    TicketStatusLog.objects.create(
        ticket = ticket,
        old_status = old_status,
        new_status = new_status
    ) 

    return JsonResponse({"success": True, "status": ticket.status})

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

def ticket_api(request):
    tickets = Ticket.objects.annotate(
    status_order=Case(
        When(status='Pending', then=0),
        When(status='Open', then=1),
        When(status='Resolved', then=2),
        default=99,
        output_field=IntegerField(),
    )
).order_by('status_order', '-created_at')
    data = []
    for ticket in tickets:

        attachments = [
            request.build_absolute_uri(a.file.url)
            for a in ticket.attachments.all()
        ]
        data.append({
            "id": ticket.id,
            "title": ticket.title,
            "message": ticket.message,
            "user": ticket.user.username if ticket.user else "N/A",
            "section": ticket.section.name if ticket.section else "N/A",
            "concern_type": ticket.concern_type.name if ticket.concern_type else "N/A",
            "status": ticket.status,
            "created_at": ticket.created_at.strftime("%Y-%m-%d %H:%M"),
            "attachments": attachments,
            "scheduled_date": ticket.scheduled_date.strftime("%Y-%m-%d") if ticket.scheduled_date else "",
            "scheduled_time": ticket.scheduled_time.strftime("%H:%M") if ticket.scheduled_time else "",
            "admin_note": ticket.admin_note or "",
            "deadline": (ticket.deadline.strftime("%Y-%m-%d %H:%M")if ticket.deadline else ""),
            "is_overdue": ticket.is_overdue,  
        })
    return JsonResponse(data, safe=False)

def download_attachment(request, pk):
    attachment = TicketAttachment.objects.get(pk=pk)

    if not attachment.file:
        raise Http404("No file")

    response = FileResponse(attachment.file.open('rb'), as_attachment=True)

    response['Content-Disposition'] = f'attachment; filename="{attachment.file.name.split("/")[-1]}"'
    
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

        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "").strip()

        if not username or not password:
            return render(request, "login.html", {
                "error": "Username and password required"
            })

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return redirect("home")

        return render(request, "login.html", {
            "error": "Invalid username or password"
        })

    return render(request, "login.html")

@require_POST
def logout_view(request):
        
        print("LOGGING OUT USER:", request.user)
        logout(request)
        return redirect('login')

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
            outlet=request.user.username,
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

    tickets = Ticket.objects.annotate(
    status_order=Case(
        When(status='Pending', then=0),
        When(status='Open', then=1),
        When(status='Resolved', then=2),
        default=99,
        output_field=IntegerField(),
    )
).order_by('status_order', '-created_at')

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
   