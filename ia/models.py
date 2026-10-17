"""Models de configuração global e por usuário para a camada de IA."""

from __future__ import annotations

from decimal import Decimal
from typing import ClassVar

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.cache import cache
from django.db import models


class ConfiguracaoIA(models.Model):
    """Configuração global do acesso aos provedores de IA."""

    objects = models.Manager()
    PROVEDOR_CHOICES: ClassVar[tuple[tuple[str, str], ...]] = (
        ("gemini", "Gemini"),
        ("falso", "Falso"),
    )
    NIVEL_RACIOCINIO_CHOICES: ClassVar[tuple[tuple[str, str], ...]] = (
        ("", "Padrão do modelo"),
        ("low", "Baixo"),
        ("medium", "Médio"),
        ("high", "Alto"),
    )
    CACHE_KEY = "ia:configuracao-global"

    id = models.PositiveSmallIntegerField(
        primary_key=True,
        default=1,
        editable=False,
        verbose_name="identificador",
        help_text="A configuração global usa sempre o identificador 1.",
    )
    provedor = models.CharField(
        max_length=20,
        choices=PROVEDOR_CHOICES,
        default="gemini",
        verbose_name="provedor",
        help_text="Provedor usado para as chamadas de IA.",
    )
    modelo = models.CharField(
        max_length=120,
        default="gemini-3.5-flash-lite",
        verbose_name="modelo",
        help_text="Nome do modelo usado pelo provedor.",
    )
    temperatura = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=Decimal("0.00"),
        verbose_name="temperatura",
        help_text="Grau de aleatoriedade da resposta, entre 0 e 1.",
    )
    max_tokens_saida = models.PositiveIntegerField(
        default=8192,
        verbose_name="máximo de tokens de saída",
        help_text="Limite de tokens produzidos em uma resposta.",
    )
    nivel_raciocinio = models.CharField(
        max_length=10,
        choices=NIVEL_RACIOCINIO_CHOICES,
        default="low",
        verbose_name="nível de raciocínio",
        help_text=(
            "Os níveis valem do Gemini 3 em diante. Com um modelo 2.5, deixe este campo vazio."
        ),
    )
    tentativas = models.PositiveSmallIntegerField(
        default=2,
        verbose_name="tentativas",
        help_text="Quantidade de tentativas permitidas para erros temporários.",
    )
    timeout_s = models.PositiveIntegerField(
        default=60,
        verbose_name="tempo limite em segundos",
        help_text="Tempo máximo de espera por chamada ao provedor.",
    )
    limite_mensal_usuario = models.PositiveIntegerField(
        default=100000,
        verbose_name="limite mensal por usuário",
        help_text="Quantidade máxima de tokens por usuário em um mês.",
    )
    aviso_percentual = models.PositiveSmallIntegerField(
        default=80,
        verbose_name="percentual de aviso",
        help_text="Percentual da cota que dispara um aviso ao usuário.",
    )
    reserva_minima_tokens = models.PositiveIntegerField(
        default=5000,
        verbose_name="reserva mínima de tokens",
        help_text="Quantidade mínima reservada antes de uma chamada.",
    )
    limite_mensal_sistema = models.PositiveIntegerField(
        default=20000000,
        verbose_name="limite mensal do sistema",
        help_text="Limite total mensal do sistema; zero desliga este limite.",
    )
    tamanho_maximo_mb = models.PositiveSmallIntegerField(
        default=10,
        verbose_name="tamanho máximo de arquivo em MB",
        help_text="Tamanho máximo permitido por arquivo enviado à IA.",
    )
    pdf_max_paginas = models.PositiveSmallIntegerField(
        default=10,
        verbose_name="máximo de páginas PDF",
        help_text="Quantidade máxima de páginas aceita em um PDF.",
    )
    reter_requisicoes_dias = models.PositiveIntegerField(
        default=60,
        verbose_name="retenção de requisições em dias",
        help_text="Quantidade de dias para reter registros de requisições.",
    )
    preco_entrada_milhao = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="preço de entrada por milhão",
        help_text="Preço em dólares por milhão de tokens de entrada, se informado.",
    )
    preco_saida_milhao = models.DecimalField(
        max_digits=12,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name="preço de saída por milhão",
        help_text="Preço em dólares por milhão de tokens de saída, se informado.",
    )
    atualizado_em = models.DateTimeField(
        auto_now=True,
        verbose_name="atualizado em",
        help_text="Data e hora da última atualização da configuração.",
    )

    @classmethod
    def obter(cls) -> ConfiguracaoIA:
        """Retorna a configuração única, usando cache por 30 segundos."""
        configuracao = cache.get(cls.CACHE_KEY)
        if configuracao is None:
            configuracao, _ = cls.objects.get_or_create(pk=1)
            cache.set(cls.CACHE_KEY, configuracao, timeout=30)
        return configuracao

    def save(self, *args: object, **kwargs: object) -> None:
        """Salva a configuração e invalida seu cache."""
        cache.delete(self.CACHE_KEY)
        super().save(*args, **kwargs)

    class Meta:
        """Metadados da configuração global única."""

        verbose_name = "Configuração de IA"
        verbose_name_plural = "Configurações de IA"


