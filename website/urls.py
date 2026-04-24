from django.urls import path
from .views import (
    IndexView,
    ContatoView,
    FabricanteCreate,
    FabricanteUpdate,
    FabricanteDelete,
    FabricanteList,
    FabricanteDetail,
)
urlpatterns = [
    path("", IndexView.as_view(), name="index"),
    path("contato/", ContatoView.as_view(), name="contato"),

    path("cadastrar/fabricante/", FabricanteCreate.as_view(), name="fabricante-create"),
    path("atualizar/fabricante/<int:pk>/", FabricanteUpdate.as_view(), name="fabricante-update"),
    path("excluir/fabricante/<int:pk>/", FabricanteDelete.as_view(), name="fabricante-delete"),
    path("listar/fabricante/", FabricanteList.as_view(), name="fabricante-list"),
    path("detalhar/fabricante/<int:pk>/", FabricanteDetail.as_view(), name="fabricante-detail"),
]
