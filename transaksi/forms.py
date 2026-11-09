from django import forms

from akun.forms import bersihkan_telepon

from .models import Transaksi


class CheckoutForm(forms.Form):
    nama = forms.CharField(label="Nama pembeli", max_length=100)
    telepon = forms.CharField(label="No. WhatsApp", max_length=20)
    alamat = forms.CharField(label="Alamat", widget=forms.Textarea(attrs={"rows": 3}))
    metode = forms.ChoiceField(
        label="Metode pembayaran",
        choices=Transaksi.Metode.choices,
        widget=forms.RadioSelect,
        initial=Transaksi.Metode.TRANSFER,
    )
    catatan = forms.CharField(label="Catatan (opsional)", required=False, widget=forms.Textarea(attrs={"rows": 2}))
    setuju = forms.BooleanField(
        label="Saya sudah memeriksa data kendaraan dan setuju memesan unit ini.",
        error_messages={"required": "Centang persetujuan untuk melanjutkan."},
    )

    def clean_telepon(self):
        return bersihkan_telepon(self.cleaned_data["telepon"])
