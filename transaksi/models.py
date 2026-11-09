from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.crypto import get_random_string

KARAKTER_KODE = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"


def buat_kode():
    """Kode unik seperti INV-20261025-K7M2P."""
    while True:
        kode = f"INV-{timezone.localdate():%Y%m%d}-{get_random_string(5, KARAKTER_KODE)}"
        if not Transaksi.objects.filter(kode=kode).exists():
            return kode


class Transaksi(models.Model):
    class Status(models.TextChoices):
        MENUNGGU = "menunggu", "Menunggu konfirmasi"
        DIKONFIRMASI = "dikonfirmasi", "Dikonfirmasi"
        SELESAI = "selesai", "Selesai"
        DIBATALKAN = "dibatalkan", "Dibatalkan"

    class Metode(models.TextChoices):
        TRANSFER = "transfer", "Transfer bank"
        TUNAI = "tunai", "Tunai (bayar di tempat)"

    kode = models.CharField(max_length=30, unique=True, editable=False)
    pembeli = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="transaksi")
    kendaraan = models.ForeignKey("katalog.Kendaraan", on_delete=models.PROTECT, related_name="transaksi")
    judul_kendaraan = models.CharField(max_length=200, help_text="Salinan nama unit saat transaksi dibuat")
    harga = models.PositiveBigIntegerField(help_text="Harga saat transaksi dibuat (Rp)")
    biaya_admin = models.PositiveBigIntegerField(default=0)
    metode = models.CharField(max_length=10, choices=Metode.choices, default=Metode.TRANSFER)
    status = models.CharField(max_length=15, choices=Status.choices, default=Status.MENUNGGU, db_index=True)

    nama_pembeli = models.CharField(max_length=100)
    telepon = models.CharField(max_length=20)
    alamat = models.TextField()
    catatan = models.TextField(blank=True)

    dibuat = models.DateTimeField(auto_now_add=True, db_index=True)
    diperbarui = models.DateTimeField(auto_now=True)
    dikonfirmasi_pada = models.DateTimeField(null=True, blank=True)
    selesai_pada = models.DateTimeField(null=True, blank=True)
    dibatalkan_pada = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-dibuat"]
        verbose_name = "Transaksi"
        verbose_name_plural = "Transaksi"

    def __str__(self):
        return f"{self.kode} - {self.judul_kendaraan}"

    def save(self, *args, **kwargs):
        if not self.kode:
            self.kode = buat_kode()
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("transaksi:detail", args=[self.kode])

    @property
    def total(self):
        return self.harga + self.biaya_admin

    @property
    def aktif(self):
        return self.status in (self.Status.MENUNGGU, self.Status.DIKONFIRMASI)

    @property
    def bisa_dibatalkan_pembeli(self):
        return self.status == self.Status.MENUNGGU

    @property
    def bisa_cetak_struk(self):
        return self.status in (self.Status.DIKONFIRMASI, self.Status.SELESAI)
