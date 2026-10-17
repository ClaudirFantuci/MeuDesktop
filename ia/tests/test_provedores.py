"""Testes dos provedores de IA sem acesso à rede."""

import os

from django.core.cache import cache
from django.test import TestCase

from ia.models import ConfiguracaoIA
from ia.provedores import _clientes, obter_provedor
from ia.provedores.base import ErroConfiguracao, PedidoIA, UsoTokens


class ProvedoresTestCase(TestCase):
    """Testa o contrato e a seleção de provedores sem acesso à rede."""

    def setUp(self) -> None:
        cache.clear()
        _clientes.clear()
        os.environ.pop("GEMINI_API_KEY", None)

    def tearDown(self) -> None:
        cache.clear()
        _clientes.clear()

    def test_configuracao_obter_cria_e_reutiliza_linha_unica(self) -> None:
        """Verifica a criação e o cache da configuração única."""
        primeira = ConfiguracaoIA.obter()  # pyright: ignore[reportPrivateUsage]
        segunda = ConfiguracaoIA.obter()

        self.assertEqual(getattr(ConfiguracaoIA, "objects").count(), 1)
        self.assertEqual(primeira, segunda)
        self.assertEqual(primeira.pk, 1)

    def test_salvar_configuracao_cria_novo_provedor(self) -> None:
        """Verifica a renovação do cliente após salvar a configuração."""
        configuracao = ConfiguracaoIA.obter()
        configuracao.provedor = "falso"
        configuracao.save()
        primeiro = obter_provedor(configuracao)

        configuracao.modelo = "outro-modelo"
        configuracao.save()
        segundo = obter_provedor(configuracao)

        self.assertIsNot(primeiro, segundo)

    def test_provedor_falso_processa_fila_e_registra_pedidos(self) -> None:
        """Verifica a ordem da fila e o registro dos pedidos recebidos."""
        configuracao = ConfiguracaoIA.obter()
        configuracao.provedor = "falso"
        configuracao.save()
        provedor = obter_provedor(configuracao)
        pedido = PedidoIA(instrucoes="", texto="teste")
        uso = UsoTokens(entrada=2, saida=3)
        provedor.programar(texto="primeira", uso=uso)
        provedor.programar(texto="segunda")

        primeira = provedor.gerar(pedido)
        segunda = provedor.gerar(pedido)

        self.assertEqual(primeira.texto, "primeira")
        self.assertEqual(primeira.uso, uso)
        self.assertEqual(segunda.texto, "segunda")
        self.assertEqual(provedor.pedidos, [pedido, pedido])

    def test_provedor_falso_levanta_erro_programado(self) -> None:
        """Verifica que o provedor falso repassa o erro programado."""
        configuracao = ConfiguracaoIA.obter()
        configuracao.provedor = "falso"
        configuracao.save()
        provedor = obter_provedor(configuracao)
        erro = RuntimeError("falha simulada")
        provedor.programar(erro=erro)

        with self.assertRaisesRegex(RuntimeError, "falha simulada"):
            provedor.gerar(PedidoIA(instrucoes="", texto="teste"))

    def test_gemini_sem_chave_levanta_erro_de_configuracao(self) -> None:
        """Verifica o erro claro quando a chave do Gemini está ausente."""
        configuracao = ConfiguracaoIA.obter()

        with self.assertRaises(ErroConfiguracao):
            obter_provedor(configuracao)
