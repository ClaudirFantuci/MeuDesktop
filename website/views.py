from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, TemplateView, UpdateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

# Django braces faz o GroupRequiredMixin para controle de acesso por Grupo
from braces.views import GroupRequiredMixin

from .models import (
    Armazenamento,
    Fabricante,
    Fonte,
    HistoricoMontagem,
    MemoriaRAM,
    Montagem,
    PlacaDeVideo,
    PlacaMae,
    Processador,
)

PAGINACAO_PADRAO = 12

# Campos de componentes de uma Montagem, usados para registrar o histórico
# (rótulo amigável usado nas mensagens de histórico)
CAMPOS_COMPONENTES = [
    ("processador", "Processador"),
    ("placa_mae", "Placa-mãe"),
    ("memoria_ram", "Memória RAM"),
    ("placa_de_video", "Placa de Vídeo"),
    ("armazenamento", "Armazenamento"),
    ("fonte", "Fonte"),
]


class BaseLoginMixin(LoginRequiredMixin):
    """Exige apenas que o usuário esteja autenticado."""
    login_url = reverse_lazy("login")


class AdminRequiredMixin(GroupRequiredMixin):
    """Exige que o usuário esteja autenticado e pertença ao grupo Administrador.

    Visitantes anônimos são redirecionados para o login; usuários autenticados
    sem o grupo recebem 403 (em vez de ficarem presos em um loop de login).
    """
    group_required = ["Administrador"]
    login_url = reverse_lazy("login")
    raise_exception = True
    redirect_unauthenticated_users = True


class IndexView(TemplateView):
    template_name = "website/model.html"

    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)

        # QuerySets reaproveitados para exibir cadastros recentes na home
        context["ultimos_processadores"] = Processador.objects.select_related("fabricante")[:5]
        context["ultimas_placas_mae"] = PlacaMae.objects.select_related("fabricante")[:5]
        context["total_fabricantes"] = Fabricante.objects.count()

        if self.request.user.is_authenticated:
            context["minhas_montagens"] = (
                Montagem.objects.filter(usuario=self.request.user)
                .select_related("processador", "placa_mae")[:5]
            )
        return context


class ContatoView(TemplateView):
    template_name = "website/contato.html"


class SobreView(TemplateView):
    template_name = "website/sobre.html"


###############################################################
# Fabricante
###############################################################


class FabricanteCreate(AdminRequiredMixin, CreateView):
    model = Fabricante
    fields = ["nome", "website"]
    template_name = "website/fabricante/form.html"
    success_url = reverse_lazy("fabricante-list")
    extra_context = {
        "titulo": "Cadastro de Fabricante",
        "botao": "Criar Fabricante",
    }


class FabricanteUpdate(AdminRequiredMixin, UpdateView):
    model = Fabricante
    fields = ["nome", "website"]
    template_name = "website/fabricante/form.html"
    success_url = reverse_lazy("fabricante-list")
    extra_context = {
        "titulo": "Editar Fabricante",
        "botao": "Atualizar Fabricante",
    }


class FabricanteDelete(AdminRequiredMixin, DeleteView):
    model = Fabricante
    template_name = "website/fabricante/confirm_delete.html"
    success_url = reverse_lazy("fabricante-list")


class FabricanteList(BaseLoginMixin, ListView):
    model = Fabricante
    template_name = "website/fabricante/list.html"
    context_object_name = "fabricantes"
    paginate_by = PAGINACAO_PADRAO


class FabricanteDetail(BaseLoginMixin, DetailView):
    model = Fabricante
    template_name = "website/fabricante/detail.html"


###############################################################
# Processador
###############################################################


