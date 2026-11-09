from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import DaftarForm, LoginAdminForm, LoginPembeliForm, ProfilForm
from .models import Profil


class MasukPembeli(LoginView):
    template_name = "akun/masuk.html"
    authentication_form = LoginPembeliForm
    redirect_authenticated_user = True
    extra_context = {"peran": "pembeli", "judul": "Masuk sebagai Pembeli"}


class MasukAdmin(LoginView):
    template_name = "akun/masuk.html"
    authentication_form = LoginAdminForm
    # False agar pembeli yang sudah login tidak berputar-putar saat diarahkan ke halaman admin
    redirect_authenticated_user = False
    extra_context = {"peran": "admin", "judul": "Login Admin"}


def daftar(request):
    if request.user.is_authenticated:
        return redirect("dasbor:index")

    tujuan = request.POST.get("next") or request.GET.get("next", "")
    aman = url_has_allowed_host_and_scheme(tujuan, allowed_hosts={request.get_host()}, require_https=request.is_secure())

    form = DaftarForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Akun berhasil dibuat. Selamat datang!")
        return redirect(tujuan if (tujuan and aman) else "dasbor:index")

    return render(request, "akun/daftar.html", {"form": form, "next": tujuan if aman else ""})


@login_required
def profil(request):
    profil_obj = Profil.untuk(request.user)
    if request.method == "POST":
        form = ProfilForm(request.POST, user=request.user)
        if form.is_valid():
            form.simpan()
            messages.success(request, "Profil berhasil diperbarui.")
            return redirect("akun:profil")
    else:
        form = ProfilForm(
            user=request.user,
            initial={
                "nama_lengkap": request.user.first_name,
                "email": request.user.email,
                "telepon": profil_obj.telepon,
                "alamat": profil_obj.alamat,
            },
        )
    return render(request, "akun/profil.html", {"form": form})
