from django.db.models.signals import post_save
from django.dispatch import receiver
from .websocket import (
    notify_ticket_update,
    notify_ticket_delete,
)
from .models import Ticket

@receiver(post_save, sender=Ticket)
def ticket_saved(sender, instance, **kwargs):
    notify_ticket_update(instance)
    print("🔥 SIGNAL FIRED", instance.id)