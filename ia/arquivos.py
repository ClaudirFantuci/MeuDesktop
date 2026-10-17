"""Validação e normalização de arquivos enviados aos provedores de IA."""

from __future__ import annotations

import hashlib
from io import BytesIO

from PIL import Image, ImageOps, UnidentifiedImageError
from pypdf import PdfReader

from ia.models import ConfiguracaoIA


Image.MAX_IMAGE_PIXELS = 25_000_000


class ArquivoInvalido(ValueError):
    """Arquivo ausente, excedente, corrompido ou não suportado."""


def hash_arquivo(conteudo: bytes) -> str:
    """Calcula o hash SHA-256 do conteúdo do arquivo."""
    return hashlib.sha256(conteudo).hexdigest()


def _validar_tamanho(conteudo: bytes, configuracao: ConfiguracaoIA) -> None:
    limite = configuracao.tamanho_maximo_mb * 1024 * 1024
    if len(conteudo) > limite:
        raise ArquivoInvalido(
            f"O arquivo é muito grande. O limite é de {configuracao.tamanho_maximo_mb} MB."
        )


def _preparar_pdf(conteudo: bytes, configuracao: ConfiguracaoIA) -> tuple[bytes, str]:
    try:
        paginas = len(PdfReader(BytesIO(conteudo)).pages)
    except Exception as exc:
        raise ArquivoInvalido("O PDF está inválido ou corrompido.") from exc
    if paginas > configuracao.pdf_max_paginas:
        raise ArquivoInvalido(
            f"O PDF tem muitas páginas. O limite é de {configuracao.pdf_max_paginas}."
        )
    return conteudo, "application/pdf"


def _preparar_imagem(conteudo: bytes, lado_maximo: int) -> tuple[bytes, str]:
    if lado_maximo <= 0:
        raise ArquivoInvalido("O lado máximo da imagem deve ser maior que zero.")
    try:
        with Image.open(BytesIO(conteudo)) as imagem:
            imagem = ImageOps.exif_transpose(imagem)
            imagem = imagem.convert("RGB")
            imagem.thumbnail((lado_maximo, lado_maximo), Image.Resampling.LANCZOS)
            saida = BytesIO()
            imagem.save(saida, format="JPEG", quality=85)
    except (Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ArquivoInvalido("A imagem excede o limite de pixels permitido.") from exc
    except (UnidentifiedImageError, OSError, ValueError) as exc:
        raise ArquivoInvalido("A imagem está inválida ou corrompida.") from exc
    return saida.getvalue(), "image/jpeg"


def preparar_arquivo(
    conteudo: bytes,
    mime: str,
    lado_maximo: int = 2048,
) -> tuple[bytes, str]:
    """Valida, reduz e normaliza um arquivo aceito pela camada de IA."""
    if not isinstance(conteudo, bytes) or not conteudo:
        raise ArquivoInvalido("O arquivo está vazio ou não é binário.")

    configuracao = ConfiguracaoIA.obter()
    _validar_tamanho(conteudo, configuracao)
    mime = (mime or "").lower().split(";", 1)[0].strip()

    if mime == "application/pdf" or conteudo.startswith(b"%PDF-"):
        return _preparar_pdf(conteudo, configuracao)
    if mime.startswith("image/"):
        return _preparar_imagem(conteudo, lado_maximo)
    raise ArquivoInvalido("Tipo de arquivo não suportado. Envie um PDF ou uma imagem.")
