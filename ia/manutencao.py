"""Endpoint interno para tarefas agendadas do app ia."""

import hmac

from django.conf import settings
from django.core.management import call_command
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def manutencao(request: HttpRequest) -> JsonResponse:
    """Executa a limpeza de auditoria quando o segredo interno confere."""
    if request.method != "POST":
        return JsonResponse({"erro": "Método não permitido."}, status=405)

    recebido = request.headers.get("X-Tarefas-Segredo", "")
    esperado = getattr(settings, "TAREFAS_SEGREDO", "")
    if not esperado or not hmac.compare_digest(recebido, esperado):
        return JsonResponse({"erro": "Não autorizado."}, status=403)

    call_command("ia_limpar")
    return JsonResponse({"status": "ok"})
