from django.urls import path

from apps.clients.views import (
    CashflowPrognoseView,
    ChurnAssessmentListView,
    ClientDetailView,
    ClientEmailAddressDetailView,
    ClientEmailAddressListCreateView,
    ClientKeyFactDetailView,
    ClientKeyFactListCreateView,
    ClientListCreateView,
    ClientPhoneNumberDetailView,
    ClientPhoneNumberListCreateView,
    HealthAssessmentListView,
    ServiceDetailView,
    ServiceListCreateView,
    SubmitChurnCheckView,
    SubmitHealthCheckView,
)
from apps.integrations.views import ClientIntegrationDataListView, CreateJiraIssueView, CreateJiraProjectView, SyncConfluencePageView
from apps.tasks.views import (
    ClientActivityListCreateView,
    ClientRemoveListView,
    SubtaskToggleView,
    TaskCompleteView,
    TaskDetailView,
    TaskEmailPreviewView,
    TaskExecuteJiraView,
    TaskExecuteWebhookView,
    TaskGenerateView,
    TaskListCreateView,
    TaskSendEmailView,
    TaskSkipView,
    TaskStartSequenceView,
)

app_name = "clients"

urlpatterns = [
    path("", ClientListCreateView.as_view(), name="client-list-create"),
    path("cashflow-prognose/", CashflowPrognoseView.as_view(), name="cashflow-prognose"),
    path("<slug:slug>/", ClientDetailView.as_view(), name="client-detail"),
    path("<slug:slug>/services/", ServiceListCreateView.as_view(), name="service-list-create"),
    path("<slug:slug>/services/<uuid:pk>/", ServiceDetailView.as_view(), name="service-detail"),
    # Key Facts
    path("<slug:slug>/key-facts/", ClientKeyFactListCreateView.as_view(), name="key-fact-list-create"),
    path("<slug:slug>/key-facts/<uuid:pk>/", ClientKeyFactDetailView.as_view(), name="key-fact-detail"),
    # Phone Numbers
    path("<slug:slug>/phone-numbers/", ClientPhoneNumberListCreateView.as_view(), name="phone-number-list-create"),
    path("<slug:slug>/phone-numbers/<uuid:pk>/", ClientPhoneNumberDetailView.as_view(), name="phone-number-detail"),
    # Email Addresses
    path("<slug:slug>/email-addresses/", ClientEmailAddressListCreateView.as_view(), name="email-address-list-create"),
    path("<slug:slug>/email-addresses/<uuid:pk>/", ClientEmailAddressDetailView.as_view(), name="email-address-detail"),
    # Tasks
    path("<slug:slug>/tasks/", TaskListCreateView.as_view(), name="task-list-create"),
    path("<slug:slug>/tasks/generate/", TaskGenerateView.as_view(), name="task-generate"),
    path("<slug:slug>/tasks/remove-list/", ClientRemoveListView.as_view(), name="task-remove-list"),
    path("<slug:slug>/tasks/<uuid:pk>/", TaskDetailView.as_view(), name="task-detail"),
    path("<slug:slug>/tasks/<uuid:pk>/complete/", TaskCompleteView.as_view(), name="task-complete"),
    path("<slug:slug>/tasks/<uuid:pk>/skip/", TaskSkipView.as_view(), name="task-skip"),
    path("<slug:slug>/tasks/<uuid:pk>/email-preview/", TaskEmailPreviewView.as_view(), name="task-email-preview"),
    path("<slug:slug>/tasks/<uuid:pk>/send-email/", TaskSendEmailView.as_view(), name="task-send-email"),
    path("<slug:slug>/tasks/<uuid:pk>/start-sequence/", TaskStartSequenceView.as_view(), name="task-start-sequence"),
    path("<slug:slug>/tasks/<uuid:pk>/execute-jira/", TaskExecuteJiraView.as_view(), name="task-execute-jira"),
    path("<slug:slug>/tasks/<uuid:pk>/execute-webhook/", TaskExecuteWebhookView.as_view(), name="task-execute-webhook"),
    path("<slug:slug>/tasks/<uuid:pk>/subtasks/<uuid:subtask_pk>/", SubtaskToggleView.as_view(), name="subtask-toggle"),
    # Integration Data
    path("<slug:slug>/integrations/", ClientIntegrationDataListView.as_view(), name="client-integration-data"),
    path("<slug:slug>/integrations/jira/create-project/", CreateJiraProjectView.as_view(), name="client-jira-create-project"),
    path("<slug:slug>/integrations/jira/create-issue/", CreateJiraIssueView.as_view(), name="client-jira-create-issue"),
    path("<slug:slug>/integrations/confluence/sync/", SyncConfluencePageView.as_view(), name="client-confluence-sync"),
    # Health & Churn Assessments
    path("<slug:slug>/tasks/<uuid:pk>/submit-health-check/", SubmitHealthCheckView.as_view(), name="submit-health-check"),
    path("<slug:slug>/tasks/<uuid:pk>/submit-churn-check/", SubmitChurnCheckView.as_view(), name="submit-churn-check"),
    path("<slug:slug>/health-assessments/", HealthAssessmentListView.as_view(), name="health-assessment-list"),
    path("<slug:slug>/churn-assessments/", ChurnAssessmentListView.as_view(), name="churn-assessment-list"),
    # Activities / Timeline
    path("<slug:slug>/activities/", ClientActivityListCreateView.as_view(), name="activity-list-create"),
]
