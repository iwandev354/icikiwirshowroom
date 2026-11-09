from datetime import date

from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, F, Q, Sum
from django.db.models.functions import TruncMonth
from django.shortcuts import redirect, render
from django.utils import timezone

from katalog.models import Favorit, Jenis, Kendaraan, Pertanyaan
from transaksi.models import Transaksi

BULAN = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]
S = Transaksi.Status
NILAI = Sum(F("harga") + F("biaya_admin"))  # total = harga + biaya admin


def _ringkas(n):
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f}".replace(".", ",") + " M"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.0f} jt"
    if n >= 1_000:
        return f"{n / 1_000:.0f} rb"
    return str(n)


@login_required
def index(request):
    """Arahkan ke dasbor sesuai peran."""
    return redirect("dasbor:admin" if request.user.is_staff else "dasbor:pembeli")


@login_required
def pembeli(request):
    if request.user.is_staff:
        return redirect("dasbor:admin")

    trx = Transaksi.objects.filter(pembeli=request.user)
    ringkasan = trx.aggregate(
        menunggu=Count("id", filter=Q(status=S.MENUNGGU)),
        dikonfirmasi=Count("id", filter=Q(status=S.DIKONFIRMASI)),
        selesai=Count("id", filter=Q(status=S.SELESAI)),
        belanja=Sum(F("harga") + F("biaya_admin"), filter=Q(status=S.SELESAI)),
    )
    favorit_qs = Favorit.objects.filter(user=request.user)

    return render(
        request,
        "dasbor/pembeli.html",
        {
            "ringkasan": ringkasan,
            "belanja": ringkasan["belanja"] or 0,
            "jumlah_favorit": favorit_qs.count(),
            "transaksi_terbaru": trx.select_related("kendaraan")[:5],
            "favorit_terbaru": favorit_qs.select_related("kendaraan__merek")[:4],
        },
    )


def _grafik_penjualan(bulan_terakhir=6):
    """Penjualan (transaksi selesai) per bulan untuk `bulan_terakhir` bulan terakhir."""
    hari_ini = timezone.localdate()
    daftar = []
    y, m = hari_ini.year, hari_ini.month
    for i in range(bulan_terakhir - 1, -1, -1):
        mm, yy = m - i, y
        while mm <= 0:
            mm += 12
            yy -= 1
        daftar.append((yy, mm))

    baris = (
        Transaksi.objects.filter(status=S.SELESAI, selesai_pada__date__gte=date(daftar[0][0], daftar[0][1], 1))
        .annotate(bulan=TruncMonth("selesai_pada"))
        .values("bulan")
        .annotate(nilai=NILAI, jumlah=Count("id"))
    )
    peta = {(b["bulan"].year, b["bulan"].month): b for b in baris}

    data = []
    for yy, mm in daftar:
        b = peta.get((yy, mm))
        nilai = int(b["nilai"]) if b else 0
        data.append({"label": BULAN[mm - 1], "nilai": nilai, "jumlah": b["jumlah"] if b else 0, "teks": _ringkas(nilai)})

    maks = max((d["nilai"] for d in data), default=0) or 1
    for d in data:
        d["persen"] = max(round(d["nilai"] / maks * 100), 3) if d["nilai"] else 0
    return data


@staff_member_required(login_url="akun:masuk_admin")
def dasbor_admin(request):
    stok = Kendaraan.objects.aggregate(
        tersedia=Count("id", filter=Q(status=Kendaraan.Status.TERSEDIA)),
        dipesan=Count("id", filter=Q(status=Kendaraan.Status.DIPESAN)),
        terjual=Count("id", filter=Q(status=Kendaraan.Status.TERJUAL)),
        motor=Count("id", filter=Q(jenis=Jenis.MOTOR, status=Kendaraan.Status.TERSEDIA)),
        mobil=Count("id", filter=Q(jenis=Jenis.MOBIL, status=Kendaraan.Status.TERSEDIA)),
    )
    trx = Transaksi.objects.aggregate(
        menunggu=Count("id", filter=Q(status=S.MENUNGGU)),
        dikonfirmasi=Count("id", filter=Q(status=S.DIKONFIRMASI)),
        selesai=Count("id", filter=Q(status=S.SELESAI)),
        pendapatan=Sum(F("harga") + F("biaya_admin"), filter=Q(status=S.SELESAI)),
    )
    grafik = _grafik_penjualan()

    return render(
        request,
        "dasbor/admin.html",
        {
            "stok": stok,
            "trx": trx,
            "pendapatan": trx["pendapatan"] or 0,
            "bulan_ini": grafik[-1],
            "grafik": grafik,
            "jumlah_pembeli": get_user_model().objects.filter(is_staff=False, is_active=True).count(),
            "perlu_tindakan": Transaksi.objects.filter(status__in=[S.MENUNGGU, S.DIKONFIRMASI])
            .select_related("kendaraan")
            .order_by("dibuat")[:8],
            "pertanyaan_baru": Pertanyaan.objects.filter(sudah_dibaca=False).count(),
            "pertanyaan_terbaru": Pertanyaan.objects.select_related("kendaraan")[:5],
        },
    )


@staff_member_required(login_url="akun:masuk_admin")
def admin_transaksi(request):
    qs = Transaksi.objects.select_related("kendaraan", "pembeli")

    status = request.GET.get("status", "")
    if status in Transaksi.Status.values:
        qs = qs.filter(status=status)

    q = request.GET.get("q", "").strip()
    if q:
        qs = qs.filter(
            Q(kode__icontains=q)
            | Q(nama_pembeli__icontains=q)
            | Q(judul_kendaraan__icontains=q)
            | Q(pembeli__username__icontains=q)
        )

    halaman = Paginator(qs, 20).get_page(request.GET.get("page"))
    params = request.GET.copy()
    params.pop("page", None)

    return render(
        request,
        "dasbor/admin_transaksi.html",
        {
            "halaman": halaman,
            "status_aktif": status,
            "q": q,
            "status_pilihan": Transaksi.Status.choices,
            "querystring": params.urlencode(),
        },
    )
