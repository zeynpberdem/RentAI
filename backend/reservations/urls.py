"""Reservation uc noktalari — see PDF RES-1/2/3.

DefaultRouter kullanmiyoruz: router'in bos ('') prefix ile urettigi detay
adresi ('<pk>/cancel', araya '/' KOYMADAN) bizim istedigimiz
'api/reservations/<pk>/cancel' formatiyla eslesmiyor. Bunun yerine
ViewSet'in action metodlarini elle path()'lere baglıyoruz — URL formati
tam kontrolümüzde kalıyor, ViewSet + @action yapısından vazgeçmeden.
"""

from django.urls import path

from .views import ReservationViewSet

reservation_list = ReservationViewSet.as_view({'get': 'list', 'post': 'create'})
reservation_cancel = ReservationViewSet.as_view({'post': 'cancel'})
reservation_extend = ReservationViewSet.as_view({'post': 'extend'})


urlpatterns = [
    path('', reservation_list, name='reservation-list-create'),
    path('/<uuid:pk>/cancel', reservation_cancel, name='reservation-cancel'),
    path('/<uuid:pk>/extend', reservation_extend, name='reservation-extend'),
]
