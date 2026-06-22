from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from cloudinary.models import CloudinaryField


class Section(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    
class ConcernType(models.Model):

    section = models.ForeignKey( Section, on_delete=models.CASCADE, related_name='concerns')
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Ticket(models.Model):

    status_choices = [
    ('pending', 'Pending'),
    ('progress', 'In Progress'), 
    ('resolved', 'Resolved'),       
    ]     
    PRIORITY_CHOICES = [
    ('Low', 'Low'),
    ('Medium', 'Medium'),
    ('High', 'High'),   
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)   
    email = models.EmailField()
    title = models.CharField(max_length=100)
    message = models.TextField()
    status = models.CharField(max_length=20,choices=status_choices, default='pending')
    attachment = models.FileField(upload_to='tickets/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name="tickets", null=True, blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Medium')
    concern_type = models.ForeignKey(ConcernType, on_delete=models.SET_NULL, null=True, blank=True)
    scheduled_date = models.DateField(null=True, blank=True)
    scheduled_time = models.TimeField(null=True, blank=True)
    admin_note = models.TextField(blank=True, null=True)
    deadline = models.DateTimeField(null=True, blank=True)
    outlet = models.CharField(max_length=50)
    description = models.TextField()
    

    @property
    def is_overdue(self):
        if not self.deadline:
            return False
        
        if self.status == 'resolve':
            return False
        
        return timezone.now() > self.deadline

    def resolution_time(self):
        logs = self.status_logs.order_by('changed_at')

        start = None
        total = timezone.timedelta()

        for log in logs:
            if log.new_status == "resolved":
                start = log.changed_at

            if log.old_status == "resolved" and start:
                total += log.changed_at - start
                start = None

        return total

    @property
    def age(self):
        return timezone.now() - self.created_at


    @property
    def reopen_count(self):
        return self.status_logs.filter(
        old_status='resolved'
    ).count()


    @property
    def first_resolution_time(self):

        first_resolved = self.status_logs.filter(
        new_status='resolved'
    ).order_by('changed_at').first()

        if first_resolved:
         return first_resolved.changed_at - self.created_at

        return None
class TicketAttachment(models.Model):
        ticket = models.ForeignKey(
            Ticket,
            on_delete=models.CASCADE,
            related_name="attachments"
        )
        file = CloudinaryField('file', blank=True, null=True)

        def __str__(self):
            return f"Attachment {self.ticket.id}"
           
class TicketStatusLog(models.Model):
    ticket = models.ForeignKey(Ticket,on_delete=models.CASCADE,related_name="status_logs")
    old_status = models.CharField(max_length=20)
    new_status = models.CharField(max_length=20)
    changed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ticket.id}: {self.old_status} → {self.new_status}"        
# Create your models here.
