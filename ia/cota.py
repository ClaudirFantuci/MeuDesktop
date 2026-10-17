"""Regras de cota mensal de tokens da camada de IA."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.db import models, transaction
from django.db.models import F, Sum

from ia.models import ConfiguracaoIA, ConfiguracaoIAUsuario, ConsumoIA
from ia.provedores.base import UsoTokens


FUSO_COTA = ZoneInfo("America/Sao_Paulo")


class CotaExcedida(Exception):
    """Indica que o usuário não possui tokens suficientes para uma chamada."""

    def __init__(self, situacao: "SituacaoCota") -> None:
        self.situacao = situacao
        super().__init__(situacao.mensagem_esgotada())


@dataclass(frozen=True)
class SituacaoCota:
    """Estado calculado da cota de um dono em um mês."""

    usado: int
    limite: int
    restante: int
    percentual: Decimal
    renova_em: date
    esgotada: bool
    em_alerta: bool

    def mensagem_esgotada(self) -> str:
        """Retorna a mensagem de cota esgotada para o usuário."""
        return f"Sua cota de IA acabou. Ela renova em {self.renova_em:%d/%m}."


def mes_atual() -> date:
    """Retorna o primeiro dia do mês atual em São Paulo."""
    hoje = datetime.now(FUSO_COTA).date()
    return hoje.replace(day=1)


def proximo_mes(mes: date) -> date:
    """Retorna o primeiro dia do mês seguinte."""
    if mes.month == 12:
        return date(mes.year + 1, 1, 1)
    return date(mes.year, mes.month + 1, 1)


def dono_da_cota(usuario: models.Model) -> models.Model:
    """Retorna o dono definido pelo domínio para a cota de IA."""
    return usuario


def limite_do_usuario(usuario: models.Model) -> int:
    """Lê o limite individual ou cai no limite global configurado."""
    configuracao_usuario = ConfiguracaoIAUsuario.objects.filter(usuario=usuario).first()
    if configuracao_usuario is not None and configuracao_usuario.limite_mensal is not None:
        return configuracao_usuario.limite_mensal
    return ConfiguracaoIA.obter().limite_mensal_usuario


def _usado_no_mes(dono: models.Model, mes: date) -> int:
    consumo = ConsumoIA.objects.filter(dono=dono, mes=mes).values_list("tokens_total", flat=True).first()
    return int(consumo or 0)


def situacao_da_cota(dono: models.Model) -> SituacaoCota:
    """Calcula a situação atual da cota mensal do dono."""
    configuracao = ConfiguracaoIA.obter()
    usado = _usado_no_mes(dono, mes_atual())
    limite = limite_do_usuario(dono)
    restante = max(limite - usado, 0)
    percentual = (
        Decimal("100")
        if limite == 0
        else (Decimal(usado) * Decimal("100") / Decimal(limite))
    )
    return SituacaoCota(
        usado=usado,
        limite=limite,
        restante=restante,
        percentual=percentual,
        renova_em=proximo_mes(mes_atual()),
        esgotada=limite == 0 or restante < configuracao.reserva_minima_tokens,
        em_alerta=percentual >= configuracao.aviso_percentual,
    )


def verificar(dono: models.Model) -> SituacaoCota:
    """Verifica a cota e levanta CotaExcedida quando não há reserva."""
    situacao = situacao_da_cota(dono)
    if situacao.esgotada:
        raise CotaExcedida(situacao)
    return situacao


def teto_do_sistema_atingido() -> bool:
    """Verifica o teto mensal agregado do sistema."""
    configuracao = ConfiguracaoIA.obter()
    if configuracao.limite_mensal_sistema == 0:
        return False
    usado = (
        ConsumoIA.objects.filter(mes=mes_atual()).aggregate(total=Sum("tokens_total"))["total"]
        or 0
    )
    return int(usado) >= configuracao.limite_mensal_sistema


def custo_estimado(uso: UsoTokens, configuracao: ConfiguracaoIA | None = None) -> Decimal:
    """Calcula o custo em dólares usando os preços configurados."""
    configuracao = configuracao or ConfiguracaoIA.obter()
    preco_entrada = configuracao.preco_entrada_milhao or Decimal("0")
    preco_saida = configuracao.preco_saida_milhao or Decimal("0")
    return (
        Decimal(uso.entrada) * preco_entrada
        + Decimal(uso.saida) * preco_saida
    ) / Decimal("1000000")


@transaction.atomic
def registrar_consumo(dono: models.Model, uso: UsoTokens, custo: Decimal) -> ConsumoIA:
    """Registra tokens e custo usando incrementos atômicos no banco."""
    consumo, _ = ConsumoIA.objects.get_or_create(
        dono=dono,
        mes=mes_atual(),
        defaults={
            "tokens_entrada": 0,
            "tokens_saida": 0,
            "tokens_total": 0,
            "custo_estimado": Decimal("0"),
            "requisicoes": 0,
        },
    )
    ConsumoIA.objects.filter(pk=consumo.pk).update(
        tokens_entrada=F("tokens_entrada") + uso.entrada,
        tokens_saida=F("tokens_saida") + uso.saida,
        tokens_total=F("tokens_total") + uso.total,
        custo_estimado=F("custo_estimado") + custo,
        requisicoes=F("requisicoes") + 1,
    )
    consumo.refresh_from_db()
    return consumo
