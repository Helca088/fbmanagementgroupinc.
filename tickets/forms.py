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
        choices=UserProfile.ACCOUNT_TYPES,
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
        )

    def _save_profile(self, user):
        profile, _ = UserProfile.objects.update_or_create(
            user=user,
            defaults={
                "outlet": self.cleaned_data.get("outlet"),
                "account_type": self.cleaned_data.get("account_type", "outlet"),
            },
        )
        profile.departments.set(self.cleaned_data.get("departments") or [])

    def _save_m2m(self):
        # Runs after the user row exists, in both admin and normal usage.
        super()._save_m2m()
        self._save_profile(self.instance)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_superuser = self.cleaned_data.get("is_superuser", False)

        if commit:
            user.save()
            self.save_m2m()

        return user