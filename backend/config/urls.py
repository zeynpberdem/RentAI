"""URL configuration for the RentAI project."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path('admin/', admin.site.urls),

    # Her app'in kendi uc noktalari kendi urls.py'sinde tanimli — "reservations
    # ile ilgili bir API mi ariyorum" dersen direkt reservations/urls.py'ye
    # bakman yetiyor, tum route'lari burada aramana gerek kalmiyor.
    path('api/auth/', include('users.urls')),
    path('api/', include('vehicles.urls')),
    path('api/reservations', include('reservations.urls')),
    path('api/reservations2/',include('reservations2.urls')),
    path('api/handovers', include('handovers.urls')),
    path('api/service-requests', include('service_requests.urls')),

    # --- API docs (drf-spectacular) — endpoint'leri tarayıcıdan görüp
    # deneyebilmek için; Postman'e gerek kalmadan register/login test edilebilir.
    path('api/schema', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]

# TR: Yüklenen araç görsellerini yerel geliştirmede tarayıcıdan görebilmek
# için — bu, sadece DEBUG=True iken devreye girer; gerçek (prod) ortamda
# medya dosyaları normalde ayrı bir sunucu/servis (nginx, S3 vb.) tarafından
# sunulur, Django'nun kendisi değil.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
