from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import UserProfile, Outlet, Department


class CustomUserCreationForm(UserCreationForm):

    departments = forms.ModelMultipleChoiceField(
        queryset=Department.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )

    outlet = forms.ModelChoiceField(
        queryset=Outlet.objects.all(),
        required=False,
    )

    account_type = forms.ChoiceField(
        choices=[
            ("admin", "Admin"),
            ("outlet", "Outlet"),
        ],
        initial="outlet",
    )

    is_superuser = forms.BooleanField(required=False)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "password1",
            "password2",
            "outlet",
            "departments",
            "account_type",
        )

    def save(self, commit=True):
        user = super().save(commit=False)

        user.is_superuser = self.cleaned_data["is_superuser"]

        if commit:
            user.save()

            profile, created = UserProfile.objects.update_or_create(
                user=user,
                defaults={
                    "outlet": self.cleaned_data["outlet"],
                    "account_type": self.cleaned_data["account_type"],
                },
            )

            profile.departments.set(
                self.cleaned_data["departments"]
            )

        return user