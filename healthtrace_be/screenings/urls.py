from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RoleConfigViewSet, 
    ScreeningStationViewSet, 
    PatientWorkflowViewSet, 
    StationEntryViewSet
)

router = DefaultRouter()
router.register(r'roles', RoleConfigViewSet, basename='roleconfig')
router.register(r'stations', ScreeningStationViewSet, basename='station')
router.register(r'patients', PatientWorkflowViewSet, basename='patient')
router.register(r'entries', StationEntryViewSet, basename='entry')

# Backward-compatible aliases for legacy /api/screenings/ endpoints
screenings_router = DefaultRouter()
screenings_router.register(r'', PatientWorkflowViewSet, basename='screening')

urlpatterns = [
    path('', include(router.urls)),
    path('screenings/', include(screenings_router.urls)),
]
