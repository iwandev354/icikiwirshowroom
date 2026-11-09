from django.conf import settings
from django.db import models


class Profil(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profil")
    telepon = models.CharField(max_length=20, blank=True)
    alamat = models.TextField(blank=True)

    class Meta:
        verbose_name = "Profil"
        verbose_name_plural = "Profil"

    def __str__(self):
        return f"Profil {self.user}"

    @classmethod
    def untuk(cls, user):
        """Ambil profil user; dibuat bila belum ada (mis. superuser lama)."""
        profil, _ = cls.objects.get_or_create(user=user)
        return profil
