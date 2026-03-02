from django.urls import path

from . import views

app_name = "members"

urlpatterns = [
    path("", views.MemberListView.as_view(), name="member-list"),
    path("invite/", views.InviteMemberView.as_view(), name="member-invite"),
    path("<uuid:pk>/", views.MemberDetailView.as_view(), name="member-detail"),
]
