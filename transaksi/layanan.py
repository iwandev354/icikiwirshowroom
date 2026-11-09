"""Logika bisnis transaksi.

Semua perubahan status dan stok kendaraan lewat modul ini, di dalam transaksi
database dengan penguncian baris (select_for_update) agar dua pembeli tidak
bisa memesan unit yang sama secara bersamaan.
"""
from django.conf import settings
from django.db import transaction
from django.utils import timezone

from katalog.models import Kendaraan

from .models import Transaksi


class TransaksiError(Exception):
    """Aksi tidak diizinkan; pesannya aman ditampilkan ke pengguna."""


def buat_transaksi(pembeli, kendaraan_id, data):
    with transaction.atomic():
        kendaraan = Kendaraan.objects.select_for_update().get(pk=kendaraan_id)
        if kendaraan.status != Kendaraan.Status.TERSEDIA:
            raise TransaksiError("Maaf, kendaraan ini sudah tidak tersedia (baru saja dipesan).")

        trx = Transaksi.objects.create(
            pembeli=pembeli,
            kendaraan=kendaraan,
            judul_kendaraan=f"{kendaraan.judul} ({kendaraan.tahun})",
            harga=kendaraan.harga,
            biaya_admin=settings.BIAYA_ADMIN,
            metode=data["metode"],
            nama_pembeli=data["nama"],
            telepon=data["telepon"],
            alamat=data["alamat"],
            catatan=data.get("catatan", ""),
        )
        kendaraan.status = Kendaraan.Status.DIPESAN
        kendaraan.save(update_fields=["status", "diperbarui"])
    return trx


def ubah_status(kode, aksi, oleh):
    """aksi: 'konfirmasi' | 'selesai' | 'batal'. `oleh` adalah user yang menjalankan.

    Raises Transaksi.DoesNotExist bila kode tidak ada, TransaksiError bila tidak diizinkan.
    """
    S = Transaksi.Status
    with transaction.atomic():
        trx = Transaksi.objects.select_for_update().select_related("kendaraan").get(kode=kode)
        kendaraan = trx.kendaraan
        sekarang = timezone.now()

        if aksi == "konfirmasi":
            if not oleh.is_staff:
                raise TransaksiError("Hanya admin yang dapat mengonfirmasi transaksi.")
            if trx.status != S.MENUNGGU:
                raise TransaksiError("Hanya transaksi berstatus 'Menunggu konfirmasi' yang dapat dikonfirmasi.")
            trx.status = S.DIKONFIRMASI
            trx.dikonfirmasi_pada = sekarang

        elif aksi == "selesai":
            if not oleh.is_staff:
                raise TransaksiError("Hanya admin yang dapat menyelesaikan transaksi.")
            if trx.status != S.DIKONFIRMASI:
                raise TransaksiError("Transaksi harus dikonfirmasi lebih dulu sebelum diselesaikan.")
            trx.status = S.SELESAI
            trx.selesai_pada = sekarang
            kendaraan.status = Kendaraan.Status.TERJUAL
            kendaraan.save(update_fields=["status", "diperbarui"])

        elif aksi == "batal":
            if oleh.is_staff:
                boleh = trx.aktif
            else:
                boleh = trx.pembeli_id == oleh.id and trx.bisa_dibatalkan_pembeli
            if not boleh:
                raise TransaksiError("Transaksi ini tidak dapat dibatalkan.")
            trx.status = S.DIBATALKAN
            trx.dibatalkan_pada = sekarang
            if kendaraan.status == Kendaraan.Status.DIPESAN:
                kendaraan.status = Kendaraan.Status.TERSEDIA
                kendaraan.save(update_fields=["status", "diperbarui"])

        else:
            raise TransaksiError("Aksi tidak dikenal.")

        trx.save()
    return trx
