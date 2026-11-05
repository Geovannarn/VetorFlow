
from django.contrib import admin
from django.urls import include, path
from django.shortcuts import render


def inicio(request):
    return render(request, 'index.html')


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.routes')),
    path('', inicio, name='inicio'),
]
