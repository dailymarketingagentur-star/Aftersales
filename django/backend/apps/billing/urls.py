from django.urls import path

from . import views

app_name = "billing"

urlpatterns = [
    path("checkout/", views.CheckoutView.as_view(), name="checkout"),
    path("portal/", views.PortalView.as_view(), name="portal"),
    path("status/", views.SubscriptionStatusView.as_view(), name="status"),
]
