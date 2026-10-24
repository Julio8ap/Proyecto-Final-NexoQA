from .registry import MODULOS, permiso


def menu(request):
    return {
        "menu_modulos": [
            {"slug": slug, "titulo": titulo}
            for slug, (modelo, titulo) in MODULOS.items()
            if request.user.has_perm(permiso(modelo, "view"))
        ]
    }
