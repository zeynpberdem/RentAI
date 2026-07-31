"""Service request uc noktalari — see PDF SRV-1/SRV-2.

DefaultRouter kullanmiyoruz: router'in bos ('') prefix ile urettigi detay
adresi ('<pk>', araya '/' KOYMADAN) bizim istedigimiz
'api/service-requests/<pk>' formatiyla eslesmiyor. Bunun yerine ViewSet'in
action metodlarini elle path()'lere baglıyoruz.
"""

from django.urls import path

from .views import ServiceRequestViewSet

service_request_list = ServiceRequestViewSet.as_view({'get': 'list', 'post': 'create'})
service_request_detail = ServiceRequestViewSet.as_view({'put': 'update', 'patch': 'partial_update'})

urlpatterns = [
    path('', service_request_list, name='service-request-list-create'),
    path('/<uuid:pk>', service_request_detail, name='service-request-update'),
]
