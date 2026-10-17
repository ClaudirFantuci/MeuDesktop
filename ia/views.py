"""Views das telas de operação e administração da camada de IA."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.views import redirect_to_login
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Q, QuerySet, Sum
from django.db.models.functions import Coalesce
from django.http import HttpRequest, HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView, UpdateView, View

from ia.chamada import testar_conexao
from ia.cota import limite_do_usuario, mes_atual, situacao_da_cota
from ia.forms import ConfiguracaoIAForm, ConfiguracaoIAUsuarioForm
from ia.models import ConfiguracaoIA, ConfiguracaoIAUsuario, ConsumoIA, RequisicaoIA
from ia.provedores.base import ErroIA


User = get_user_model()


class SuperuserRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Restringe uma tela a superusuários e preserva o redirecionamento de login."""

    login_url = reverse_lazy("login")
    raise_exception = True

    def test_func(self) -> bool:
        return bool(self.request.user.is_superuser)

    def handle_no_permission(self) -> HttpResponse:
        if not self.request.user.is_authenticated:
            return redirect_to_login(
                self.request.get_full_path(),
                self.get_login_url(),
                self.get_redirect_field_name(),
            )
        return HttpResponseForbidden()


class RequisicaoIAListView(SuperuserRequiredMixin, ListView):
    """Lista paginada de tentativas de IA com filtros e resumo mensal."""

    model = RequisicaoIA
    template_name = "ia/requisicao_list.html"
    context_object_name = "requisicoes"
    paginate_by = 20

    def get_queryset(self) -> QuerySet[RequisicaoIA]:
        queryset = (
            RequisicaoIA.objects.select_related("usuario", "referencia_tipo")
            .order_by("-criado_em")
        )
        params = self.request.GET
        if params.get("usuario"):
            queryset = queryset.filter(usuario_id=params["usuario"])
        if params.get("situacao"):
            queryset = queryset.filter(situacao=params["situacao"])
        if params.get("finalidade"):
            queryset = queryset.filter(finalidade__icontains=params["finalidade"])
        if params.get("origem"):
            queryset = queryset.filter(origem=params["origem"])
        if params.get("inicio"):
            try:
                queryset = queryset.filter(
                    criado_em__date__gte=date.fromisoformat(params["inicio"])
                )
            except ValueError:
                pass
        if params.get("fim"):
            try:
                queryset = queryset.filter(criado_em__date__lte=date.fromisoformat(params["fim"]))
            except ValueError:
                pass
        return queryset

    def _resumo_mes(self) -> dict[str, object]:
        inicio = mes_atual()
        queryset = RequisicaoIA.objects.filter(criado_em__date__gte=inicio)
        resumo = queryset.aggregate(
            tokens=Coalesce(Sum("tokens_total"), 0),
            custo=Coalesce(Sum("custo_estimado"), Decimal("0")),
            erros=Count("id", filter=~Q(situacao="sucesso")),
        )
        referencias = (
            queryset.filter(referencia_tipo__isnull=False, referencia_id__isnull=False)
            .values("referencia_tipo", "referencia_id")
            .annotate(
                custo=Coalesce(Sum("custo_estimado"), Decimal("0")),
                tokens=Sum("tokens_total"),
            )
            .order_by("-custo", "-tokens")[:5]
        )
        referencias_maiores = []
        for item in referencias:
            tipo = RequisicaoIA.objects.filter(
                referencia_tipo_id=item["referencia_tipo"], referencia_id=item["referencia_id"]
            ).first()
            try:
                referencia = tipo.referencia if tipo else None
                nome = str(referencia) if referencia is not None else "—"
            except (AttributeError, ObjectDoesNotExist, TypeError, ValueError):
                nome = "—"
            referencias_maiores.append({"nome": nome, "custo": item["custo"]})

        usuarios = (
            queryset.values("usuario_id", "usuario__username")
            .annotate(
                custo=Coalesce(Sum("custo_estimado"), Decimal("0")),
                tokens=Sum("tokens_total"),
            )
            .order_by("-custo", "-tokens")[:5]
        )
        return {
            "tokens": resumo["tokens"],
            "custo": resumo["custo"],
            "erros": resumo["erros"],
            "referencias": referencias_maiores,
            "usuarios": usuarios,
        }

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        context.update(
            {
                "usuarios_filtro": User.objects.order_by("username"),
                "situacoes": RequisicaoIA.SITUACAO_CHOICES,
                "origens": RequisicaoIA.ORIGEM_CHOICES,
                "resumo": self._resumo_mes(),
            }
        )
        return context


class RequisicaoIADetailView(SuperuserRequiredMixin, DetailView):
    """Exibe a resposta e o erro de uma tentativa de IA."""

    model = RequisicaoIA
    template_name = "ia/requisicao_detail.html"
    context_object_name = "requisicao"

    def get_queryset(self) -> QuerySet[RequisicaoIA]:
        return super().get_queryset().select_related("usuario", "referencia_tipo")


