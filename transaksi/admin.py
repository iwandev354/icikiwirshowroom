from django.contrib import admin

from .models import Transaksi


@admin.register(Transaksi)
class TransaksiAdmin(admin.ModelAdmin):
    """Hanya-lihat. Perubahan status dilakukan lewat Dasbor Admin agar stok kendaraan tetap konsisten."""

    list_display = ("kode", "nama_pembeli", "judul_kendaraan", "total_rp", "metode", "status", "dibuat")
    list_filter = ("status", "metode")
    search_fields = ("kode", "nama_pembeli", "judul_kendaraan", "pembeli__username")
    date_hierarchy = "dibuat"

    @admin.display(description="Total")
    def total_rp(self, obj):
        return "Rp " + f"{obj.total:,}".replace(",", ".")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
