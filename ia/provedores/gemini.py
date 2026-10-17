"""Implementação do provedor Google Gemini."""

from __future__ import annotations

import copy
from typing import Any

from google import genai
from google.genai import errors, types
from pydantic import ValidationError

from ia.provedores.base import (
    BloqueioSeguranca,
    ErroConfiguracao,
    ErroPermanente,
    ErroTemporario,
    PedidoIA,
    ProvedorIA,
    RespostaIA,
    RespostaInvalida,
    TempoEsgotado,
    UsoTokens,
)


class ProvedorGemini(ProvedorIA):
    """Adapta o contrato neutro à API Google Gemini."""

    def __init__(self, config: Any, chave: str) -> None:
        super().__init__(config, chave)
        self.cliente = genai.Client(
            api_key=chave,
            http_options=types.HttpOptions(timeout=config.timeout_s * 1000),
        )

    def gerar(self, pedido: PedidoIA) -> RespostaIA:
        """Envia um pedido ao Gemini e normaliza sua resposta."""
        contents = [
            types.Content(
                role=mensagem.papel,
                parts=[types.Part(text=mensagem.texto)],
            )
            for mensagem in pedido.historico
        ]
        partes = [
            types.Part.from_bytes(data=arquivo.conteudo, mime_type=arquivo.mime)
            for arquivo in pedido.arquivos
        ]
        partes.append(types.Part(text=pedido.texto))
        contents.append(types.Content(role="user", parts=partes))

        kwargs: dict[str, Any] = {
            "system_instruction": pedido.instrucoes,
            "temperature": float(self.config.temperatura),
            "max_output_tokens": self.config.max_tokens_saida,
        }
        if self.config.nivel_raciocinio:
            kwargs["thinking_config"] = types.ThinkingConfig(
                thinking_level=self.config.nivel_raciocinio,
            )
        if pedido.esquema is not None:
            kwargs["response_mime_type"] = "application/json"
            kwargs["response_json_schema"] = _schema_sem_referencias(pedido.esquema)

        try:
            response = self.cliente.models.generate_content(
                model=self.config.modelo,
                contents=contents,
                config=types.GenerateContentConfig(**kwargs),
            )
        except TimeoutError as exc:
            raise TempoEsgotado(str(exc), modelo=self.config.modelo) from exc
        except errors.APIError as exc:
            raise _erro_api(exc, self.config.modelo) from exc
        except OSError as exc:
            raise ErroTemporario(str(exc), modelo=self.config.modelo) from exc

        uso = _uso_tokens(response)
        motivo_fim = _motivo_fim(response)
        texto = response.text or ""
        if motivo_fim in {"SAFETY", "PROHIBITED_CONTENT"}:
            raise BloqueioSeguranca(
                "A resposta foi bloqueada pelos filtros de segurança do Gemini.",
                uso=uso,
                texto_bruto=texto,
                modelo=self.config.modelo,
            )
        if motivo_fim == "MAX_TOKENS":
            raise RespostaInvalida(
                "A resposta atingiu o limite máximo de tokens.",
                uso=uso,
                texto_bruto=texto,
                modelo=self.config.modelo,
            )

        dados = None
        if pedido.esquema is not None:
            try:
                dados = pedido.esquema.model_validate_json(texto)
            except ValidationError as exc:
                raise RespostaInvalida(
                    "A resposta do Gemini não corresponde ao esquema solicitado.",
                    uso=uso,
                    texto_bruto=texto,
                    modelo=self.config.modelo,
                ) from exc

        return RespostaIA(
            texto=texto,
            dados=dados,
            uso=uso,
            modelo=self.config.modelo,
            motivo_fim=motivo_fim,
            id_resposta=getattr(response, "response_id", "") or "",
        )


def _erro_api(exc: errors.APIError, modelo: str) -> Exception:
    code = getattr(exc, "code", None)
    mensagem = str(exc)
    if code in {400, 401, 403, 404}:
        return ErroConfiguracao(mensagem, modelo=modelo)
    if code == 429 or (isinstance(code, int) and code >= 500):
        return ErroTemporario(mensagem, modelo=modelo)
    if isinstance(code, int) and 400 <= code < 500:
        return ErroPermanente(mensagem, modelo=modelo)
    return ErroTemporario(mensagem, modelo=modelo)


def _uso_tokens(response: Any) -> UsoTokens:
    metadata = getattr(response, "usage_metadata", None)
    entrada = getattr(metadata, "prompt_token_count", 0) or 0
    raciocinio = getattr(metadata, "thoughts_token_count", 0) or 0
    saida = (getattr(metadata, "candidates_token_count", 0) or 0) + raciocinio
    return UsoTokens(entrada=entrada, saida=saida, raciocinio=raciocinio)


def _motivo_fim(response: Any) -> str:
    candidates = getattr(response, "candidates", None) or []
    if not candidates:
        return ""
    motivo = getattr(candidates[0], "finish_reason", "")
    return getattr(motivo, "name", str(motivo))


def _schema_sem_referencias(esquema: type[Any]) -> dict[str, Any]:
    documento = copy.deepcopy(esquema.model_json_schema())
    definicoes = documento.pop("$defs", {})

    def resolver(valor: Any, caminho: tuple[str, ...] = ()) -> Any:
        if isinstance(valor, dict):
            referencia = valor.get("$ref")
            if referencia and referencia.startswith("#/$defs/"):
                nome = referencia.removeprefix("#/$defs/")
                if nome not in caminho:
                    return resolver(definicoes[nome], caminho + (nome,))
            return {
                chave: resolver(item, caminho)
                for chave, item in valor.items()
                if chave != "$ref"
            }
        if isinstance(valor, list):
            return [resolver(item, caminho) for item in valor]
        return valor

    return resolver(documento)
