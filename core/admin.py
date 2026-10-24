from django.contrib import admin
from .models import Auditoria


class ConsultaAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


admin.site.register(Auditoria, ConsultaAdmin)
admin.site.site_header = "Transmetro · Administración de consulta"
