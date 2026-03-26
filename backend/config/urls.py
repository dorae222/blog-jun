from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from blog.sitemaps import sitemap_xml, robots_txt

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('blog.urls')),
    path('api/auth/', include('accounts.urls')),
    path('api/operations/', include('operations.urls')),
    path('sitemap.xml', sitemap_xml),
    path('robots.txt', robots_txt),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
