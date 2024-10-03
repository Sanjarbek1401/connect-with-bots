from django import forms
from django.contrib.auth.models import User
from .models import UserProfile
from django.core.exceptions import ValidationError


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput, label='Confirm Password')

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password != password_confirm:
            raise ValidationError("Passwords do not match")

        return cleaned_data


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['passport_series', 'passport_number']

    def clean_passport_series(self):
        passport_series = self.cleaned_data['passport_series']
        if not passport_series.isalpha() or len(passport_series) != 2:
            raise ValidationError("Passport series must consist of exactly 2 letters.")
        return passport_series

    def clean_passport_number(self):
        passport_number = self.cleaned_data['passport_number']
        if not passport_number.isdigit() or len(passport_number) != 7:
            raise ValidationError("Passport number must consist of exactly 7 digits.")
        return passport_number
