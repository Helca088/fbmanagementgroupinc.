from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from ..models import TicketAttachment 
import cloudinary.utils

def download_attachment(request, pk):
    attachment = TicketAttachment.objects.get(pk=pk)

    url, _ = cloudinary.utils.cloudinary_url(
        attachment.file.public_id,
        resource_type="auto",
        flags="attachment"
    )

    return redirect(url)