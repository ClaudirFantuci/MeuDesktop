from django.contrib import admin

from .models import ConfiguracaoIA, ConfiguracaoIAUsuario, ConsumoIA, RequisicaoIA


@admin.register(ConfiguracaoIA)
class ConfiguracaoIAAdmin(admin.ModelAdmin):
    """Admin da configuração global única de IA."""

    list_display = ("provedor", "modelo", "atualizado_em")

    def has_add_permission(self, request: object) -> bool:
        """Impede adicionar uma segunda configuração global."""
        return not getattr(ConfiguracaoIA, "objects").exists()  # pyright: ignore[reportPrivateUsage]


@admin.register(ConfiguracaoIAUsuario)
class ConfiguracaoIAUsuarioAdmin(admin.ModelAdmin):
    """Admin das configurações individuais de IA."""

    list_display = ("usuario", "ia_habilitada", "limite_mensal")
    list_filter = ("ia_habilitada",)
    search_fields = ("usuario__username", "usuario__email")


class SomenteLeituraIAAdmin(admin.ModelAdmin):
    """Base administrativa sem operações de escrita."""

    def get_readonly_fields(self, request: object, obj: object = None) -> tuple[str, ...]:
        """Torna todos os campos concretos somente leitura."""
        return tuple(field.name for field in self.model._meta.fields)  # pyright: ignore[reportPrivateUsage]

    def has_add_permission(self, request: object) -> bool:
        """Impede inclusão manual de registros de auditoria ou consumo."""
        return False

    def has_change_permission(self, request: object, obj: object = None) -> bool:
        """Impede edição manual de registros de auditoria ou consumo."""
        return False

    def has_delete_permission(self, request: object, obj: object = None) -> bool:
        """Impede exclusão manual de registros de auditoria ou consumo."""
        return False


@admin.register(RequisicaoIA)
class RequisicaoIAAdmin(SomenteLeituraIAAdmin):
    """Admin somente leitura das tentativas de IA."""

    list_display = (
        "criado_em",
        "usuario",
        "finalidade",
        "tentativa",
        "situacao",
        "tokens_total",
    )
    list_filter = ("situacao", "provedor", "origem")
    search_fields = ("finalidade", "modelo", "contexto_hash", "arquivo_hash")


@admin.register(ConsumoIA)
class ConsumoIAAdmin(SomenteLeituraIAAdmin):
    """Admin somente leitura dos consumos mensais."""

    list_display = ("dono", "mes", "tokens_total", "custo_estimado", "requisicoes")
    list_filter = ("mes",)