class ProcessadorCreate(AdminRequiredMixin, CreateView):
    model = Processador
    fields = [
        "nome",
        "fabricante",
        "socket",
        "cores",
        "threads",
        "frequencia_base",
        "frequencia_turbo",
        "tdp",
        "tem_video_integrado",
        "geracao",
        "preco",
        "descricao",
        "disponivel",
    ]
    template_name = "website/processador/form.html"
    success_url = reverse_lazy("processador-list")
    extra_context = {
        "titulo": "Cadastro de Processador",
        "botao": "Criar Processador",
    }


class ProcessadorUpdate(AdminRequiredMixin, UpdateView):
    model = Processador
    fields = ProcessadorCreate.fields
    template_name = "website/processador/form.html"
    success_url = reverse_lazy("processador-list")
    extra_context = {
        "titulo": "Editar Processador",
        "botao": "Atualizar Processador",
    }


class ProcessadorDelete(AdminRequiredMixin, DeleteView):
    model = Processador
    template_name = "website/processador/confirm_delete.html"
    success_url = reverse_lazy("processador-list")


class ProcessadorList(BaseLoginMixin, ListView):
    model = Processador
    template_name = "website/processador/list.html"
    context_object_name = "processadores"
    paginate_by = PAGINACAO_PADRAO

    def get_queryset(self):
        # select_related evita uma query extra por linha para buscar o fabricante
        return super().get_queryset().select_related("fabricante")


class ProcessadorDetail(BaseLoginMixin, DetailView):
    model = Processador
    template_name = "website/processador/detail.html"

    def get_queryset(self):
        return super().get_queryset().select_related("fabricante")


###############################################################
# PlacaMae
###############################################################


class PlacaMaeCreate(AdminRequiredMixin, CreateView):
    model = PlacaMae
    fields = [
        "nome",
        "fabricante",
        "socket",
        "chipset",
        "tipo_memoria",
        "slots_ram",
        "max_memoria_gb",
        "frequencia_max_ram",
        "form_factor",
        "tem_slot_m2",
        "quantidade_m2",
        "portas_sata",
        "slot_pcie_x16",
        "preco",
        "descricao",
        "disponivel",
    ]
    template_name = "website/placamae/form.html"
    success_url = reverse_lazy("placamae-list")
    extra_context = {
        "titulo": "Cadastro de Placa-mãe",
        "botao": "Criar Placa-mãe",
    }


class PlacaMaeUpdate(AdminRequiredMixin, UpdateView):
    model = PlacaMae
    fields = PlacaMaeCreate.fields
    template_name = "website/placamae/form.html"
    success_url = reverse_lazy("placamae-list")
    extra_context = {
        "titulo": "Editar Placa-mãe",
        "botao": "Atualizar Placa-mãe",
    }


class PlacaMaeDelete(AdminRequiredMixin, DeleteView):
    model = PlacaMae
    template_name = "website/placamae/confirm_delete.html"
    success_url = reverse_lazy("placamae-list")


class PlacaMaeList(BaseLoginMixin, ListView):
    model = PlacaMae
    template_name = "website/placamae/list.html"
    context_object_name = "placas_mae"
    paginate_by = PAGINACAO_PADRAO

    def get_queryset(self):
        return super().get_queryset().select_related("fabricante")


class PlacaMaeDetail(BaseLoginMixin, DetailView):
    model = PlacaMae
    template_name = "website/placamae/detail.html"

    def get_queryset(self):
        return super().get_queryset().select_related("fabricante")


###############################################################
# MemoriaRAM
###############################################################


class MemoriaRAMCreate(AdminRequiredMixin, CreateView):
    model = MemoriaRAM
    fields = [
        "nome",
        "fabricante",
        "tipo",
        "capacidade_gb",
        "quantidade_modulos",
        "frequencia_mhz",
        "latencia",
        "preco",
        "descricao",
        "disponivel",
    ]
    template_name = "website/memoriam/form.html"
    success_url = reverse_lazy("memoriam-list")
    extra_context = {
        "titulo": "Cadastro de Memória RAM",
        "botao": "Criar Memória RAM",
    }


