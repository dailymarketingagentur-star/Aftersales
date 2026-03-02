from django.urls import path

from apps.clients.views import ServiceTypeDetailView, ServiceTypeListCreateView

app_name = "service-types"

urlpatterns = [
    path("", ServiceTypeListCreateView.as_view(), name="service-type-list-create"),
    path("<uuid:pk>/", ServiceTypeDetailView.as_view(), name="service-type-detail"),
]
