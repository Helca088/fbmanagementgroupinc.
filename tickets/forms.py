from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import UserProfile, Outlet


class CustomUserCreationForm(UserCreationForm):
    outlet = forms.ModelChoiceField(
        queryset=Outlet.objects.all(),
        required=False,
    )

    is_staff = forms.BooleanField(required=False)
    is_superuser = forms.BooleanField(required=False)
    is_active = forms.BooleanField(required=False, initial=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "password1",
            "password2",
            "outlet",
            "is_staff",
            "is_superuser",
            "is_active",
        )

    def save(self, commit=True):
        print("===== FORM SAVE CALLED =====")
        print(self.cleaned_data)
        user = super().save(commit=False)

        user.is_staff = self.cleaned_data["is_staff"]
        user.is_superuser = self.cleaned_data["is_superuser"]
        user.is_active = self.cleaned_data["is_active"]

        if commit:
            user.save()

            UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    "outlet": self.cleaned_data["outlet"],
                },
            )

        return user