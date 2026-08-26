from django import template

register = template.Library()


@register.filter(name="pertence")
def pertence_ao(usuario, nome_do_grupo):
    """Retorna True se o usuário autenticado pertencer ao grupo informado."""
    if not getattr(usuario, "is_authenticated", False):
        return False
    if usuario.is_superuser:
        return True
    return usuario.groups.filter(name=nome_do_grupo).exists()
