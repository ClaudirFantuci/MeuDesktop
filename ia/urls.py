from django.urls import path

from .manutencao import manutencao
from ia.views import (
    ConfiguracaoIAUpdateView,
    ConfiguracaoIAUsuarioListView,
    ConfiguracaoIAUsuarioPadraoView,
    ConfiguracaoIAUsuarioUpdateView,
    MeuConsumoIAView,
    RequisicaoIADetailView,
    RequisicaoIAListView,
)


app_name = "ia"

urlpatterns = [
    path("requisicoes/", RequisicaoIAListView.as_view(), name="requisicoes"),
    path("requisicoes/<int:pk>/", RequisicaoIADetailView.as_view(), name="requisicao-detail"),
    path("consumo/", MeuConsumoIAView.as_view(), name="consumo"),
    path("configuracao/", ConfiguracaoIAUpdateView.as_view(), name="configuracao"),
    path("usuarios/", ConfiguracaoIAUsuarioListView.as_view(), name="usuarios"),
    path("usuarios/<int:pk>/", ConfiguracaoIAUsuarioUpdateView.as_view(), name="usuario-edit"),
    path("usuarios/<int:pk>/padrao/", ConfiguracaoIAUsuarioPadraoView.as_view(), name="usuario-padrao"),
    path("manutencao/", manutencao, name="manutencao"),
]
