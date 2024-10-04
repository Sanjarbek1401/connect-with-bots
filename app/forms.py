from django import forms
from django.contrib.auth.models import User
from .models import UserProfile
from django.core.exceptions import ValidationError


class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput)
    password_confirm = forms.CharField(widget=forms.PasswordInput, label='Parolni tasdiqlang')

    class Meta:
        model = User
        fields = ['username', 'email', 'password']

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError("Bu foydalanuvchi nomi allaqachon ro'yxatdan o'tgan.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("Bu email allaqon ro'yxatdan o'tgan.")
        return email

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get('password')
        password_confirm = cleaned_data.get('password_confirm')

        if password != password_confirm:
            raise ValidationError("Parollar mos kelmaydi.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['passport_series', 'passport_number']

    def clean_passport_series(self):
        passport_series = self.cleaned_data['passport_series']
        if not passport_series.isalpha() or len(passport_series) != 2:
            raise ValidationError("Passport seriyasi aniq 2 ta harfdan iborat bo'lishi kerak.")
        return passport_series

    def clean_passport_number(self):
        passport_number = self.cleaned_data['passport_number']
        if not passport_number.isdigit() or len(passport_number) != 7:
            raise ValidationError("Passport raqami aniq 7 ta raqamlardan iborat bo'lishi kerak.")
        return passport_number