class MemoriaRAMUpdate(AdminRequiredMixin, UpdateView):
    model = MemoriaRAM
    fields = MemoriaRAMCreate.fields
    template_name = "website/memoriam/form.html"
    success_url = reverse_lazy("memoriam-list")
    extra_context = {
        "titulo": "Editar Memória RAM",
        "botao": "Atualizar Memória RAM",
    }


class MemoriaRAMDelete(AdminRequiredMixin, DeleteView):
    model = MemoriaRAM
    template_name = "website/memoriam/confirm_delete.html"
    success_url = reverse_lazy("memoriam-list")


class MemoriaRAMList(BaseLoginMixin, ListView):
    model = MemoriaRAM
    template_name = "website/memoriam/list.html"
    context_object_name = "memorias_ram"
    paginate_by = PAGINACAO_PADRAO

    def get_queryset(self):
        return super().get_queryset().select_related("fabricante")


class MemoriaRAMDetail(BaseLoginMixin, DetailView):
    model = MemoriaRAM
    template_name = "website/memoriam/detail.html"

    def get_queryset(self):
        return super().get_queryset().select_related("fabricante")


###############################################################
# PlacaDeVideo
###############################################################


class PlacaDeVideoCreate(AdminRequiredMixin, CreateView):
    model = PlacaDeVideo
    fields = [
        "nome",
        "fabricante",
        "gpu_chip",
        "memoria_gb",
        "tipo_memoria",
        "interface",
        "consumo_watts",
        "fonte_recomendada_watts",
        "comprimento_mm",
        "preco",
        "descricao",
        "disponivel",
    ]
    template_name = "website/placavideo/form.html"
    success_url = reverse_lazy("placavideo-list")
    extra_context = {
        "titulo": "Cadastro de Placa de Vídeo",
        "botao": "Criar Placa de Vídeo",
    }


class PlacaDeVideoUpdate(AdminRequiredMixin, UpdateView):
    model = PlacaDeVideo
    fields = PlacaDeVideoCreate.fields
    template_name = "website/placavideo/form.html"
    success_url = reverse_lazy("placavideo-list")
    extra_context = {
        "titulo": "Editar Placa de Vídeo",
        "botao": "Atualizar Placa de Vídeo",
    }


class PlacaDeVideoDelete(AdminRequiredMixin, DeleteView):
    model = PlacaDeVideo
    template_name = "website/placavideo/confirm_delete.html"
    success_url = reverse_lazy("placavideo-list")


class PlacaDeVideoList(BaseLoginMixin, ListView):
    model = PlacaDeVideo
    template_name = "website/placavideo/list.html"
    context_object_name = "placas_video"
    paginate_by = PAGINACAO_PADRAO

    def get_queryset(self):
        return super().get_queryset().select_related("fabricante")


class PlacaDeVideoDetail(BaseLoginMixin, DetailView):
    model = PlacaDeVideo
    template_name = "website/placavideo/detail.html"

    def get_queryset(self):
        return super().get_queryset().select_related("fabricante")


###############################################################
# Armazenamento
###############################################################


class ArmazenamentoCreate(AdminRequiredMixin, CreateView):
    model = Armazenamento
    fields = [
        "nome",
        "fabricante",
        "tipo",
        "interface",
        "capacidade_gb",
        "velocidade_leitura",
        "velocidade_escrita",
        "preco",
        "descricao",
        "disponivel",
    ]
    template_name = "website/armazenamento/form.html"
    success_url = reverse_lazy("armazenamento-list")
    extra_context = {
        "titulo": "Cadastro de Armazenamento",
        "botao": "Criar Armazenamento",
    }


class ArmazenamentoUpdate(AdminRequiredMixin, UpdateView):
    model = Armazenamento
    fields = ArmazenamentoCreate.fields
    template_name = "website/armazenamento/form.html"
    success_url = reverse_lazy("armazenamento-list")
    extra_context = {
        "titulo": "Editar Armazenamento",
        "botao": "Atualizar Armazenamento",
    }


