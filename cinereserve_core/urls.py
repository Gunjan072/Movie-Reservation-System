from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from movies.views import home_view

admin.site.site_header = "CineReserve Administration"
admin.site.site_title = "CineReserve Admin"
admin.site.index_title = "Cinema operations & catalogue"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', home_view, name='home'),
    path('accounts/', include('accounts.urls')),
    path('movies/', include('movies.urls')),
    path('cinemas/', include('cinemas.urls')),
    path('shows/', include('shows.urls')),
    path('bookings/', include('bookings.urls')),
    path('reviews/', include('reviews.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('recommendations/', include('recommendations.urls')),
    path('chatbot/', include('chatbot.urls')),
    path('api/', include('api.urls')),
]

handler403 = 'cinereserve_core.error_views.permission_denied'
handler404 = 'cinereserve_core.error_views.page_not_found'
handler500 = 'cinereserve_core.error_views.server_error'

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
