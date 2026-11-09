from django.contrib.auth.views import LogoutView
from django.urls import path

from . import views

app_name = "akun"

urlpatterns = [
    path("masuk/", views.MasukPembeli.as_view(), name="masuk"),
    path("admin-masuk/", views.MasukAdmin.as_view(), name="masuk_admin"),
    path("daftar/", views.daftar, name="daftar"),
    path("keluar/", LogoutView.as_view(), name="keluar"),
    path("profil/", views.profil, name="profil"),
]
