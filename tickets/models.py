from django.db import models
from django.contrib.auth.models import User

class Section(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

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
        ('resolved  ', 'Resolved'),       
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

    def __str__(self):
        return f'Ticket {self.id} - {self.title}'
# Create your models here.
