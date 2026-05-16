from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    # El panel de administración vuelve a la raíz para responder en /admin/
    path('admin/', admin.site.urls),
    
    # Envolvemos la documentación y el conector de tus compañeros bajo /api/
    path('api/', include([
        # Rutas de la documentación (Swagger)
        path('schema/', SpectacularAPIView.as_view(), name='schema'),
        path('', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
        
        # El conector de tus compañeros
        path('', include('api.urls')),
    ])),
]
