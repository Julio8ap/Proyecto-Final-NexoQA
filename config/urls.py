from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import path
from core import views
from reportes.views import reportes
from operacion.views import finalizar, atender
from accounts.views import eliminar_usuario

urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "login/",
        auth_views.LoginView.as_view(template_name="registration/login.html"),
        name="login",
    ),
    path("logout/", auth_views.LogoutView.as_view(), name="logout"),
    path(
        "cuenta/clave/",
        auth_views.PasswordChangeView.as_view(
            template_name="registration/password_change.html", success_url="/"
        ),
        name="password_change",
    ),
    path("", views.dashboard, name="dashboard"),
    path("reportes/", reportes, name="reportes"),
    path("alertas/<int:pk>/atender/", atender, name="atender_alerta"),
    path(
        "usuarios/<int:pk>/eliminar/",
        eliminar_usuario,
        name="eliminar_usuario",
    ),
    path(
        "recorridos/<int:pk>/finalizar/", finalizar, name="finalizar_recorrido"
    ),
    path("gestion/<slug:modulo>/", views.listado, name="listado"),
    path("gestion/<slug:modulo>/nuevo/", views.editar, name="crear"),
    path("gestion/<slug:modulo>/<int:pk>/", views.detalle, name="detalle"),
    path(
        "gestion/<slug:modulo>/<int:pk>/editar/", views.editar, name="editar"
    ),
]
