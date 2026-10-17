"""Tipos e contrato comum para provedores de IA."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel


@dataclass(frozen=True)
class Arquivo:
    """Arquivo enviado como parte de um pedido de IA."""

    conteudo: bytes
    mime: str
    nome: str = ""


@dataclass(frozen=True)
class MensagemHistorico:
    """Mensagem anterior de uma conversa com o provedor."""

    papel: str
    texto: str

    def __post_init__(self) -> None:
        if self.papel not in {"user", "model"}:
            raise ValueError("papel deve ser 'user' ou 'model'")


@dataclass(frozen=True)
class PedidoIA:
    """Pedido neutro encaminhado a qualquer provedor de IA."""

    instrucoes: str
    texto: str
    arquivos: tuple[Arquivo, ...] = ()
    historico: tuple[MensagemHistorico, ...] = ()
    esquema: type[BaseModel] | None = None


@dataclass(frozen=True)
class UsoTokens:
    """Tokens informados pelo provedor para uma resposta."""

    entrada: int = 0
    saida: int = 0
    raciocinio: int = 0

    @property
    def total(self) -> int:
        """Retorna a soma dos tokens de entrada e saída."""

        return self.entrada + self.saida


@dataclass(frozen=True)
class RespostaIA:
    """Resposta normalizada devolvida por um provedor de IA."""

    texto: str
    dados: BaseModel | None
    uso: UsoTokens
    modelo: str
    motivo_fim: str
    id_resposta: str = ""


class ErroIA(Exception):
    """Erro normalizado de uma chamada de IA."""

    situacao = "erro_ia"

    def __init__(
        self,
        mensagem: str = "Erro ao consultar o provedor de IA.",
        *,
        uso: UsoTokens | None = None,
        texto_bruto: str = "",
        modelo: str = "",
    ) -> None:
        super().__init__(mensagem)
        self.uso = uso or UsoTokens()
        self.texto_bruto = texto_bruto
        self.modelo = modelo


class ErroTemporario(ErroIA):
    """Erro que pode ser resolvido por nova tentativa."""

    situacao = "erro_temporario"


class TempoEsgotado(ErroTemporario):
    """Erro causado pelo limite de tempo da chamada."""

    situacao = "tempo_esgotado"


class ErroPermanente(ErroIA):
    """Erro que não deve ser repetido automaticamente."""

    situacao = "erro_permanente"


class RespostaInvalida(ErroPermanente):
    """Resposta que não atende ao contrato solicitado."""

    situacao = "resposta_invalida"


class BloqueioSeguranca(ErroIA):
    """Resposta bloqueada pelos filtros de segurança do provedor."""

    situacao = "bloqueada_seguranca"


class ErroConfiguracao(ErroIA):
    """Configuração ausente ou inválida para o provedor."""

    situacao = "erro_configuracao"


class IaIndisponivel(ErroIA):
    """Provedor temporariamente indisponível."""

    situacao = "indisponivel"


class ProvedorIA(ABC):
    """Interface comum para todos os provedores de IA."""

    def __init__(self, config: Any, chave: str = "") -> None:
        self.config = config
        self.chave = chave

    @abstractmethod
    def gerar(self, pedido: PedidoIA) -> RespostaIA:
        """Gera uma resposta para um pedido neutro."""

        raise NotImplementedError
