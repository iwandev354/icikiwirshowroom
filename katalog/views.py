from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .forms import JadwalKunjunganForm, PertanyaanForm, TukarTambahForm
from .models import Favorit, Jenis, JadwalKunjungan, Kendaraan, Merek

URUTAN = {
    "terbaru": ("-dibuat", "Terbaru"),
    "termurah": ("harga", "Harga termurah"),
    "termahal": ("-harga", "Harga termahal"),
    "tahun": ("-tahun", "Tahun terbaru"),
    "km": ("kilometer", "Kilometer terendah"),
}


def _int_atau_none(nilai):
    try:
        return int(nilai)
    except (TypeError, ValueError):
        return None


def beranda(request):
    unggulan = (
        Kendaraan.objects.select_related("merek")
        .filter(unggulan=True)
        .exclude(status=Kendaraan.Status.TERJUAL)[:6]
    )
    terbaru = (
        Kendaraan.objects.select_related("merek")
        .exclude(status=Kendaraan.Status.TERJUAL)[:8]
    )
    jumlah = {
        "motor": Kendaraan.objects.filter(jenis=Jenis.MOTOR, status=Kendaraan.Status.TERSEDIA).count(),
        "mobil": Kendaraan.objects.filter(jenis=Jenis.MOBIL, status=Kendaraan.Status.TERSEDIA).count(),
    }
    return render(request, "katalog/beranda.html", {"unggulan": unggulan, "terbaru": terbaru, "jumlah": jumlah})


def daftar(request):
    qs = Kendaraan.objects.select_related("merek")
    g = request.GET

    jenis = g.get("jenis", "")
    if jenis in Jenis.values:
        qs = qs.filter(jenis=jenis)

    merek_id = _int_atau_none(g.get("merek"))
    if merek_id:
        qs = qs.filter(merek_id=merek_id)

    q = g.get("q", "").strip()
    if q:
        qs = qs.filter(Q(judul__icontains=q) | Q(merek__nama__icontains=q) | Q(warna__icontains=q))

    for param, lookup in (
        ("tahun_min", "tahun__gte"),
        ("tahun_max", "tahun__lte"),
        ("harga_min", "harga__gte"),
        ("harga_max", "harga__lte"),
    ):
        nilai = _int_atau_none(g.get(param))
        if nilai is not None:
            qs = qs.filter(**{lookup: nilai})

    transmisi = g.get("transmisi", "")
    if transmisi in Kendaraan.Transmisi.values:
        qs = qs.filter(transmisi=transmisi)

    if not g.get("semua"):
        qs = qs.exclude(status=Kendaraan.Status.TERJUAL)

    urut = g.get("urut", "terbaru")
    if urut not in URUTAN:
        urut = "terbaru"
    qs = qs.order_by(URUTAN[urut][0], "-id")

    halaman = Paginator(qs, 12).get_page(g.get("page"))

    merek_qs = Merek.objects.all()
    if jenis in Jenis.values:
        merek_qs = merek_qs.filter(jenis=jenis)

    # Query string tanpa 'page' untuk tautan paginasi
    params = g.copy()
    params.pop("page", None)

    context = {
        "halaman": halaman,
        "merek_list": merek_qs,
        "urutan": [(k, v[1]) for k, v in URUTAN.items()],
        "filter": {
            "jenis": jenis, "merek": merek_id, "q": q, "urut": urut, "transmisi": transmisi,
            "tahun_min": g.get("tahun_min", ""), "tahun_max": g.get("tahun_max", ""),
            "harga_min": g.get("harga_min", ""), "harga_max": g.get("harga_max", ""),
        },
        "jenis_pilihan": Jenis.choices,
        "transmisi_pilihan": Kendaraan.Transmisi.choices,
        "querystring": params.urlencode(),
    }
    return render(request, "katalog/daftar.html", context)


def detail(request, slug):
    kendaraan = get_object_or_404(
        Kendaraan.objects.select_related("merek").prefetch_related("foto"), slug=slug
    )

    if request.method == "POST":
        form = PertanyaanForm(request.POST)
        if form.is_valid():
            pertanyaan = form.save(commit=False)
            pertanyaan.kendaraan = kendaraan
            pertanyaan.save()
            messages.success(request, "Terima kasih! Pertanyaan Anda sudah terkirim, kami akan segera menghubungi Anda.")
            return redirect(kendaraan.get_absolute_url() + "#kontak")
    else:
        form = PertanyaanForm()

    mirip = (
        Kendaraan.objects.select_related("merek")
        .filter(jenis=kendaraan.jenis)
        .exclude(pk=kendaraan.pk)
        .exclude(status=Kendaraan.Status.TERJUAL)
        .order_by("-dibuat")[:4]
    )
    return render(request, "katalog/detail.html", {"k": kendaraan, "form": form, "mirip": mirip})


@login_required
def favorit(request):
    if request.user.is_staff:
        messages.info(request, "Akun admin tidak memiliki daftar favorit.")
        return redirect("dasbor:index")
    daftar_favorit = Favorit.objects.filter(user=request.user).select_related("kendaraan__merek")
    return render(request, "katalog/favorit.html", {"daftar_favorit": daftar_favorit})


@login_required
@require_POST
def favorit_toggle(request, kendaraan_id):
    kendaraan = get_object_or_404(Kendaraan, pk=kendaraan_id)
    if request.user.is_staff:
        messages.error(request, "Akun admin tidak memiliki daftar favorit.")
    else:
        obj, dibuat = Favorit.objects.get_or_create(user=request.user, kendaraan=kendaraan)
        if dibuat:
            messages.success(request, f"{kendaraan.judul} ditambahkan ke favorit.")
        else:
            obj.delete()
            messages.info(request, f"{kendaraan.judul} dihapus dari favorit.")

    tujuan = request.POST.get("next", "")
    if not url_has_allowed_host_and_scheme(tujuan, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        tujuan = kendaraan.get_absolute_url()
    return redirect(tujuan)

def tukar_tambah(request):
    if request.method == "POST":
        form = TukarTambahForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "Pengajuan tukar tambah terkirim! Kami akan menghubungi Anda untuk penaksiran.")
            return redirect("katalog:tukar_tambah")
    else:
        form = TukarTambahForm()
    return render(request, "katalog/tukar_tambah.html", {"form": form})

def jadwal_kunjungan(request, slug):
    kendaraan = get_object_or_404(Kendaraan, slug=slug)
    if request.method == "POST":
        form = JadwalKunjunganForm(request.POST)
        if form.is_valid():
            jadwal = form.save(commit=False)
            jadwal.kendaraan = kendaraan
            if request.user.is_authenticated:
                jadwal.user = request.user
            jadwal.save()
            messages.success(request, "Jadwal kunjungan terkirim! Kami akan mengonfirmasi lewat telepon.")
            return redirect(kendaraan.get_absolute_url())
    else:
        form = JadwalKunjunganForm()
    return render(request, "katalog/jadwal.html", {"k": kendaraan, "form": form})

@login_required
def jadwal_saya(request):
    daftar_jadwal = (
        JadwalKunjungan.objects.filter(user=request.user)
        .select_related("kendaraan")
        .order_by("-tanggal", "-jam")
    )
    return render(request, "katalog/jadwal_saya.html", {"daftar_jadwal": daftar_jadwal})