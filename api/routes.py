from django.urls import path

from .benchmark_views import benchmark_dados, benchmark_grafico, benchmark_relatorio
from .views import clientes

urlpatterns = [
    path("clientes/", clientes, name="clientes"),
    path("clientes/<str:id_cliente>/", clientes, name="cliente"),
    path("benchmark/", benchmark_dados, name="benchmark"),
    path("benchmark/relatorio/", benchmark_relatorio, name="benchmark-relatorio"),
    path("benchmark/grafico/<str:nome>/", benchmark_grafico, name="benchmark-grafico"),
]