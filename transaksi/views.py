from django.conf import settings
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import F, Q, Sum
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from akun.models import Profil
from katalog.models import Kendaraan

from . import layanan
from .forms import CheckoutForm
from .models import Transaksi

PESAN_SUKSES = {
    "konfirmasi": "Transaksi {kode} dikonfirmasi.",
    "selesai": "Transaksi {kode} ditandai selesai. Kendaraan kini berstatus terjual.",
    "batal": "Transaksi {kode} dibatalkan. Kendaraan tersedia kembali.",
}


def _tujuan_aman(request, fallback):
    tujuan = request.POST.get("next", "")
    if tujuan and url_has_allowed_host_and_scheme(tujuan, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return tujuan
    return fallback


def _ambil_milik(request, kode):
    """Transaksi hanya boleh dilihat pemiliknya atau admin; selain itu 404."""
    trx = get_object_or_404(Transaksi.objects.select_related("kendaraan__merek", "pembeli"), kode=kode)
    if not (request.user.is_staff or trx.pembeli_id == request.user.id):
        raise Http404
    return trx


@login_required
def beli(request, slug):
    kendaraan = get_object_or_404(Kendaraan.objects.select_related("merek"), slug=slug)

    if request.user.is_staff:
        messages.error(request, "Akun admin tidak dapat membeli kendaraan. Gunakan akun pembeli.")
        return redirect(kendaraan)
    if not kendaraan.tersedia:
        messages.error(request, "Maaf, kendaraan ini sudah tidak tersedia.")
        return redirect(kendaraan)

    profil = Profil.untuk(request.user)

    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            try:
                trx = layanan.buat_transaksi(request.user, kendaraan.pk, form.cleaned_data)
            except layanan.TransaksiError as e:
                messages.error(request, str(e))
                return redirect(kendaraan)

            # Simpan telepon/alamat ke profil bila belum terisi, agar pesanan berikutnya otomatis terisi
            ubah = []
            if not profil.telepon:
                profil.telepon = form.cleaned_data["telepon"]
                ubah.append("telepon")
            if not profil.alamat:
                profil.alamat = form.cleaned_data["alamat"]
                ubah.append("alamat")
            if ubah:
                profil.save(update_fields=ubah)

            messages.success(request, "Pesanan berhasil dibuat. Menunggu konfirmasi dari penjual.")
            return redirect("transaksi:detail", kode=trx.kode)
    else:
        form = CheckoutForm(
            initial={
                "nama": request.user.get_full_name() or request.user.username,
                "telepon": profil.telepon,
                "alamat": profil.alamat,
            }
        )

    return render(
        request,
        "transaksi/beli.html",
        {"k": kendaraan, "form": form, "biaya_admin": settings.BIAYA_ADMIN, "total": kendaraan.harga + settings.BIAYA_ADMIN},
    )


@login_required
def histori(request):
    if request.user.is_staff:
        return redirect("dasbor:admin_transaksi")

    semua = Transaksi.objects.filter(pembeli=request.user)
    qs = semua.select_related("kendaraan")

    status = request.GET.get("status", "")
    if status in Transaksi.Status.values:
        qs = qs.filter(status=status)

    total_belanja = (
        semua.filter(status=Transaksi.Status.SELESAI).aggregate(t=Sum(F("harga") + F("biaya_admin")))["t"] or 0
    )
    halaman = Paginator(qs, 10).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)

    return render(
        request,
        "transaksi/histori.html",
        {
            "halaman": halaman,
            "status_aktif": status,
            "status_pilihan": Transaksi.Status.choices,
            "total_belanja": total_belanja,
            "jumlah": semua.count(),
            "querystring": params.urlencode(),
        },
    )


@login_required
def detail(request, kode):
    return render(request, "transaksi/detail.html", {"t": _ambil_milik(request, kode)})


@login_required
def struk(request, kode):
    trx = _ambil_milik(request, kode)
    if not trx.bisa_cetak_struk:
        messages.info(request, "Struk tersedia setelah transaksi dikonfirmasi oleh penjual.")
        return redirect(trx)
    return render(request, "transaksi/struk.html", {"t": trx})


def _jalankan_aksi(request, kode, aksi):
    try:
        trx = layanan.ubah_status(kode, aksi, request.user)
    except Transaksi.DoesNotExist:
        raise Http404
    except layanan.TransaksiError as e:
        messages.error(request, str(e))
        return None
    messages.success(request, PESAN_SUKSES[aksi].format(kode=trx.kode))
    return trx


@login_required
@require_POST
def batal(request, kode):
    """Pembeli membatalkan pesanannya sendiri (selama masih menunggu konfirmasi)."""
    get_object_or_404(Transaksi, kode=kode, pembeli=request.user)
    _jalankan_aksi(request, kode, "batal")
    return redirect("transaksi:detail", kode=kode)


@staff_member_required(login_url="akun:masuk_admin")
@require_POST
def aksi_admin(request, kode):
    """Admin: konfirmasi / selesai / batal."""
    _jalankan_aksi(request, kode, request.POST.get("aksi", ""))
    return redirect(_tujuan_aman(request, fallback=Transaksi(kode=kode).get_absolute_url()))
