from django.contrib import admin

from .models import Profil


@admin.register(Profil)
class ProfilAdmin(admin.ModelAdmin):
    list_display = ("user", "telepon")
    search_fields = ("user__username", "user__first_name", "telepon")
