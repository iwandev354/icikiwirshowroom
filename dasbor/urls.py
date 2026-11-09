from django.urls import path

from . import views

app_name = "dasbor"

urlpatterns = [
    path("", views.index, name="index"),
    path("pembeli/", views.pembeli, name="pembeli"),
    path("admin/", views.dasbor_admin, name="admin"),
    path("admin/transaksi/", views.admin_transaksi, name="admin_transaksi"),
]
