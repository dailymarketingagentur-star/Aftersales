from django.urls import path

from . import views

app_name = "tenants"

urlpatterns = [
    path("", views.TenantListCreateView.as_view(), name="tenant-list-create"),
    path("<uuid:pk>/", views.TenantDetailView.as_view(), name="tenant-detail"),
]
