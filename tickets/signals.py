from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Ticket
from .views import notify_ticket_update

@receiver(post_save, sender=Ticket)
def ticket_saved(sender, instance, **kwargs):
    notify_ticket_update(instance)