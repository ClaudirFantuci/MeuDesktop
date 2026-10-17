from __future__ import annotations

import os
from typing import Any

from django.utils.module_loading import import_string

from ia.provedores.base import ErroConfiguracao, ProvedorIA


PROVEDORES = {
    "gemini": "ia.provedores.gemini.ProvedorGemini",
    "falso": "ia.provedores.falso.ProvedorFalso",
}

_clientes: dict[tuple[str, Any], ProvedorIA] = {}


def obter_provedor(config: Any) -> ProvedorIA:
    """Obtém um provedor configurado, reutilizando-o até a configuração mudar."""
    try:
        caminho = PROVEDORES[config.provedor]
    except KeyError as exc:
        raise ErroConfiguracao(
            f"Provedor de IA desconhecido: {config.provedor}.",
            modelo=getattr(config, "modelo", ""),
        ) from exc

    chave = os.environ.get("GEMINI_API_KEY", "") if config.provedor == "gemini" else ""
    if config.provedor == "gemini" and not chave:
        raise ErroConfiguracao(
            "GEMINI_API_KEY não foi configurada para o provedor Gemini.",
            modelo=config.modelo,
        )

    cache_key = (config.provedor, config.atualizado_em)
    if cache_key not in _clientes:
        _clientes[cache_key] = import_string(caminho)(config, chave)
    return _clientes[cache_key]
