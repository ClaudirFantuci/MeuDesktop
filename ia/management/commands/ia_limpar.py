"""Remove auditorias de IA fora do prazo de retenção."""

from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from ia.models import ConfiguracaoIA, RequisicaoIA


class Command(BaseCommand):
    """Apaga RequisicaoIA antigas em lotes, sem alterar ConsumoIA."""

    help = "Remove requisições de IA mais antigas que o prazo configurado."
    batch_size = 1000

    def handle(self, *args: object, **options: object) -> str:
        configuracao = ConfiguracaoIA.obter()
        limite = timezone.now() - timedelta(days=configuracao.reter_requisicoes_dias)
        total = 0

        while True:
            ids = list(
                RequisicaoIA.objects.filter(criado_em__lt=limite)
                .order_by("pk")
                .values_list("pk", flat=True)[: self.batch_size]
            )
            if not ids:
                break
            apagados, _ = RequisicaoIA.objects.filter(pk__in=ids).delete()
            total += apagados

        self.stdout.write(f"{total} requisição(ões) de IA removida(s).")
        return str(total)