class ArmazenamentoDelete(AdminRequiredMixin, DeleteView):
    model = Armazenamento
    template_name = "website/armazenamento/confirm_delete.html"
    success_url = reverse_lazy("armazenamento-list")


class ArmazenamentoList(BaseLoginMixin, ListView):
    model = Armazenamento
    template_name = "website/armazenamento/list.html"
    context_object_name = "armazenamentos"
    paginate_by = PAGINACAO_PADRAO

    def get_queryset(self):
        return super().get_queryset().select_related("fabricante")


class ArmazenamentoDetail(BaseLoginMixin, DetailView):
    model = Armazenamento
    template_name = "website/armazenamento/detail.html"

    def get_queryset(self):
        return super().get_queryset().select_related("fabricante")


###############################################################
# Fonte
###############################################################


class FonteCreate(AdminRequiredMixin, CreateView):
    model = Fonte
    fields = [
        "nome",
        "fabricante",
        "potencia_watts",
        "certificacao",
        "modular",
        "preco",
        "descricao",
        "disponivel",
    ]
    template_name = "website/fonte/form.html"
    success_url = reverse_lazy("fonte-list")
    extra_context = {
        "titulo": "Cadastro de Fonte",
        "botao": "Criar Fonte",
    }


class FonteUpdate(AdminRequiredMixin, UpdateView):
    model = Fonte
    fields = FonteCreate.fields
    template_name = "website/fonte/form.html"
    success_url = reverse_lazy("fonte-list")
    extra_context = {
        "titulo": "Editar Fonte",
        "botao": "Atualizar Fonte",
    }


class FonteDelete(AdminRequiredMixin, DeleteView):
    model = Fonte
    template_name = "website/fonte/confirm_delete.html"
    success_url = reverse_lazy("fonte-list")


class FonteList(BaseLoginMixin, ListView):
    model = Fonte
    template_name = "website/fonte/list.html"
    context_object_name = "fontes"
    paginate_by = PAGINACAO_PADRAO

    def get_queryset(self):
        return super().get_queryset().select_related("fabricante")


class FonteDetail(BaseLoginMixin, DetailView):
    model = Fonte
    template_name = "website/fonte/detail.html"

    def get_queryset(self):
        return super().get_queryset().select_related("fabricante")


###############################################################
# Montagem (movimento: cada usuário monta e finaliza o próprio PC)
###############################################################


class MontagemCreate(BaseLoginMixin, CreateView):
    model = Montagem
    fields = [
        "nome",
        "processador",
        "placa_mae",
        "memoria_ram",
        "placa_de_video",
        "armazenamento",
        "fonte",
    ]
    template_name = "website/montagem/form.html"
    success_url = reverse_lazy("montagem-list")
    extra_context = {
        "titulo": "Nova Montagem",
        "botao": "Criar Montagem",
    }

    def form_valid(self, form):
        # "guarda" o usuário logado como dono da montagem
        form.instance.usuario = self.request.user

        # executa o INSERT no banco
        url_sucesso = super().form_valid(form)

        HistoricoMontagem.objects.create(
            montagem=self.object,
            acao="Criada",
            componente_tipo="Montagem",
            componente_nome=self.object.nome,
        )
        for campo, rotulo in CAMPOS_COMPONENTES:
            valor = getattr(self.object, campo)
            if valor:
                HistoricoMontagem.objects.create(
                    montagem=self.object,
                    acao="Adicionado",
                    componente_tipo=rotulo,
                    componente_nome=str(valor),
                )
        return url_sucesso


