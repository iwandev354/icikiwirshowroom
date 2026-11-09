from django.urls import path

from . import views

app_name = "katalog"

urlpatterns = [
    path("", views.beranda, name="beranda"),
    path("kendaraan/", views.daftar, name="daftar"),
    path("favorit/", views.favorit, name="favorit"),
    path("favorit/toggle/<int:kendaraan_id>/", views.favorit_toggle, name="favorit_toggle"),
    path("kendaraan/<slug:slug>/", views.detail, name="detail"),
    path("tukar-tambah/", views.tukar_tambah, name="tukar_tambah"),
    path("kendaraan/<slug:slug>/jadwal/", views.jadwal_kunjungan, name="jadwal"),
    path("jadwal-saya/", views.jadwal_saya, name="jadwal_saya"),
]
