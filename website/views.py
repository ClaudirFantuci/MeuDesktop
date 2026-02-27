from django.shortcuts import render
from django.views.generic import TemplateView


class IndexView(TemplateView):
    template_name = "website/model.html"

class ContatoView(TemplateView):
    template_name = "website/contato.html"

