from django.contrib import admin

from .models import Favorit, FotoKendaraan, Kendaraan, Merek, Pertanyaan, TukarTambah, JadwalKunjungan


@admin.register(Favorit)
class FavoritAdmin(admin.ModelAdmin):
    list_display = ("user", "kendaraan", "dibuat")
    search_fields = ("user__username", "kendaraan__judul")


@admin.register(Merek)
class MerekAdmin(admin.ModelAdmin):
    list_display = ("nama", "jenis")
    list_filter = ("jenis",)
    search_fields = ("nama",)


class FotoInline(admin.TabularInline):
    model = FotoKendaraan
    extra = 1


@admin.register(Kendaraan)
class KendaraanAdmin(admin.ModelAdmin):
    list_display = ("judul", "jenis", "merek", "tahun", "harga_rp", "kilometer", "status", "unggulan")
    list_filter = ("jenis", "status", "merek", "tahun", "unggulan")
    list_editable = ("status", "unggulan")
    search_fields = ("judul", "merek__nama", "warna", "plat_wilayah")
    prepopulated_fields = {"slug": ("judul", "tahun")}
    inlines = [FotoInline]
    date_hierarchy = "dibuat"

    @admin.display(description="Harga", ordering="harga")
    def harga_rp(self, obj):
        return obj.harga_rp


@admin.register(Pertanyaan)
class PertanyaanAdmin(admin.ModelAdmin):
    list_display = ("nama", "telepon", "kendaraan", "dibuat", "sudah_dibaca")
    list_filter = ("sudah_dibaca", "dibuat")
    list_editable = ("sudah_dibaca",)
    search_fields = ("nama", "telepon", "pesan", "kendaraan__judul")
    readonly_fields = ("kendaraan", "nama", "telepon", "pesan", "dibuat")

    def has_add_permission(self, request):
        return False

@admin.register(TukarTambah)
class TukarTambahAdmin(admin.ModelAdmin):
    list_display = ("nama", "telepon", "merek_model", "tahun", "kondisi", "nilai_taksiran", "status", "dibuat")
    list_filter = ("status", "jenis", "kondisi", "dibuat")
    list_editable = ("status", "nilai_taksiran")
    search_fields = ("nama", "telepon", "merek_model")
    readonly_fields = ("dibuat",)

@admin.register(JadwalKunjungan)
class JadwalKunjunganAdmin(admin.ModelAdmin):
    list_display = ("nama", "telepon", "kendaraan", "tanggal", "jam", "status", "dibuat")
    list_filter = ("status", "tanggal")
    list_editable = ("status",)
    search_fields = ("nama", "telepon", "kendaraan__judul")
    date_hierarchy = "tanggal"