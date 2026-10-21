from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import Reservation2ViewSet

# DRF Router oluşturuyoruz
router = DefaultRouter()#api uc noktalarını olusturmak icin 
# 'reservations2' adıyla viewset'i router'a yüklüyoruz
router.register(r'reservations2', Reservation2ViewSet, basename='reservation2')
#otomatik bir url olusturuyoryz burda
urlpatterns = [
    path('', include(router.urls)),
]