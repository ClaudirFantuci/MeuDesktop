"""Porta de entrada única para chamadas de IA."""

from __future__ import annotations

import hashlib
import logging
import time
from collections.abc import Callable, Mapping
from time import monotonic
from typing import Any

from django.contrib.contenttypes.models import ContentType
from pydantic import BaseModel, ConfigDict

from ia.cota import (
    CotaExcedida,
    custo_estimado,
    dono_da_cota,
    registrar_consumo,
    teto_do_sistema_atingido,
    verificar,
)
from ia.models import ConfiguracaoIA, ConfiguracaoIAUsuario, RequisicaoIA
from ia.provedores import obter_provedor
from ia.provedores.base import (
    ErroIA,
    ErroTemporario,
    IaIndisponivel,
    PedidoIA,
    RespostaIA,
    UsoTokens,
)


logger = logging.getLogger(__name__)


class _StatusConexao(BaseModel):
    """Esquema mínimo usado pelo teste de conexão."""

    model_config = ConfigDict(extra="forbid")
    status: str


def _referencia_campos(referencia: Any) -> tuple[ContentType | None, int | None]:
    if referencia is None:
        return None, None
    return ContentType.objects.get_for_model(referencia), int(referencia.pk)


def _arquivo_campos(arquivo_info: Mapping[str, Any] | None) -> dict[str, Any]:
    if not arquivo_info:
        return {
            "arquivo_mime": "",
            "arquivo_tamanho": 0,
            "arquivo_hash": "",
        }
    return {
        "arquivo_mime": str(arquivo_info.get("mime", "")),
        "arquivo_tamanho": int(arquivo_info.get("tamanho", 0) or 0),
        "arquivo_hash": str(arquivo_info.get("hash", "")),
    }


def _auditar(
    *,
    usuario: Any,
    finalidade: str,
    origem: str,
    referencia: Any,
    versao_prompt: str,
    tentativa: int,
    provedor: str,
    modelo: str,
    situacao: str,
    uso: UsoTokens | None = None,
    custo: Any = 0,
    duracao_ms: int = 0,
    motivo_fim: str = "",
    resposta: str = "",
    erro: str = "",
    contexto_hash: str = "",
    arquivo_info: Mapping[str, Any] | None = None,
) -> None:
    """Tenta gravar auditoria, sem deixar sua falha afetar a chamada."""
    try:
        referencia_tipo, referencia_id = _referencia_campos(referencia)
        uso = uso or UsoTokens()
        RequisicaoIA.objects.create(
            usuario=usuario,
            referencia_tipo=referencia_tipo,
            referencia_id=referencia_id,
            origem=origem,
            finalidade=finalidade,
            provedor=provedor,
            modelo=modelo,
            versao_prompt=versao_prompt,
            tentativa=tentativa,
            situacao=situacao,
            tokens_entrada=uso.entrada,
            tokens_saida=uso.saida,
            tokens_raciocinio=uso.raciocinio,
            tokens_total=uso.total,
            custo_estimado=custo,
            duracao_ms=duracao_ms,
            motivo_fim=motivo_fim,
            resposta=(resposta or "")[:20000],
            erro=erro,
            contexto_hash=contexto_hash,
            **_arquivo_campos(arquivo_info),
        )
    except Exception:
        logger.exception("Falha ao gravar auditoria da chamada de IA")


def _registrar_uso(dono: Any, uso: UsoTokens, configuracao: ConfiguracaoIA) -> Any:
    if uso.total <= 0:
        return 0
    custo = custo_estimado(uso, configuracao)
    registrar_consumo(dono, uso, custo)
    return custo


