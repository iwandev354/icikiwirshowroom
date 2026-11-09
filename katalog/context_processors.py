from django.conf import settings
from django.utils.functional import SimpleLazyObject


def _favorit_ids(user):
    from .models import Favorit

    return set(Favorit.objects.filter(user=user).values_list("kendaraan_id", flat=True))


def situs(request):
    """Data umum untuk semua template: info usaha dan daftar id favorit pembeli."""
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated and not user.is_staff:
        favorit_ids = SimpleLazyObject(lambda: _favorit_ids(user))  # query hanya bila dipakai
    else:
        favorit_ids = frozenset()
    return {
        "NAMA_USAHA": settings.NAMA_USAHA,
        "WHATSAPP_NUMBER": settings.WHATSAPP_NUMBER,
        "INFO_REKENING": settings.INFO_REKENING,
        "favorit_ids": favorit_ids,
    }
