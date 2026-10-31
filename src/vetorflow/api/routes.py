from django.urls import path
from .views import clientes

urlpatterns = [
    path("clientes/", clientes, name="clientes"),
    path("clientes/<str:id_cliente>/", clientes, name="cliente"),
]