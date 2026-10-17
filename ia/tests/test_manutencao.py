"""Testes do comando e da rota interna de manutenção."""

from datetime import timedelta
from io import StringIO
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from ia.models import ConfiguracaoIA, ConsumoIA, RequisicaoIA


User = get_user_model()


class ManutencaoTestCase(TestCase):
    """Verifica limpeza em lotes e proteção por segredo."""

    def setUp(self) -> None:
        self.usuario = User.objects.create_user(username="limpeza", password="senha")
        self.configuracao = ConfiguracaoIA.obter()
        self.configuracao.reter_requisicoes_dias = 60
        self.configuracao.save()

    def _requisicao(self, finalidade: str) -> RequisicaoIA:
        return RequisicaoIA.objects.create(
            usuario=self.usuario,
            finalidade=finalidade,
            provedor="falso",
            modelo="teste",
            tentativa=1,
            situacao="sucesso",
        )

    def test_comando_remove_antigas_em_lotes_sem_apagar_consumo(self) -> None:
        """Remove auditorias antigas e preserva o agregado mensal."""
        antigas = [self._requisicao(f"antiga_{numero}") for numero in range(1001)]
        recente = self._requisicao("recente")
        data_antiga = timezone.now() - timedelta(days=61)
        RequisicaoIA.objects.filter(pk__in=[item.pk for item in antigas]).update(criado_em=data_antiga)
        ConsumoIA.objects.create(dono=self.usuario, mes=date_mes(), tokens_total=321)

        saida = StringIO()
        call_command("ia_limpar", stdout=saida)

        self.assertEqual(RequisicaoIA.objects.filter(finalidade__startswith="antiga_").count(), 0)
        self.assertTrue(RequisicaoIA.objects.filter(pk=recente.pk).exists())
        self.assertEqual(ConsumoIA.objects.get(dono=self.usuario).tokens_total, 321)
        self.assertIn("1001", saida.getvalue())

    @override_settings(TAREFAS_SEGREDO="segredo-de-teste")
    @patch("ia.manutencao.call_command")
    def test_rota_exige_segredo_e_executa_limpeza(self, executar) -> None:
        """Aceita apenas POST com o header secreto correto."""
        url = reverse("ia:manutencao")

        self.assertEqual(self.client.post(url).status_code, 403)
        self.assertEqual(
            self.client.post(url, HTTP_X_TAREFAS_SEGREDO="errado").status_code,
            403,
        )
        resposta = self.client.post(url, HTTP_X_TAREFAS_SEGREDO="segredo-de-teste")

        self.assertEqual(resposta.status_code, 200)
        executar.assert_called_once_with("ia_limpar")


def date_mes():
    """Retorna o mês usado pelo teste sem depender do relógio do servidor."""
    hoje = timezone.localdate()
    return hoje.replace(day=1)
