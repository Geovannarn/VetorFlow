from django.contrib import admin
from django.urls import include, path
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.routes')),
    path('', lambda request: redirect('/api/')),
]