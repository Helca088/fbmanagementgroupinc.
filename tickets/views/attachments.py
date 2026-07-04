from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from ..models import TicketAttachment 
from django.shortcuts import get_object_or_404, redirect
import cloudinary.utils

def download_attachment(request, pk):
    attachment = get_object_or_404(TicketAttachment, pk=pk)

    return HttpResponse(f"""
    public_id: {attachment.file.public_id}<br>
    url: {attachment.file.url}<br>
    name: {attachment.file}<br>
    """)