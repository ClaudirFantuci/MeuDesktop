"""Testes da porta de entrada de IA sem rede."""

from datetime import date
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase

from ia.chamada import chamar_ia
from ia.cota import CotaExcedida, limite_do_usuario, mes_atual
from ia.models import ConfiguracaoIA, ConfiguracaoIAUsuario, ConsumoIA, RequisicaoIA
from ia.provedores import _clientes, obter_provedor
from ia.provedores.base import (
    ErroConfiguracao,
    ErroTemporario,
    IaIndisponivel,
    PedidoIA,
    UsoTokens,
)


User = get_user_model()


class ChamadaTestCase(TestCase):
    """Verifica cota, tentativas, consumo e auditoria da porta de entrada."""

    def setUp(self) -> None:
        cache.clear()
        _clientes.clear()
        self.usuario = User.objects.create_user(username="teste", password="senha")
        self.configuracao = ConfiguracaoIA.obter()
        self.configuracao.provedor = "falso"
        self.configuracao.reserva_minima_tokens = 0
        self.configuracao.limite_mensal_sistema = 0
        self.configuracao.save()
        self.provedor = obter_provedor(self.configuracao)

    def tearDown(self) -> None:
        cache.clear()
        _clientes.clear()

    @staticmethod
    def montar_pedido(_configuracao: ConfiguracaoIA) -> PedidoIA:
        return PedidoIA(instrucoes="Você é um teste.", texto="texto enviado")

    def test_sucesso_grava_auditoria_referencia_e_consumo(self) -> None:
        """Registra sucesso, referência e consumo mensal."""
        self.provedor.programar(texto="resposta", uso=UsoTokens(entrada=10, saida=20))

        resposta = chamar_ia(
            finalidade="app_teste",
            montar_pedido=self.montar_pedido,
            usuario=self.usuario,
            referencia=self.usuario,
            versao_prompt="v1",
        )

        registro = RequisicaoIA.objects.get()
        consumo = ConsumoIA.objects.get(dono=self.usuario, mes=mes_atual())
        self.assertEqual(resposta.texto, "resposta")
        self.assertEqual(registro.situacao, "sucesso")
        self.assertEqual(registro.referencia, self.usuario)
        self.assertEqual(registro.tentativa, 1)
        self.assertEqual(registro.contexto_hash.__len__(), 64)
        self.assertEqual(consumo.tokens_total, 30)
        self.assertEqual(consumo.requisicoes, 1)

    @patch("ia.chamada.time.sleep")
    def test_erro_temporario_seguido_de_sucesso_grava_duas_tentativas(self, dormir) -> None:
        """Repete erro temporário e registra cada tentativa."""
        self.provedor.programar(
            erro=ErroTemporario(
                "temporário",
                uso=UsoTokens(entrada=2, saida=3),
                modelo=self.configuracao.modelo,
            )
        )
        self.provedor.programar(texto="ok", uso=UsoTokens(entrada=4, saida=5))

        chamar_ia(finalidade="app_teste", montar_pedido=self.montar_pedido, usuario=self.usuario)

        registros = RequisicaoIA.objects.order_by("tentativa")
        consumo = ConsumoIA.objects.get(dono=self.usuario, mes=mes_atual())
        self.assertEqual(registros.count(), 2)
        self.assertEqual(list(registros.values_list("situacao", flat=True)), ["erro_temporario", "sucesso"])
        self.assertEqual(consumo.tokens_total, 14)
        dormir.assert_called_once_with(1)

    def test_erro_configuracao_nao_repete(self) -> None:
        """Não repete erros de configuração."""
        self.provedor.programar(erro=ErroConfiguracao("configuração inválida"))

        with self.assertRaises(ErroConfiguracao):
            chamar_ia(finalidade="app_teste", montar_pedido=self.montar_pedido, usuario=self.usuario)

        self.assertEqual(RequisicaoIA.objects.count(), 1)
        self.assertEqual(RequisicaoIA.objects.get().tentativa, 1)

    def test_cota_esgotada_nao_chama_provedor_e_audita_bloqueio(self) -> None:
        """Bloqueia antes do provedor quando a reserva acabou."""
        self.configuracao.limite_mensal_usuario = 0
        self.configuracao.save()

        with self.assertRaises(CotaExcedida):
            chamar_ia(finalidade="app_teste", montar_pedido=self.montar_pedido, usuario=self.usuario)

        self.assertEqual(self.provedor.pedidos, [])
        self.assertEqual(RequisicaoIA.objects.get().situacao, "bloqueada_cota")

    def test_limite_proprio_zero_bloqueia_e_vazio_volta_ao_padrao(self) -> None:
        """Respeita zero individual e usa o padrão quando o campo é vazio."""
        self.configuracao.limite_mensal_usuario = 123
        self.configuracao.save()
        preferencia = ConfiguracaoIAUsuario.objects.create(
            usuario=self.usuario,
            limite_mensal=0,
        )

        with self.assertRaises(CotaExcedida):
            chamar_ia(finalidade="app_teste", montar_pedido=self.montar_pedido, usuario=self.usuario)

        preferencia.limite_mensal = None
        preferencia.save()
        self.assertEqual(limite_do_usuario(self.usuario), 123)

    def test_falha_ao_gravar_auditoria_nao_derruba_chamada(self) -> None:
        """Mantém o sucesso quando a auditoria falha."""
        self.provedor.programar(texto="ok", uso=UsoTokens(entrada=1, saida=1))

        with patch("ia.chamada.RequisicaoIA.objects.create", side_effect=RuntimeError("banco")):
            resposta = chamar_ia(
                finalidade="app_teste",
                montar_pedido=self.montar_pedido,
                usuario=self.usuario,
            )

        self.assertEqual(resposta.texto, "ok")
        self.assertEqual(ConsumoIA.objects.get().tokens_total, 2)

    def test_teto_do_sistema_bloqueia_todos(self) -> None:
        """Bloqueia a chamada quando o teto mensal agregado foi atingido."""
        self.configuracao.limite_mensal_sistema = 10
        self.configuracao.save()
        ConsumoIA.objects.create(dono=self.usuario, mes=mes_atual(), tokens_total=10)

        with self.assertRaises(IaIndisponivel):
            chamar_ia(finalidade="app_teste", montar_pedido=self.montar_pedido, usuario=self.usuario)

        self.assertEqual(self.provedor.pedidos, [])
        self.assertEqual(RequisicaoIA.objects.get().situacao, "indisponivel")

    def test_consumo_de_mes_anterior_nao_conta_no_mes_atual(self) -> None:
        """Considera somente o mês corrente na cota."""
        atual = mes_atual()
        anterior = date(atual.year - 1, 12, 1) if atual.month == 1 else date(atual.year, atual.month - 1, 1)
        ConsumoIA.objects.create(dono=self.usuario, mes=anterior, tokens_total=999999)
        self.provedor.programar(texto="ok", uso=UsoTokens(entrada=4, saida=6))

        chamar_ia(finalidade="app_teste", montar_pedido=self.montar_pedido, usuario=self.usuario)

        self.assertEqual(ConsumoIA.objects.get(dono=self.usuario, mes=anterior).tokens_total, 999999)
        self.assertEqual(ConsumoIA.objects.get(dono=self.usuario, mes=atual).tokens_total, 10)
