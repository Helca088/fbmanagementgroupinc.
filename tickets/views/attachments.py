from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404
from ..models import TicketAttachment 

def download_attachment(request, pk):
    attachment = TicketAttachment.objects.get(pk=pk)

    if not attachment.file:
        raise Http404("No file")

    response = FileResponse(attachment.file.open('rb'), as_attachment=True)

    response['Content-Disposition'] = f'attachment; filename="{attachment.file.name.split("/")[-1]}"'
    
    return response