def chamar_ia(
    *,
    finalidade: str,
    montar_pedido: Callable[[ConfiguracaoIA], PedidoIA],
    usuario: Any,
    origem: str = "site",
    referencia: Any = None,
    versao_prompt: str = "",
    arquivo_info: Mapping[str, Any] | None = None,
) -> RespostaIA:
    """Executa uma chamada de IA com cota, tentativas e auditoria."""
    configuracao = ConfiguracaoIA.obter()
    dono = dono_da_cota(usuario)
    contexto_hash = ""

    configuracao_usuario = ConfiguracaoIAUsuario.objects.filter(usuario=usuario).first()
    if configuracao_usuario is not None and not configuracao_usuario.ia_habilitada:
        erro = IaIndisponivel("A IA está desabilitada para este usuário.", modelo=configuracao.modelo)
        _auditar(
            usuario=usuario,
            finalidade=finalidade,
            origem=origem,
            referencia=referencia,
            versao_prompt=versao_prompt,
            tentativa=1,
            provedor=configuracao.provedor,
            modelo=configuracao.modelo,
            situacao=erro.situacao,
            erro=str(erro),
            arquivo_info=arquivo_info,
        )
        raise erro

    if teto_do_sistema_atingido():
        erro = IaIndisponivel("O limite mensal do sistema de IA foi atingido.", modelo=configuracao.modelo)
        _auditar(
            usuario=usuario,
            finalidade=finalidade,
            origem=origem,
            referencia=referencia,
            versao_prompt=versao_prompt,
            tentativa=1,
            provedor=configuracao.provedor,
            modelo=configuracao.modelo,
            situacao=erro.situacao,
            erro=str(erro),
            arquivo_info=arquivo_info,
        )
        raise erro

    try:
        verificar(dono)
    except CotaExcedida as erro:
        _auditar(
            usuario=usuario,
            finalidade=finalidade,
            origem=origem,
            referencia=referencia,
            versao_prompt=versao_prompt,
            tentativa=1,
            provedor=configuracao.provedor,
            modelo=configuracao.modelo,
            situacao="bloqueada_cota",
            erro=str(erro),
            arquivo_info=arquivo_info,
        )
        raise

    pedido = montar_pedido(configuracao)
    contexto_hash = hashlib.sha256(pedido.texto.encode("utf-8")).hexdigest()
    tentativas = max(configuracao.tentativas, 1)

    for tentativa in range(1, tentativas + 1):
        inicio = monotonic()
        try:
            provedor = obter_provedor(configuracao)
            resposta = provedor.gerar(pedido)
            duracao_ms = int((monotonic() - inicio) * 1000)
            custo = _registrar_uso(dono, resposta.uso, configuracao)
            _auditar(
                usuario=usuario,
                finalidade=finalidade,
                origem=origem,
                referencia=referencia,
                versao_prompt=versao_prompt,
                tentativa=tentativa,
                provedor=configuracao.provedor,
                modelo=resposta.modelo or configuracao.modelo,
                situacao="sucesso",
                uso=resposta.uso,
                custo=custo,
                duracao_ms=duracao_ms,
                motivo_fim=resposta.motivo_fim,
                resposta=resposta.texto,
                contexto_hash=contexto_hash,
                arquivo_info=arquivo_info,
            )
            return resposta
        except ErroIA as erro:
            uso = erro.uso
            duracao_ms = int((monotonic() - inicio) * 1000)
            custo = _registrar_uso(dono, uso, configuracao)
            _auditar(
                usuario=usuario,
                finalidade=finalidade,
                origem=origem,
                referencia=referencia,
                versao_prompt=versao_prompt,
                tentativa=tentativa,
                provedor=configuracao.provedor,
                modelo=erro.modelo or configuracao.modelo,
                situacao=erro.situacao,
                uso=uso,
                custo=custo,
                duracao_ms=duracao_ms,
                motivo_fim=erro.situacao,
                resposta=erro.texto_bruto,
                erro=str(erro),
                contexto_hash=contexto_hash,
                arquivo_info=arquivo_info,
            )
            if not isinstance(erro, ErroTemporario):
                raise
            if tentativa >= tentativas:
                raise
            time.sleep(tentativa)

    raise RuntimeError("A chamada de IA terminou sem resposta ou erro.")


def testar_conexao(usuario: Any) -> RespostaIA:
    """Executa uma chamada mínima para verificar a conexão com o provedor."""

    def montar_pedido(_configuracao: ConfiguracaoIA) -> PedidoIA:
        return PedidoIA(
            instrucoes="Responda apenas com o status solicitado.",
            texto="Responda com status ok.",
            esquema=_StatusConexao,
        )

    return chamar_ia(
        finalidade="teste_conexao",
        montar_pedido=montar_pedido,
        usuario=usuario,
    )
