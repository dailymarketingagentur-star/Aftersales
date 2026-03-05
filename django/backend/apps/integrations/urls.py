from django.urls import path

from apps.integrations import views

app_name = "integrations"

urlpatterns = [
    # Config Copy
    path("copy-config/sources/", views.CopyConfigSourcesView.as_view(), name="copy-config-sources"),
    path("copy-config/", views.CopyConfigView.as_view(), name="copy-config"),
    # Connection (Owner only)
    path("connection/", views.JiraConnectionView.as_view(), name="connection"),
    path("connection/test/", views.JiraConnectionTestView.as_view(), name="connection-test"),
    # Templates
    path("templates/", views.ActionTemplateListCreateView.as_view(), name="template-list"),
    path("templates/<uuid:pk>/", views.ActionTemplateDetailView.as_view(), name="template-detail"),
    # Sequences
    path("sequences/", views.ActionSequenceListCreateView.as_view(), name="sequence-list"),
    path("sequences/<uuid:pk>/", views.ActionSequenceDetailView.as_view(), name="sequence-detail"),
    path("sequences/<uuid:sequence_pk>/steps/", views.SequenceStepListCreateView.as_view(), name="step-list"),
    path("sequences/<uuid:sequence_pk>/steps/<uuid:pk>/", views.SequenceStepDetailView.as_view(), name="step-detail"),
    # Execution
    path("execute/", views.ExecuteActionView.as_view(), name="execute-action"),
    path("execute/sequence/", views.ExecuteSequenceView.as_view(), name="execute-sequence"),
    path("executions/", views.ExecutionListView.as_view(), name="execution-list"),
    path("executions/<uuid:pk>/", views.ExecutionDetailView.as_view(), name="execution-detail"),
    path("executions/<uuid:pk>/cancel/", views.ExecutionCancelView.as_view(), name="execution-cancel"),
    # Jira Proxy
    path("jira/projects/", views.JiraProjectsView.as_view(), name="jira-projects"),
    path("jira/issue-types/<str:project_key>/", views.JiraIssueTypesView.as_view(), name="jira-issue-types"),
    path("jira/fields/", views.JiraFieldsView.as_view(), name="jira-fields"),
    # Confluence Proxy
    path("confluence/spaces/", views.ConfluenceSpacesView.as_view(), name="confluence-spaces"),
    path("confluence/spaces/<str:space_key>/pages/", views.ConfluencePagesView.as_view(), name="confluence-pages"),
    # Integration Types (Registry-based)
    path("types/", views.IntegrationTypeListView.as_view(), name="integration-types"),
    path("toggle/", views.IntegrationToggleView.as_view(), name="integration-toggle"),
    # Twilio
    path("twilio/connection/", views.TwilioConnectionView.as_view(), name="twilio-connection"),
    path("twilio/connection/test/", views.TwilioConnectionTestView.as_view(), name="twilio-connection-test"),
    path("twilio/token/", views.TwilioAccessTokenView.as_view(), name="twilio-token"),
    path("twilio/twiml/voice/", views.TwiMLVoiceView.as_view(), name="twilio-twiml-voice"),
    # WhatsApp
    path("whatsapp/connection/", views.WhatsAppConnectionView.as_view(), name="whatsapp-connection"),
    path("whatsapp/connection/test/", views.WhatsAppConnectionTestView.as_view(), name="whatsapp-connection-test"),
    path("whatsapp/send/", views.WhatsAppSendMessageView.as_view(), name="whatsapp-send"),
]
