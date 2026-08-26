from django.contrib import admin
from .models import (
	Armazenamento,
	Fabricante,
	Fonte,
	HistoricoMontagem,
	MemoriaRAM,
	Montagem,
	PlacaDeVideo,
	PlacaMae,
	Processador,
)

# Register your models here.


@admin.register(Fabricante)
class FabricanteAdmin(admin.ModelAdmin):
	list_display = ("nome", "website", "criado_em")
	search_fields = ("nome",)


@admin.register(Processador)
class ProcessadorAdmin(admin.ModelAdmin):
	list_display = ("nome", "fabricante", "socket", "preco", "disponivel")
	list_filter = ("socket", "disponivel", "fabricante")
	search_fields = ("nome", "geracao")


@admin.register(PlacaMae)
class PlacaMaeAdmin(admin.ModelAdmin):
	list_display = ("nome", "fabricante", "socket", "chipset", "preco", "disponivel")
	list_filter = ("socket", "tipo_memoria", "form_factor", "disponivel")
	search_fields = ("nome", "chipset")


@admin.register(MemoriaRAM)
class MemoriaRAMAdmin(admin.ModelAdmin):
	list_display = ("nome", "fabricante", "tipo", "capacidade_gb", "frequencia_mhz", "preco", "disponivel")
	list_filter = ("tipo", "disponivel", "fabricante")
	search_fields = ("nome", "latencia")


@admin.register(PlacaDeVideo)
class PlacaDeVideoAdmin(admin.ModelAdmin):
	list_display = ("nome", "fabricante", "gpu_chip", "memoria_gb", "preco", "disponivel")
	list_filter = ("disponivel", "fabricante")
	search_fields = ("nome", "gpu_chip")


@admin.register(Armazenamento)
class ArmazenamentoAdmin(admin.ModelAdmin):
	list_display = ("nome", "fabricante", "tipo", "interface", "capacidade_gb", "preco", "disponivel")
	list_filter = ("tipo", "interface", "disponivel", "fabricante")
	search_fields = ("nome",)


@admin.register(Fonte)
class FonteAdmin(admin.ModelAdmin):
	list_display = ("nome", "fabricante", "potencia_watts", "certificacao", "preco", "disponivel")
	list_filter = ("certificacao", "modular", "disponivel", "fabricante")
	search_fields = ("nome",)


class HistoricoMontagemInline(admin.TabularInline):
	model = HistoricoMontagem
	extra = 0
	readonly_fields = ("acao", "componente_tipo", "componente_nome", "data")
	can_delete = False


@admin.register(Montagem)
class MontagemAdmin(admin.ModelAdmin):
	list_display = ("nome", "usuario", "processador", "placa_mae", "finalizada", "data_atualizacao")
	list_filter = ("finalizada", "usuario")
	search_fields = ("nome",)
	inlines = [HistoricoMontagemInline]


@admin.register(HistoricoMontagem)
class HistoricoMontagemAdmin(admin.ModelAdmin):
	list_display = ("montagem", "acao", "componente_tipo", "componente_nome", "data")
	list_filter = ("acao",)
