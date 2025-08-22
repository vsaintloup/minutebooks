from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from documents.views import DocumentViewSet
from tickets.views import TicketViewSet

# DRF Router
router = DefaultRouter()
router.register(r"documents", DocumentViewSet, basename="document")
router.register(r"tickets", TicketViewSet, basename="ticket")

urlpatterns = [
    path("accounts/", include("allauth.urls")),
    path("api/", include(router.urls)),
    path("api-auth/", include("rest_framework.urls")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += i18n_patterns(
    path("admin/", admin.site.urls),
    path("", include("corps.urls")),
)