class MeuConsumoIAView(LoginRequiredMixin, ListView):
    """Exibe a cota atual e as últimas requisições do usuário logado."""

    model = RequisicaoIA
    template_name = "ia/meu_consumo.html"
    context_object_name = "requisicoes"
    login_url = reverse_lazy("login")

    def get_queryset(self) -> QuerySet[RequisicaoIA]:
        return RequisicaoIA.objects.filter(usuario=self.request.user).order_by("-criado_em")[:20]

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        configuracao = ConfiguracaoIA.obter()
        cota = situacao_da_cota(self.request.user)
        percentual = min(cota.percentual, Decimal("100"))
        context.update(
            {
                "cota": cota,
                "percentual_barra": percentual,
                "aviso_percentual": configuracao.aviso_percentual,
            }
        )
        return context


class ConfiguracaoIAUpdateView(SuperuserRequiredMixin, UpdateView):
    """Edita a configuração global e permite testar a conexão."""

    model = ConfiguracaoIA
    form_class = ConfiguracaoIAForm
    template_name = "ia/configuracao_form.html"
    success_url = reverse_lazy("ia:configuracao")
    object: ConfiguracaoIA

    def get_object(self, queryset: QuerySet[ConfiguracaoIA] | None = None) -> ConfiguracaoIA:
        return ConfiguracaoIA.obter()

    def post(self, request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
        self.object = self.get_object()
        if "testar_conexao" not in request.POST:
            return super().post(request, *args, **kwargs)
        form = self.get_form()
        if not form.is_valid():
            return self.form_invalid(form)
        self.object = form.save()
        try:
            testar_conexao(request.user)
        except ErroIA as erro:
            messages.error(request, f"Falha no teste de conexão: {erro}")
        else:
            messages.success(request, "Conexão com o provedor testada com sucesso.")
        return redirect(self.success_url)


class ConfiguracaoIAUsuarioListView(SuperuserRequiredMixin, ListView):
    """Lista usuários com situação da IA, limite efetivo e uso do mês."""

    template_name = "ia/usuario_list.html"
    context_object_name = "usuarios_ia"

    def get_queryset(self) -> QuerySet[User]:
        return User.objects.order_by("username")

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        configuracao = ConfiguracaoIA.obter()
        mes = mes_atual()
        itens = []
        for usuario in context["usuarios_ia"]:
            preferencia = ConfiguracaoIAUsuario.objects.filter(usuario=usuario).first()
            limite = limite_do_usuario(usuario)
            consumo = ConsumoIA.objects.filter(dono=usuario, mes=mes).first()
            itens.append(
                {
                    "usuario": usuario,
                    "preferencia": preferencia,
                    "limite": limite,
                    "limite_formatado": f"{limite:,}".replace(",", "."),
                    "limite_tipo": (
                        "próprio"
                        if preferencia and preferencia.limite_mensal is not None
                        else "padrão"
                    ),
                    "uso": consumo.tokens_total if consumo else 0,
                    "ligada": preferencia is None or preferencia.ia_habilitada,
                }
            )
        context["usuarios_ia"] = itens
        context["limite_padrao"] = configuracao.limite_mensal_usuario
        return context


class ConfiguracaoIAUsuarioUpdateView(SuperuserRequiredMixin, UpdateView):
    """Edita as preferências de IA de um usuário."""

    model = ConfiguracaoIAUsuario
    form_class = ConfiguracaoIAUsuarioForm
    template_name = "ia/usuario_form.html"
    context_object_name = "preferencia"
    success_url = reverse_lazy("ia:usuarios")

    def get_object(
        self,
        queryset: QuerySet[ConfiguracaoIAUsuario] | None = None,
    ) -> ConfiguracaoIAUsuario:
        usuario = get_object_or_404(User, pk=self.kwargs["pk"])
        preferencia, _ = ConfiguracaoIAUsuario.objects.get_or_create(usuario=usuario)
        return preferencia

    def get_context_data(self, **kwargs: object) -> dict[str, object]:
        context = super().get_context_data(**kwargs)
        context["usuario"] = self.object.usuario
        return context


class ConfiguracaoIAUsuarioPadraoView(SuperuserRequiredMixin, View):
    """Remove a exceção individual e restaura o limite padrão."""

    def post(self, request: HttpRequest, *args: object, **kwargs: object) -> HttpResponse:
        """Apaga a configuração individual e redireciona para a lista."""
        usuario = get_object_or_404(User, pk=kwargs["pk"])
        ConfiguracaoIAUsuario.objects.filter(usuario=usuario).delete()
        messages.success(request, "O usuário voltou a usar a configuração padrão de IA.")
        return redirect("ia:usuarios")