class ConfiguracaoIAUsuario(models.Model):
    """Preferências de IA específicas de um usuário."""

    objects = models.Manager()
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="configuracao_ia",
        verbose_name="usuário",
        help_text="Usuário ao qual estas preferências pertencem.",
    )
    ia_habilitada = models.BooleanField(
        default=True,
        verbose_name="IA habilitada",
        help_text="Define se o usuário pode utilizar os recursos de IA.",
    )
    limite_mensal = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="limite mensal",
        help_text="Vazio usa o padrão global; zero não permite tokens para este usuário.",
    )
    observacao = models.TextField(
        blank=True,
        verbose_name="observação",
        help_text="Observação administrativa sobre as preferências do usuário.",
    )

    class Meta:
        """Metadados das preferências individuais de IA."""

        verbose_name = "Configuração de IA do usuário"
        verbose_name_plural = "Configurações de IA dos usuários"


class RequisicaoIA(models.Model):
    """Auditoria de uma tentativa individual de chamada de IA."""

    objects = models.Manager()
    ORIGEM_CHOICES: ClassVar[tuple[tuple[str, str], ...]] = (
        ("site", "Site"),
        ("telegram", "Telegram"),
        ("comando", "Comando"),
    )
    SITUACAO_CHOICES: ClassVar[tuple[tuple[str, str], ...]] = (
        ("sucesso", "Sucesso"),
        ("resposta_invalida", "Resposta inválida"),
        ("erro_temporario", "Erro temporário"),
        ("erro_permanente", "Erro permanente"),
        ("tempo_esgotado", "Tempo esgotado"),
        ("bloqueada_cota", "Bloqueada por cota"),
        ("bloqueada_seguranca", "Bloqueada por segurança"),
        ("indisponivel", "Indisponível"),
        ("erro_configuracao", "Erro de configuração"),
    )

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="requisicoes_ia",
        verbose_name="usuário",
        help_text="Usuário responsável pela tentativa.",
    )
    referencia_tipo = models.ForeignKey(
        ContentType,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="tipo da referência",
        help_text="Tipo do objeto usado para agrupar a chamada.",
    )
    referencia_id = models.PositiveBigIntegerField(
        null=True,
        blank=True,
        verbose_name="identificador da referência",
        help_text="Identificador inteiro do objeto de referência.",
    )
    referencia = GenericForeignKey("referencia_tipo", "referencia_id")
    origem = models.CharField(
        max_length=20,
        choices=ORIGEM_CHOICES,
        default="site",
        verbose_name="origem",
        help_text="Canal que originou a chamada.",
    )
    finalidade = models.CharField(
        max_length=120,
        db_index=True,
        verbose_name="finalidade",
        help_text="Identificador app_acao da finalidade da chamada.",
    )
    provedor = models.CharField(
        max_length=20,
        verbose_name="provedor",
        help_text="Provedor usado na tentativa.",
    )
    modelo = models.CharField(
        max_length=120,
        verbose_name="modelo",
        help_text="Modelo usado na tentativa.",
    )
    versao_prompt = models.CharField(
        max_length=80,
        blank=True,
        verbose_name="versão do prompt",
        help_text="Versão identificadora das instruções usadas.",
    )
    tentativa = models.PositiveSmallIntegerField(
        verbose_name="tentativa",
        help_text="Número sequencial da tentativa desta chamada.",
    )
    situacao = models.CharField(
        max_length=24,
        choices=SITUACAO_CHOICES,
        verbose_name="situação",
        help_text="Resultado da tentativa.",
    )
    tokens_entrada = models.PositiveBigIntegerField(
        default=0,
        verbose_name="tokens de entrada",
        help_text="Tokens de entrada informados pelo provedor.",
    )
    tokens_saida = models.PositiveBigIntegerField(
        default=0,
        verbose_name="tokens de saída",
        help_text="Tokens de saída, incluindo raciocínio quando informado.",
    )
    tokens_raciocinio = models.PositiveBigIntegerField(
        default=0,
        verbose_name="tokens de raciocínio",
        help_text="Tokens de raciocínio informativos.",
    )
    tokens_total = models.PositiveBigIntegerField(
        default=0,
        verbose_name="tokens totais",
        help_text="Soma dos tokens de entrada e saída.",
    )
    custo_estimado = models.DecimalField(
        max_digits=14,
        decimal_places=6,
        default=Decimal("0"),
        verbose_name="custo estimado",
        help_text="Custo estimado em dólares da tentativa.",
    )
    duracao_ms = models.PositiveIntegerField(
        default=0,
        verbose_name="duração em milissegundos",
        help_text="Tempo decorrido na tentativa.",
    )
    motivo_fim = models.CharField(
        max_length=80,
        blank=True,
        verbose_name="motivo do fim",
        help_text="Motivo de término informado pelo provedor.",
    )
    arquivo_mime = models.CharField(
        max_length=120,
        blank=True,
        verbose_name="tipo MIME do arquivo",
        help_text="Tipo MIME do arquivo enviado, quando houver.",
    )
    arquivo_tamanho = models.PositiveBigIntegerField(
        default=0,
        verbose_name="tamanho do arquivo",
        help_text="Tamanho do arquivo em bytes, quando houver.",
    )
    arquivo_hash = models.CharField(
        max_length=64,
        blank=True,
        verbose_name="hash do arquivo",
        help_text="Hash SHA-256 do arquivo, quando houver.",
    )
    resposta = models.TextField(
        max_length=20000,
        blank=True,
        verbose_name="resposta",
        help_text="Resposta cortada em no máximo 20 mil caracteres.",
    )
    erro = models.TextField(
        blank=True,
        verbose_name="erro",
        help_text="Mensagem do erro, sem dados sensíveis desnecessários.",
    )
    contexto_hash = models.CharField(
        max_length=64,
        blank=True,
        verbose_name="hash do contexto",
        help_text="Hash SHA-256 do texto enviado, sem guardar o texto completo.",
    )
    criado_em = models.DateTimeField(
        auto_now_add=True,
        verbose_name="criado em",
        help_text="Data e hora da tentativa.",
    )

    class Meta:
        verbose_name = "Requisição de IA"
        verbose_name_plural = "Requisições de IA"
        indexes = [
            models.Index(fields=("usuario", "-criado_em"), name="ia_req_user_date_idx"),
            models.Index(fields=("situacao", "-criado_em"), name="ia_req_status_date_idx"),
            models.Index(
                fields=("referencia_tipo", "referencia_id", "-criado_em"),
                name="ia_req_ref_date_idx",
            ),
        ]


