import re
import datetime
from django import forms

from .models import Pertanyaan
from .models import TukarTambah
from .models import JadwalKunjungan


class PertanyaanForm(forms.ModelForm):
    class Meta:
        model = Pertanyaan
        fields = ["nama", "telepon", "pesan"]
        widgets = {
            "nama": forms.TextInput(attrs={"placeholder": "Nama Anda"}),
            "telepon": forms.TextInput(attrs={"placeholder": "No. WhatsApp, mis. 0812xxxxxxx", "inputmode": "tel"}),
            "pesan": forms.Textarea(attrs={"rows": 4, "placeholder": "Tulis pertanyaan atau tawaran Anda"}),
        }

    def clean_telepon(self):
        nomor = re.sub(r"[\s\-().]", "", self.cleaned_data["telepon"])
        if not re.fullmatch(r"\+?\d{9,15}", nomor):
            raise forms.ValidationError("Masukkan nomor telepon yang valid (9-15 digit).")
        return nomor

class TukarTambahForm(forms.ModelForm):
    class Meta:
        model = TukarTambah
        fields = [
            "nama", "telepon", "jenis", "merek_model", "tahun", "kilometer",
            "kondisi", "harga_harapan", "foto", "catatan", "kendaraan_tujuan",
        ]
        widgets = {"catatan": forms.Textarea(attrs={"rows": 3})}

class JadwalKunjunganForm(forms.ModelForm):
    class Meta:
        model = JadwalKunjungan
        fields = ["nama", "telepon", "tanggal", "jam", "catatan"]
        widgets = {
            "tanggal": forms.DateInput(attrs={"type": "date"}),
            "jam": forms.TimeInput(attrs={"type": "time", "min": "09:00", "max": "17:00"}),
        }

    def clean_tanggal(self):
        tanggal = self.cleaned_data["tanggal"]
        if tanggal < datetime.date.today():
            raise forms.ValidationError("Tanggal tidak boleh sudah lewat.")
        return tanggal

    def clean_jam(self):
        jam = self.cleaned_data["jam"]
        if not (datetime.time(9, 0) <= jam <= datetime.time(17, 0)):
            raise forms.ValidationError("Jam kunjungan antara 09.00 dan 17.00.")
        return jam

    def clean(self):
        data = super().clean()
        tanggal, jam = data.get("tanggal"), data.get("jam")
        if tanggal and jam:
            sekarang = datetime.datetime.now()
            if datetime.datetime.combine(tanggal, jam) < sekarang:
                self.add_error("jam", "Jam tersebut sudah lewat. Pilih jam yang masih akan datang.")
        return data