from django.contrib.auth.models import Group, Permission
from django.db import transaction

ADMINISTRATIVO = "ADMINISTRATIVO"
OPERATIVO = "OPERATIVO"
ROLES = (ADMINISTRATIVO, OPERATIVO)


@transaction.atomic
def configurar_roles():
    grupos = {
        nombre: Group.objects.get_or_create(name=nombre)[0] for nombre in ROLES
    }
    permisos = Permission.objects.filter(
        content_type__app_label__in=["core", "operacion", "personal", "auth"]
    )
    grupos[ADMINISTRATIVO].permissions.set(
        permisos.exclude(codename__startswith="delete_")
        | permisos.filter(
            content_type__app_label="auth", codename="delete_user"
        )
    )
    lectura = permisos.filter(
        content_type__app_label__in=["operacion", "personal"],
        codename__startswith="view_",
    )
    acciones = permisos.filter(
        content_type__app_label="operacion",
        codename__in=["finalizar_recorrido", "descargar_reportes"],
    )
    grupos[OPERATIVO].permissions.set(lectura | acciones)
    # Conserva las cuentas y sus claves al sustituir los grupos anteriores.
    for anterior, nuevo in {
        "ADMINISTRADOR": ADMINISTRATIVO,
        "SUPERVISOR": OPERATIVO,
        "OPERADOR DE ESTACIÓN": OPERATIVO,
    }.items():
        grupo = Group.objects.filter(name=anterior).first()
        if grupo:
            grupos[nuevo].user_set.add(*grupo.user_set.all())
            grupo.delete()
    grupos[OPERATIVO].user_set.remove(*grupos[ADMINISTRATIVO].user_set.all())