class MontagemUpdate(BaseLoginMixin, UpdateView):
    model = Montagem
    fields = MontagemCreate.fields
    template_name = "website/montagem/form.html"
    success_url = reverse_lazy("montagem-list")
    extra_context = {
        "titulo": "Editar Montagem",
        "botao": "Atualizar Montagem",
    }

    def get_queryset(self):
        # o usuário só pode editar as próprias montagens
        return super().get_queryset().filter(usuario=self.request.user)

    def form_valid(self, form):
        # busca o estado anterior no banco antes do UPDATE ser executado
        anterior = Montagem.objects.get(pk=self.object.pk)

        url_sucesso = super().form_valid(form)

        # registra no histórico cada componente que mudou (movimento)
        for campo, rotulo in CAMPOS_COMPONENTES:
            valor_antigo = getattr(anterior, campo)
            valor_novo = getattr(self.object, campo)
            if valor_antigo == valor_novo:
                continue

            if valor_antigo is None:
                acao, nome = "Adicionado", str(valor_novo)
            elif valor_novo is None:
                acao, nome = "Removido", str(valor_antigo)
            else:
                acao, nome = "Alterado", f"{valor_antigo} \u2192 {valor_novo}"

            HistoricoMontagem.objects.create(
                montagem=self.object,
                acao=acao,
                componente_tipo=rotulo,
                componente_nome=nome,
            )
        return url_sucesso


class MontagemDelete(BaseLoginMixin, DeleteView):
    model = Montagem
    template_name = "website/montagem/confirm_delete.html"
    success_url = reverse_lazy("montagem-list")

    def get_queryset(self):
        return super().get_queryset().filter(usuario=self.request.user)


class MontagemList(BaseLoginMixin, ListView):
    model = Montagem
    template_name = "website/montagem/list.html"
    context_object_name = "montagens"
    paginate_by = PAGINACAO_PADRAO

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(usuario=self.request.user)
            .select_related(
                "processador", "placa_mae", "memoria_ram",
                "placa_de_video", "armazenamento", "fonte",
            )
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        total = self.get_queryset().count()
        finalizadas = self.get_queryset().filter(finalizada=True).count()
        context["total_montagens"] = total
        context["total_finalizadas"] = finalizadas
        context["total_em_andamento"] = total - finalizadas
        return context


class MontagemDetail(BaseLoginMixin, DetailView):
    model = Montagem
    template_name = "website/montagem/detail.html"

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .filter(usuario=self.request.user)
            .select_related(
                "processador", "placa_mae", "memoria_ram",
                "placa_de_video", "armazenamento", "fonte",
            )
        )


class MontagemFinalizar(BaseLoginMixin, View):
    """Verifica compatibilidade básica e finaliza a montagem (UC05 + UC07)."""

    def post(self, request, pk):
        montagem = get_object_or_404(Montagem, pk=pk, usuario=request.user)

        if montagem.finalizada:
            messages.info(request, "Esta montagem já está finalizada.")
            return redirect("montagem-detail", pk=montagem.pk)

        obrigatorios = [montagem.processador, montagem.placa_mae, montagem.memoria_ram, montagem.fonte]
        if not all(obrigatorios):
            messages.error(
                request,
                "Selecione ao menos processador, placa-mãe, memória RAM e fonte antes de finalizar.",
            )
            return redirect("montagem-detail", pk=montagem.pk)

        if montagem.processador.socket != montagem.placa_mae.socket:
            messages.error(request, "O processador e a placa-mãe têm sockets incompatíveis.")
            return redirect("montagem-detail", pk=montagem.pk)

        if montagem.memoria_ram.tipo != montagem.placa_mae.tipo_memoria:
            messages.error(request, "O tipo de memória RAM não é compatível com a placa-mãe.")
            return redirect("montagem-detail", pk=montagem.pk)

        montagem.finalizada = True
        montagem.save()

        HistoricoMontagem.objects.create(
            montagem=montagem,
            acao="Finalizada",
            componente_tipo="Montagem",
            componente_nome=montagem.nome,
        )
        messages.success(request, "Montagem finalizada com sucesso!")
        return redirect("montagem-detail", pk=montagem.pk)
