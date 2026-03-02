from django.urls import path

from apps.nps.views import (
    ClientNPSView,
    NPSCampaignDetailView,
    NPSCampaignListCreateView,
    NPSDashboardView,
    NPSResponseDetailView,
    NPSResponseListView,
    NPSSurveyListView,
    NPSTrendView,
    PublicSurveyRespondView,
    PublicSurveyView,
    SendSurveyView,
    TestimonialDetailView,
    TestimonialListCreateView,
)

app_name = "nps"

urlpatterns = [
    # Public (no auth, no X-Tenant-ID)
    path("public/<uuid:token>/", PublicSurveyView.as_view(), name="public-survey"),
    path("public/<uuid:token>/respond/", PublicSurveyRespondView.as_view(), name="public-survey-respond"),
    # Dashboard
    path("dashboard/", NPSDashboardView.as_view(), name="dashboard"),
    path("dashboard/trend/", NPSTrendView.as_view(), name="dashboard-trend"),
    # Campaigns
    path("campaigns/", NPSCampaignListCreateView.as_view(), name="campaign-list-create"),
    path("campaigns/<uuid:pk>/", NPSCampaignDetailView.as_view(), name="campaign-detail"),
    # Surveys
    path("surveys/", NPSSurveyListView.as_view(), name="survey-list"),
    path("surveys/send/", SendSurveyView.as_view(), name="survey-send"),
    # Responses
    path("responses/", NPSResponseListView.as_view(), name="response-list"),
    path("responses/<uuid:pk>/", NPSResponseDetailView.as_view(), name="response-detail"),
    # Testimonials
    path("testimonials/", TestimonialListCreateView.as_view(), name="testimonial-list-create"),
    path("testimonials/<uuid:pk>/", TestimonialDetailView.as_view(), name="testimonial-detail"),
    # Per-client
    path("clients/<slug:slug>/", ClientNPSView.as_view(), name="client-nps"),
]
