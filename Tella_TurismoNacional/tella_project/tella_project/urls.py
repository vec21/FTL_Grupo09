from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.contrib.staticfiles.urls import staticfiles_urlpatterns  # added
from django.contrib.staticfiles.storage import staticfiles_storage  # added
from django.views.generic.base import RedirectView  # added

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls', namespace='core')),
    # Favicons buscados na raiz
    path('favicon.ico', RedirectView.as_view(url=staticfiles_storage.url('favicons/favicon.ico'), permanent=False)),
    path('apple-touch-icon.png', RedirectView.as_view(url=staticfiles_storage.url('favicons/apple-touch-icon.png'), permanent=False)),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # Servir estáticos via finders (inclui STATICFILES_DIRS); evita uso direto de STATIC_ROOT vazio
    urlpatterns += staticfiles_urlpatterns()
