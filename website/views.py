from django.urls import reverse_lazy
from django.views.generic import CreateView, DeleteView, TemplateView, UpdateView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from .models import (
    Armazenamento,
    Fabricante,
    Fonte,
    MemoriaRAM,
    PlacaDeVideo,
    PlacaMae,
    Processador,
)


class IndexView(TemplateView):
    template_name = "website/model.html"


class ContatoView(TemplateView):
    template_name = "website/contato.html"


class FabricanteCreate(CreateView):
    model = Fabricante
    fields = ["nome", "website"]
    template_name = "website/fabricante/form.html"
    success_url = reverse_lazy("fabricante-list")
    extra_context = {
        "titulo": "Cadastro de Fabricante",
        "botao": "Criar Fabricante",
    }


class FabricanteUpdate(UpdateView):
    model = Fabricante
    fields = ["nome", "website"]
    template_name = "website/fabricante/form.html"
    success_url = reverse_lazy("fabricante-list")
    extra_context = {
        "titulo": "Editar Fabricante",
        "botao": "Atualizar Fabricante",
    }


class FabricanteDelete(DeleteView):
    model = Fabricante
    template_name = "website/fabricante/confirm_delete.html"
    success_url = reverse_lazy("fabricante-list")


class FabricanteList(ListView):
    model = Fabricante
    template_name = "website/fabricante/list.html"
    context_object_name = "fabricantes"


class FabricanteDetail(DetailView):
    model = Fabricante
    template_name = "website/fabricante/detail.html"


class ProcessadorCreate(CreateView):
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


class ProcessadorUpdate(UpdateView):
    model = Processador
    fields = ProcessadorCreate.fields
    template_name = "website/processador/form.html"
    success_url = reverse_lazy("processador-list")
    extra_context = {
        "titulo": "Editar Processador",
        "botao": "Atualizar Processador",
    }


class ProcessadorDelete(DeleteView):
    model = Processador
    template_name = "website/processador/confirm_delete.html"
    success_url = reverse_lazy("processador-list")


class ProcessadorList(ListView):
    model = Processador
    template_name = "website/processador/list.html"
    context_object_name = "processadores"


class ProcessadorDetail(DetailView):
    model = Processador
    template_name = "website/processador/detail.html"


class PlacaMaeCreate(CreateView):
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


class PlacaMaeUpdate(UpdateView):
    model = PlacaMae
    fields = PlacaMaeCreate.fields
    template_name = "website/placamae/form.html"
    success_url = reverse_lazy("placamae-list")
    extra_context = {
        "titulo": "Editar Placa-mãe",
        "botao": "Atualizar Placa-mãe",
    }


class PlacaMaeDelete(DeleteView):
    model = PlacaMae
    template_name = "website/placamae/confirm_delete.html"
    success_url = reverse_lazy("placamae-list")


class PlacaMaeList(ListView):
    model = PlacaMae
    template_name = "website/placamae/list.html"
    context_object_name = "placas_mae"


class PlacaMaeDetail(DetailView):
    model = PlacaMae
    template_name = "website/placamae/detail.html"


class MemoriaRAMCreate(CreateView):
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


class MemoriaRAMUpdate(UpdateView):
    model = MemoriaRAM
    fields = MemoriaRAMCreate.fields
    template_name = "website/memoriam/form.html"
    success_url = reverse_lazy("memoriam-list")
    extra_context = {
        "titulo": "Editar Memória RAM",
        "botao": "Atualizar Memória RAM",
    }


class MemoriaRAMDelete(DeleteView):
    model = MemoriaRAM
    template_name = "website/memoriam/confirm_delete.html"
    success_url = reverse_lazy("memoriam-list")


class MemoriaRAMList(ListView):
    model = MemoriaRAM
    template_name = "website/memoriam/list.html"
    context_object_name = "memorias_ram"


class MemoriaRAMDetail(DetailView):
    model = MemoriaRAM
    template_name = "website/memoriam/detail.html"


class PlacaDeVideoCreate(CreateView):
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


class PlacaDeVideoUpdate(UpdateView):
    model = PlacaDeVideo
    fields = PlacaDeVideoCreate.fields
    template_name = "website/placavideo/form.html"
    success_url = reverse_lazy("placavideo-list")
    extra_context = {
        "titulo": "Editar Placa de Vídeo",
        "botao": "Atualizar Placa de Vídeo",
    }


class PlacaDeVideoDelete(DeleteView):
    model = PlacaDeVideo
    template_name = "website/placavideo/confirm_delete.html"
    success_url = reverse_lazy("placavideo-list")


class PlacaDeVideoList(ListView):
    model = PlacaDeVideo
    template_name = "website/placavideo/list.html"
    context_object_name = "placas_video"


class PlacaDeVideoDetail(DetailView):
    model = PlacaDeVideo
    template_name = "website/placavideo/detail.html"


class ArmazenamentoCreate(CreateView):
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


class ArmazenamentoUpdate(UpdateView):
    model = Armazenamento
    fields = ArmazenamentoCreate.fields
    template_name = "website/armazenamento/form.html"
    success_url = reverse_lazy("armazenamento-list")
    extra_context = {
        "titulo": "Editar Armazenamento",
        "botao": "Atualizar Armazenamento",
    }


class ArmazenamentoDelete(DeleteView):
    model = Armazenamento
    template_name = "website/armazenamento/confirm_delete.html"
    success_url = reverse_lazy("armazenamento-list")


class ArmazenamentoList(ListView):
    model = Armazenamento
    template_name = "website/armazenamento/list.html"
    context_object_name = "armazenamentos"


class ArmazenamentoDetail(DetailView):
    model = Armazenamento
    template_name = "website/armazenamento/detail.html"


class FonteCreate(CreateView):
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


class FonteUpdate(UpdateView):
    model = Fonte
    fields = FonteCreate.fields
    template_name = "website/fonte/form.html"
    success_url = reverse_lazy("fonte-list")
    extra_context = {
        "titulo": "Editar Fonte",
        "botao": "Atualizar Fonte",
    }


class FonteDelete(DeleteView):
    model = Fonte
    template_name = "website/fonte/confirm_delete.html"
    success_url = reverse_lazy("fonte-list")


class FonteList(ListView):
    model = Fonte
    template_name = "website/fonte/list.html"
    context_object_name = "fontes"


class FonteDetail(DetailView):
    model = Fonte
    template_name = "website/fonte/detail.html"
