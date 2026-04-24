from django.contrib import admin
from .models import Fabricante

# Register your models here.


@admin.register(Fabricante)
class FabricanteAdmin(admin.ModelAdmin):
	list_display = ("nome", "website", "criado_em")
	search_fields = ("nome",)
