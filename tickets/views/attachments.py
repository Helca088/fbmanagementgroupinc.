from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from ..models import TicketAttachment 
from django.http import Http404

def download_attachment(request, pk):
    attachment = get_object_or_404(TicketAttachment, pk=pk)

    if not attachment.file:
        raise Http404("No file")

    return redirect(attachment.file.url)