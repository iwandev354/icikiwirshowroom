from django.urls import path

from . import views

app_name = "transaksi"

urlpatterns = [
    path("", views.histori, name="histori"),
    path("beli/<slug:slug>/", views.beli, name="beli"),
    path("<str:kode>/", views.detail, name="detail"),
    path("<str:kode>/struk/", views.struk, name="struk"),
    path("<str:kode>/batal/", views.batal, name="batal"),
    path("<str:kode>/aksi/", views.aksi_admin, name="aksi"),
]
