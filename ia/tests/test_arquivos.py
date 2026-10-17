"""Testes da validação e normalização de arquivos para IA."""

from io import BytesIO

from django.core.cache import cache
from django.test import TestCase
from PIL import Image

from ia.arquivos import ArquivoInvalido, hash_arquivo, preparar_arquivo
from ia.models import ConfiguracaoIA


class ArquivosTestCase(TestCase):
    """Verifica os formatos aceitos e os limites configuráveis."""

    def setUp(self) -> None:
        cache.clear()
        self.configuracao = ConfiguracaoIA.obter()

    def test_imagem_e_convertida_para_jpeg(self) -> None:
        """Converte uma imagem válida para RGB JPEG reduzido."""
        imagem = Image.new("RGBA", (32, 16), (255, 0, 0, 128))
        original = BytesIO()
        imagem.save(original, format="PNG")

        preparada, mime = preparar_arquivo(original.getvalue(), "image/png", lado_maximo=16)

        self.assertEqual(mime, "image/jpeg")
        self.assertEqual(Image.open(BytesIO(preparada)).format, "JPEG")
        self.assertEqual(len(hash_arquivo(preparada)), 64)

    def test_tipo_desconhecido_e_recusado(self) -> None:
        """Recusa conteúdo que não é PDF ou imagem."""
        with self.assertRaisesRegex(ArquivoInvalido, "não suportado"):
            preparar_arquivo(b"texto", "text/plain")

    def test_tamanho_excedente_e_recusado(self) -> None:
        """Recusa arquivo acima do limite configurado."""
        self.configuracao.tamanho_maximo_mb = 1
        self.configuracao.save()

        with self.assertRaisesRegex(ArquivoInvalido, "muito grande"):
            preparar_arquivo(b"x" * (1024 * 1024 + 1), "application/pdf")
