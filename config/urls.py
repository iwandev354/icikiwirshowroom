from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

admin.site.site_header = f"Admin {settings.NAMA_USAHA}"
admin.site.site_title = settings.NAMA_USAHA
admin.site.index_title = "Kelola kendaraan, merek, dan pertanyaan pembeli"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("akun.urls")),
    path("dasbor/", include("dasbor.urls")),
    path("transaksi/", include("transaksi.urls")),
    path("", include("katalog.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
