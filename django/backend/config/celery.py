import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.local")

app = Celery("aftersales")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Periodic tasks
app.conf.beat_schedule = {
    "jira-connection-daily-health-check": {
        "task": "apps.integrations.tasks.check_all_jira_connections",
        "schedule": crontab(hour=7, minute=0),  # Täglich um 07:00 Uhr
    },
    "process-recurring-task-schedules": {
        "task": "apps.tasks.tasks.process_recurring_schedules",
        "schedule": crontab(hour=8, minute=0),  # Täglich um 08:00 Uhr
    },
    "process-nps-campaigns": {
        "task": "apps.nps.tasks.process_nps_campaigns",
        "schedule": crontab(hour=8, minute=0),  # Täglich um 08:00 Uhr
    },
    "process-auto-trigger-tasks": {
        "task": "apps.tasks.tasks.process_auto_trigger_tasks",
        "schedule": crontab(minute="*/15"),  # Alle 15 Minuten
    },
}
