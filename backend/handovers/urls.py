"""Handover uc noktalari — see PDF HND-1/HND-2.

config/urls.py'de 'api/handovers' prefix'iyle include ediliyor; router'in
prefix'i de '' (bos) — boylece adres tam olarak 'api/handovers' cikiyor.
"""

from rest_framework.routers import DefaultRouter

from .views import HandoverViewSet

router = DefaultRouter(trailing_slash=False)
router.register('', HandoverViewSet, basename='handover')

urlpatterns = router.urls
