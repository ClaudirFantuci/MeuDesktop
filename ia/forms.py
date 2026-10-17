"""Forms das telas administrativas e de consumo de IA."""

from django import forms

from ia.models import ConfiguracaoIA, ConfiguracaoIAUsuario


class ConfiguracaoIAForm(forms.ModelForm):
    """Formulário da configuração global de IA."""

    class Meta:
        model = ConfiguracaoIA
        fields = [
            "provedor",
            "modelo",
            "temperatura",
            "max_tokens_saida",
            "nivel_raciocinio",
            "tentativas",
            "timeout_s",
            "limite_mensal_usuario",
            "aviso_percentual",
            "reserva_minima_tokens",
            "limite_mensal_sistema",
            "tamanho_maximo_mb",
            "pdf_max_paginas",
            "reter_requisicoes_dias",
            "preco_entrada_milhao",
            "preco_saida_milhao",
        ]


class ConfiguracaoIAUsuarioForm(forms.ModelForm):
    """Formulário das preferências individuais de IA."""

    class Meta:
        model = ConfiguracaoIAUsuario
        fields = ["ia_habilitada", "limite_mensal", "observacao"]
        widgets = {
            "observacao": forms.Textarea(attrs={"rows": 4}),
        }
