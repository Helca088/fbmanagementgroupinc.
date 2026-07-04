from django.http import FileResponse, Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect
from ..models import TicketAttachment 
from django.shortcuts import get_object_or_404, redirect
import cloudinary.utils

def download_attachment(request, pk):
    attachment = get_object_or_404(TicketAttachment, pk=pk)

    url = attachment.file.url.replace(
        "/upload/",
        "/upload/fl_attachment/"
    )

    return redirect(url)