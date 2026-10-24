from .registry import MODULOS, permiso
from accounts.roles import ADMINISTRATIVO, OPERATIVO


def menu(request):
    subtitulo = "Gestión municipal"
    if request.user.is_authenticated:
        roles = set(request.user.groups.values_list("name", flat=True))
        if request.user.is_superuser or ADMINISTRATIVO in roles:
            subtitulo = "Control administrativo"
        elif OPERATIVO in roles:
            subtitulo = "Control operativo"
    return {
        "subtitulo_control": subtitulo,
        "menu_modulos": [
            {"slug": slug, "titulo": titulo}
            for slug, (modelo, titulo) in MODULOS.items()
            if request.user.has_perm(permiso(modelo, "view"))
        ]
    }
