from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    # Envolvemos todo bajo el prefijo 'api/' para que Nginx conecte a la primera
    path('api/', include([
        # Panel de administración
        path('admin/', admin.site.urls),
        
        # Rutas de la documentación (Swagger) integradas en el prefijo
        path('schema/', SpectacularAPIView.as_view(), name='schema'),
        path('', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
        
        # El conector original de tus compañeros (¡así no rompemos nada!)
        path('', include('api.urls')),
    ])),
]
