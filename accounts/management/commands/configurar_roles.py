from django.core.management.base import BaseCommand
from accounts.roles import configurar_roles


class Command(BaseCommand):
    help = "Configura los dos roles y migra las membresías anteriores sin cambiar claves."

    def handle(self, *args, **options):
        configurar_roles()
        self.stdout.write(self.style.SUCCESS("Roles configurados."))
