import re

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import Profil

User = get_user_model()


def bersihkan_telepon(nilai):
    nomor = re.sub(r"[\s\-().]", "", nilai or "")
    if not re.fullmatch(r"\+?\d{9,15}", nomor):
        raise forms.ValidationError("Masukkan nomor telepon yang valid (9-15 digit).")
    return nomor


class DaftarForm(UserCreationForm):
    nama_lengkap = forms.CharField(label="Nama lengkap", max_length=100)
    email = forms.EmailField(label="Email")
    telepon = forms.CharField(label="No. telepon / WhatsApp", max_length=20)

    field_order = ["nama_lengkap", "username", "email", "telepon", "password1", "password2"]

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Email ini sudah terdaftar.")
        return email

    def clean_telepon(self):
        return bersihkan_telepon(self.cleaned_data["telepon"])

    def save(self, commit=True):
        user = super().save(commit=False)
        user.first_name = self.cleaned_data["nama_lengkap"]
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            Profil.objects.update_or_create(user=user, defaults={"telepon": self.cleaned_data["telepon"]})
        return user


class LoginPembeliForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if user.is_staff:
            raise forms.ValidationError(
                "Ini akun admin. Silakan masuk lewat halaman Login Admin.", code="bukan_pembeli"
            )


class LoginAdminForm(AuthenticationForm):
    def confirm_login_allowed(self, user):
        super().confirm_login_allowed(user)
        if not user.is_staff:
            raise forms.ValidationError("Akun ini bukan akun admin.", code="bukan_admin")


class ProfilForm(forms.Form):
    nama_lengkap = forms.CharField(label="Nama lengkap", max_length=100)
    email = forms.EmailField(label="Email")
    telepon = forms.CharField(label="No. telepon / WhatsApp", max_length=20, required=False)
    alamat = forms.CharField(label="Alamat", required=False, widget=forms.Textarea(attrs={"rows": 3}))

    def __init__(self, *args, user, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user

    def clean_email(self):
        email = self.cleaned_data["email"].strip()
        if User.objects.filter(email__iexact=email).exclude(pk=self.user.pk).exists():
            raise forms.ValidationError("Email ini sudah dipakai akun lain.")
        return email

    def clean_telepon(self):
        nilai = self.cleaned_data["telepon"]
        return bersihkan_telepon(nilai) if nilai else ""

    def simpan(self):
        d = self.cleaned_data
        self.user.first_name = d["nama_lengkap"]
        self.user.email = d["email"]
        self.user.save(update_fields=["first_name", "email"])
        profil = Profil.untuk(self.user)
        profil.telepon = d["telepon"]
        profil.alamat = d["alamat"]
        profil.save()