class ConsumoIA(models.Model):
    """Consumo agregado de tokens de um usuário em um mês."""

    objects = models.Manager()
    dono = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="consumos_ia",
        verbose_name="dono da cota",
        help_text="Usuário dono do consumo mensal.",
    )
    mes = models.DateField(
        verbose_name="mês",
        help_text="Primeiro dia do mês ao qual o consumo pertence.",
    )
    tokens_entrada = models.PositiveBigIntegerField(
        default=0,
        verbose_name="tokens de entrada",
        help_text="Total mensal de tokens de entrada.",
    )
    tokens_saida = models.PositiveBigIntegerField(
        default=0,
        verbose_name="tokens de saída",
        help_text="Total mensal de tokens de saída.",
    )
    tokens_total = models.PositiveBigIntegerField(
        default=0,
        verbose_name="tokens totais",
        help_text="Total mensal de tokens de entrada e saída.",
    )
    custo_estimado = models.DecimalField(
        max_digits=14,
        decimal_places=6,
        default=Decimal("0"),
        verbose_name="custo estimado",
        help_text="Custo mensal estimado em dólares.",
    )
    requisicoes = models.PositiveIntegerField(
        default=0,
        verbose_name="requisições",
        help_text="Quantidade mensal de tentativas registradas.",
    )

    class Meta:
        verbose_name = "Consumo de IA"
        verbose_name_plural = "Consumos de IA"
        constraints = [
            models.UniqueConstraint(fields=("dono", "mes"), name="ia_consumo_dono_mes_uniq"),
        ]
