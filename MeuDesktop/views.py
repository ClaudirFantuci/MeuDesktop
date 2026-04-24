from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import TemplateView, CreateView, UpdateView, DeleteView
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView

from .models import Fabricante


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

