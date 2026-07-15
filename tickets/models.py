from django.db import models
from django.db.models import Max
from django.contrib.auth.models import User
from datetime import timedelta
from django.utils import timezone
from cloudinary.models import CloudinaryField

class DeviceToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.TextField(unique=True)
    created = models.DateTimeField(auto_now_add=True)

class Outlet(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class UserProfile(models.Model):
    ACCOUNT_TYPES = [
        ("admin", "Admin"),
        ("outlet", "Outlet"),
    ]
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    outlet = models.ForeignKey(
        Outlet,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    account_type = models.CharField(
        max_length=20,
        choices=ACCOUNT_TYPES,
        default="outlet",
    )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        if self.account_type == "admin":
            self.user.is_staff = True
            self.user.is_active = True
        else:  # Outlet
            self.user.is_staff = False
            self.user.is_active = True

        self.user.save(update_fields=["is_staff", "is_active"])

   
    
class Department(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class Technician(models.Model):

    department = models.ForeignKey( 
        Department, 
        on_delete=models.CASCADE, 
        related_name='technician',
        null=True,
        blank=True
        )
    
    full_name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.full_name

class ConcernType(models.Model):

    department = models.ForeignKey( 
        Department, 
        on_delete=models.CASCADE, 
        related_name='concerns'
        )
    name = models.CharField(max_length=100)

    deadline_days = models.PositiveIntegerField(default=3)

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

    is_opened = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)   
    email = models.EmailField()
    title = models.CharField(max_length=100)
    message = models.TextField(blank=False)
    status = models.CharField(max_length=20,choices=status_choices, default='pending')
    attachment = models.FileField(upload_to='tickets/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolve_at = models.DateTimeField(null=True, blank=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name="tickets", null=True, blank=True)
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='Medium')
    concern_type = models.ForeignKey(ConcernType, on_delete=models.SET_NULL, null=True, blank=True)
    scheduled_date = models.DateField(null=True, blank=True)
    scheduled_time = models.TimeField(null=True, blank=True)
    admin_note = models.TextField(blank=True, null=True)
    deadline = models.DateTimeField(null=True, blank=True)
    outlet = models.ForeignKey( 
    Outlet,
    on_delete=models.SET_NULL,
    null=True,
    blank=True,)
    outlet_ticket_no = models.PositiveIntegerField(
        editable=False,
        null=True,
        blank=True
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_tickets"
    )
    description = models.TextField()
    assigned_to = models.ForeignKey(
        Technician,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
        )

    def ticket_age(self):

        seconds = int(self.age.total_seconds())

        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        minutes = (seconds % 3600) // 60

        return f"{days}d {hours}h {minutes}m"

    def save(self, *args, **kwargs):

    # Set deadline automatically
        if self.concern_type and not self.deadline:
            self.deadline = (
            timezone.now() +
            timedelta(days=self.concern_type.deadline_days)
        )

    # Assign outlet ticket number only when creating a new ticket
        if self._state.adding and self.outlet and not self.outlet_ticket_no:

            last_number = (
            Ticket.objects
            .filter(outlet=self.outlet)
            .aggregate(Max("outlet_ticket_no"))
            ["outlet_ticket_no__max"]
        )

            self.outlet_ticket_no = (last_number or 0) + 1

        # Set resolved timestamp # new
        if self.status.lower() == "resolved":
            if self.resolve_at is None:
                self.resolve_at = timezone.now()
        else:
            # Clear it if the ticket is reopened
            self.resolve_at = None

        super().save(*args, **kwargs)

    def __str__(self):
        if self.outlet:
            return f"{self.outlet.name} ({self.outlet_ticket_no})"
        return f"Ticket ({self.id})"

    @property
    def is_overdue(self):
        if not self.deadline:
            return False
        
        if self.status == "resolved":
            if self.resolve_at:
                return self.resolve_at > self.deadline
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
        file = CloudinaryField("file")
        original_filename = models.CharField(max_length=255, blank=True)

        def __str__(self):
            return f"Attachment {self.ticket.id}"    
           
class TicketStatusLog(models.Model):
    ticket = models.ForeignKey(Ticket,on_delete=models.CASCADE,related_name="status_logs")
    old_status = models.CharField(max_length=20)
    technician = models.ForeignKey(
        Technician,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    reasons = models.TextField()
    new_status = models.CharField(max_length=20)
    changed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.ticket.id}: {self.old_status} → {self.new_status}" 

class TicketAssignmentLog(models.Model):
    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name="assignment_logs"
    )       

    old_technician = models.ForeignKey(
        Technician,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="old_assignment_logs"
    )

    new_technician = models.ForeignKey(
        Technician,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="new_assignment_logs"
    )

    reason = models.TextField(blank=True)

    assigned_at = models.DateTimeField (auto_now_add=True)

    def __str__(self):
        old = self.old_technician.full_name if self.old_technician else "None"
        new = self.new_technician.full_name if self.new_technician else "None"
        return f"Ticket {self.ticket.id}: {old} → {new}"