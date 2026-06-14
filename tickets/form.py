from django import forms
from .models import Ticket


class EmailLoginForm(forms.Form):
    email = forms.EmailField()
    
class TicketForm(forms.ModelForm):

    class Meta:
        model = Ticket
        fields = '__all__'
    
