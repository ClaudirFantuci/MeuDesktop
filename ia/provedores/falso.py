from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Any

from ia.provedores.base import PedidoIA, ProvedorIA, RespostaIA, UsoTokens


@dataclass
class _RespostaProgramada:
    texto: str = ""
    dados: Any = None
    uso: UsoTokens | None = None
    erro: Exception | None = None


class ProvedorFalso(ProvedorIA):
    """Provedor determinístico para testes, sem acesso à rede."""

    def __init__(self, config: Any, chave: str = "") -> None:
        super().__init__(config, chave)
        self.pedidos: list[PedidoIA] = []
        self._fila: deque[_RespostaProgramada] = deque()

    def programar(
        self,
        texto: str = "",
        dados: Any = None,
        uso: UsoTokens | None = None,
        erro: Exception | None = None,
    ) -> None:
        """Adiciona uma resposta ou erro à fila do provedor."""
        self._fila.append(_RespostaProgramada(texto, dados, uso, erro))

    def gerar(self, pedido: PedidoIA) -> RespostaIA:
        """Registra o pedido e devolve o próximo item programado."""
        self.pedidos.append(pedido)
        resposta = self._fila.popleft() if self._fila else _RespostaProgramada(texto="ok")
        if resposta.erro is not None:
            raise resposta.erro
        return RespostaIA(
            texto=resposta.texto,
            dados=resposta.dados,
            uso=resposta.uso or UsoTokens(),
            modelo=self.config.modelo,
            motivo_fim="",
        )
