from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ScreeningViewSet, DoctorViewSet

router = DefaultRouter()
router.register(r'screenings', ScreeningViewSet)
router.register(r'doctors', DoctorViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
