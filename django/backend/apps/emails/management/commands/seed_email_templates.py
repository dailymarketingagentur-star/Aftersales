import structlog
from django.core.management.base import BaseCommand

logger = structlog.get_logger()

# fmt: off
TEMPLATES = [
    # =====================================================================
    # BESTEHENDE TEMPLATES (10)
    # =====================================================================
    {
        "slug": "willkommens-email",
        "name": "Willkommens-Email (Tag 0)",
        "subject": "Willkommen bei {{TENANT_NAME}}, {{FIRST_NAME}}!",
        "body_html": (
            '<h1 style="color: #333;">Willkommen an Bord, {{FIRST_NAME}}!</h1>'
            "<p>Wir freuen uns sehr, Sie als neuen Kunden bei <strong>{{TENANT_NAME}}</strong> "
            "begruessen zu duerfen.</p>"
            "<p>In den naechsten Tagen erhalten Sie von uns:"
            "<ul>"
            "<li>Eine Vorstellung Ihres persoenlichen Ansprechpartners</li>"
            "<li>Ihre individuelle Onboarding-Checkliste</li>"
            "<li>Zugang zu allen relevanten Ressourcen</li>"
            "</ul></p>"
            "<p>Bei Fragen stehen wir Ihnen jederzeit zur Verfuegung.</p>"
            "<p>Herzliche Gruesse,<br>Ihr {{TENANT_NAME}} Team</p>"
        ),
        "variables": ["FIRST_NAME", "TENANT_NAME"],
    },
    {
        "slug": "team-vorstellung",
        "name": "Team-Vorstellung (Tag 1-2)",
        "subject": "Ihr persoenlicher Ansprechpartner bei {{TENANT_NAME}}",
        "body_html": (
            '<h1 style="color: #333;">Lernen Sie Ihr Team kennen</h1>'
            "<p>Hallo {{FIRST_NAME}},</p>"
            "<p>mein Name ist <strong>{{CONTACT_NAME}}</strong> und ich bin Ihr "
            "persoenlicher Ansprechpartner bei {{TENANT_NAME}}.</p>"
            "<p>Sie erreichen mich unter:"
            "<ul>"
            "<li>Email: {{CONTACT_EMAIL}}</li>"
            "<li>Telefon: {{CONTACT_PHONE}}</li>"
            "</ul></p>"
            "<p>Ich freue mich auf die Zusammenarbeit!</p>"
            "<p>Beste Gruesse,<br>{{CONTACT_NAME}}</p>"
        ),
        "variables": ["FIRST_NAME", "TENANT_NAME", "CONTACT_NAME", "CONTACT_EMAIL", "CONTACT_PHONE"],
    },
    {
        "slug": "onboarding-checklist",
        "name": "Onboarding Checklist (Tag 3-5)",
        "subject": "Ihre Onboarding-Checkliste — {{TENANT_NAME}}",
        "body_html": (
            '<h1 style="color: #333;">Ihre naechsten Schritte</h1>'
            "<p>Hallo {{FIRST_NAME}},</p>"
            "<p>damit Sie optimal starten koennen, haben wir Ihnen eine persoenliche "
            "Checkliste zusammengestellt:</p>"
            "<ol>"
            "<li>Zugangsdaten pruefen und einloggen</li>"
            "<li>Profil vervollstaendigen</li>"
            "<li>Erste Einstellungen vornehmen</li>"
            "<li>Kick-off Termin bestätigen</li>"
            "</ol>"
            '<p><a href="{{CHECKLIST_URL}}" style="display: inline-block; padding: 12px 24px; '
            "background-color: #000; color: #fff; text-decoration: none; "
            'border-radius: 6px;">Zur Checkliste</a></p>'
            "<p>Beste Gruesse,<br>Ihr {{TENANT_NAME}} Team</p>"
        ),
        "variables": ["FIRST_NAME", "TENANT_NAME", "CHECKLIST_URL"],
    },
    {
        "slug": "erste-ergebnisse",
        "name": "Erste Ergebnisse (Trigger-basiert)",
        "subject": "Ihre ersten Ergebnisse sind da — {{TENANT_NAME}}",
        "body_html": (
            '<h1 style="color: #333;">Ihre ersten Ergebnisse</h1>'
            "<p>Hallo {{FIRST_NAME}},</p>"
            "<p>wir haben grossartige Neuigkeiten: Ihre ersten Ergebnisse liegen vor!</p>"
            "<p><strong>Zusammenfassung:</strong></p>"
            "<p>{{RESULTS_SUMMARY}}</p>"
            '<p><a href="{{RESULTS_URL}}" style="display: inline-block; padding: 12px 24px; '
            "background-color: #000; color: #fff; text-decoration: none; "
            'border-radius: 6px;">Ergebnisse ansehen</a></p>'
            "<p>Beste Gruesse,<br>Ihr {{TENANT_NAME}} Team</p>"
        ),
        "variables": ["FIRST_NAME", "TENANT_NAME", "RESULTS_SUMMARY", "RESULTS_URL"],
    },
    {
        "slug": "insights-feedback",
        "name": "Insights + Feedback (Tag 60)",
        "subject": "Ihre Insights nach 60 Tagen — {{TENANT_NAME}}",
        "body_html": (
            '<h1 style="color: #333;">60-Tage Insights</h1>'
            "<p>Hallo {{FIRST_NAME}},</p>"
            "<p>Sie sind jetzt seit 60 Tagen bei uns — Zeit fuer ein kurzes Update!</p>"
            "<p><strong>Ihre Highlights:</strong></p>"
            "<p>{{INSIGHTS_SUMMARY}}</p>"
            "<p>Wir wuerden uns sehr ueber Ihr Feedback freuen. Was laeuft gut? "
            "Was koennen wir verbessern?</p>"
            '<p><a href="{{FEEDBACK_URL}}" style="display: inline-block; padding: 12px 24px; '
            "background-color: #000; color: #fff; text-decoration: none; "
            'border-radius: 6px;">Feedback geben</a></p>'
            "<p>Beste Gruesse,<br>Ihr {{TENANT_NAME}} Team</p>"
        ),
        "variables": ["FIRST_NAME", "TENANT_NAME", "INSIGHTS_SUMMARY", "FEEDBACK_URL"],
    },
    {
        "slug": "nps-review",
        "name": "NPS-Survey + Review (Tag 90)",
        "subject": "Wie zufrieden sind Sie? — {{TENANT_NAME}}",
        "body_html": (
            '<h1 style="color: #333;">Ihre Meinung zaehlt</h1>'
            "<p>Hallo {{FIRST_NAME}},</p>"
            "<p>Sie sind jetzt seit 90 Tagen bei {{TENANT_NAME}}. "
            "Wie wahrscheinlich ist es, dass Sie uns weiterempfehlen wuerden?</p>"
            '<table cellpadding="0" cellspacing="0" border="0" style="margin: 24px auto;">'
            "<tr>"
            '<td style="padding: 0 3px;"><a href="{{NPS_URL}}?score=1" style="display: inline-block; width: 40px; height: 40px; line-height: 40px; text-align: center; background-color: #dc2626; color: #fff; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 16px;">1</a></td>'
            '<td style="padding: 0 3px;"><a href="{{NPS_URL}}?score=2" style="display: inline-block; width: 40px; height: 40px; line-height: 40px; text-align: center; background-color: #e04832; color: #fff; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 16px;">2</a></td>'
            '<td style="padding: 0 3px;"><a href="{{NPS_URL}}?score=3" style="display: inline-block; width: 40px; height: 40px; line-height: 40px; text-align: center; background-color: #ea580c; color: #fff; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 16px;">3</a></td>'
            '<td style="padding: 0 3px;"><a href="{{NPS_URL}}?score=4" style="display: inline-block; width: 40px; height: 40px; line-height: 40px; text-align: center; background-color: #d97706; color: #fff; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 16px;">4</a></td>'
            '<td style="padding: 0 3px;"><a href="{{NPS_URL}}?score=5" style="display: inline-block; width: 40px; height: 40px; line-height: 40px; text-align: center; background-color: #eab308; color: #fff; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 16px;">5</a></td>'
            '<td style="padding: 0 3px;"><a href="{{NPS_URL}}?score=6" style="display: inline-block; width: 40px; height: 40px; line-height: 40px; text-align: center; background-color: #a3b820; color: #fff; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 16px;">6</a></td>'
            '<td style="padding: 0 3px;"><a href="{{NPS_URL}}?score=8" style="display: inline-block; width: 40px; height: 40px; line-height: 40px; text-align: center; background-color: #65a30d; color: #fff; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 16px;">8</a></td>'
            '<td style="padding: 0 3px;"><a href="{{NPS_URL}}?score=9" style="display: inline-block; width: 40px; height: 40px; line-height: 40px; text-align: center; background-color: #16a34a; color: #fff; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 16px;">9</a></td>'
            '<td style="padding: 0 3px;"><a href="{{NPS_URL}}?score=10" style="display: inline-block; width: 40px; height: 40px; line-height: 40px; text-align: center; background-color: #15803d; color: #fff; text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 16px;">10</a></td>'
            "</tr>"
            "<tr>"
            '<td colspan="3" style="text-align: left; font-size: 12px; color: #999; padding-top: 8px;">Unwahrscheinlich</td>'
            '<td colspan="3"></td>'
            '<td colspan="3" style="text-align: right; font-size: 12px; color: #999; padding-top: 8px;">Sehr wahrscheinlich</td>'
            "</tr>"
            "</table>"
            "<p>Ihr Feedback hilft uns, besser zu werden.</p>"
            "<p>Herzliche Gruesse,<br>Ihr {{TENANT_NAME}} Team</p>"
        ),
        "variables": ["FIRST_NAME", "TENANT_NAME", "NPS_URL"],
    },
    {
        "slug": "nps-followup-promoter",
        "name": "NPS Follow-up: Promoter (9-10)",
        "subject": "Danke fuer Ihre Empfehlung! — {{TENANT_NAME}}",
        "body_html": (
            '<h1 style="color: #333;">Vielen Dank!</h1>'
            "<p>Hallo {{FIRST_NAME}},</p>"
            "<p>Wir freuen uns riesig ueber Ihre positive Bewertung! "
            "Als Dankeschoen moechten wir Sie bitten:</p>"
            "<ul>"
            "<li>Teilen Sie Ihre Erfahrung als Google-Bewertung</li>"
            "<li>Empfehlen Sie uns in Ihrem Netzwerk weiter</li>"
            "</ul>"
            '<p><a href="{{REVIEW_URL}}" style="display: inline-block; padding: 12px 24px; '
            "background-color: #000; color: #fff; text-decoration: none; "
            'border-radius: 6px;">Bewertung schreiben</a></p>'
            "<p>Herzliche Gruesse,<br>Ihr {{TENANT_NAME}} Team</p>"
        ),
        "variables": ["FIRST_NAME", "TENANT_NAME", "REVIEW_URL"],
    },
    {
        "slug": "nps-followup-passive",
        "name": "NPS Follow-up: Passiv (7-8)",
        "subject": "Wie koennen wir besser werden? — {{TENANT_NAME}}",
        "body_html": (
            '<h1 style="color: #333;">Ihr Feedback ist uns wichtig</h1>'
            "<p>Hallo {{FIRST_NAME}},</p>"
            "<p>Danke fuer Ihre ehrliche Bewertung. Wir moechten verstehen, "
            "was wir verbessern koennen, damit Sie rundum zufrieden sind.</p>"
            '<p><a href="{{FEEDBACK_URL}}" style="display: inline-block; padding: 12px 24px; '
            "background-color: #000; color: #fff; text-decoration: none; "
            'border-radius: 6px;">Feedback geben</a></p>'
            "<p>Beste Gruesse,<br>Ihr {{TENANT_NAME}} Team</p>"
        ),
        "variables": ["FIRST_NAME", "TENANT_NAME", "FEEDBACK_URL"],
    },
    {
        "slug": "nps-followup-detractor",
        "name": "NPS Follow-up: Detractor (0-6)",
        "subject": "Wir moechten es besser machen — {{TENANT_NAME}}",
        "body_html": (
            '<h1 style="color: #333;">Es tut uns leid</h1>'
            "<p>Hallo {{FIRST_NAME}},</p>"
            "<p>Ihre Zufriedenheit ist unser oberstes Ziel, und wir bedauern, "
            "dass wir Ihre Erwartungen nicht erfuellt haben.</p>"
            "<p>{{CONTACT_NAME}} wird sich persoenlich bei Ihnen melden, "
            "um die Situation zu besprechen und eine Loesung zu finden.</p>"
            "<p>Alternativ koennen Sie uns direkt kontaktieren:</p>"
            "<ul>"
            "<li>Email: {{CONTACT_EMAIL}}</li>"
            "<li>Telefon: {{CONTACT_PHONE}}</li>"
            "</ul>"
            "<p>Beste Gruesse,<br>Ihr {{TENANT_NAME}} Team</p>"
        ),
        "variables": ["FIRST_NAME", "TENANT_NAME", "CONTACT_NAME", "CONTACT_EMAIL", "CONTACT_PHONE"],
    },
    {
        "slug": "team-invite",
        "name": "Team-Einladung",
        "subject": "Einladung zu {{TENANT_NAME}}",
        "body_html": (
            '<h1 style="color: #333;">Sie wurden eingeladen</h1>'
            "<p>Hallo,</p>"
            "<p><strong>{{INVITED_BY}}</strong> hat Sie eingeladen, der Organisation "
            "<strong>{{TENANT_NAME}}</strong> beizutreten.</p>"
            '<p><a href="{{INVITE_URL}}" style="display: inline-block; padding: 12px 24px; '
            "background-color: #000; color: #fff; text-decoration: none; "
            'border-radius: 6px;">Einladung annehmen</a></p>'
            '<p style="color: #666; font-size: 14px;">'
            "Falls Sie diese Einladung nicht erwartet haben, "
            "koennen Sie diese E-Mail ignorieren.</p>"
        ),
        "variables": ["INVITED_BY", "TENANT_NAME", "INVITE_URL"],
    },

    # =====================================================================
    # A. OPERATIV / ADMINISTRATIV (7)
    # =====================================================================
    {
        "slug": "rechnung-ankuendigung",
        "name": "Rechnungsankündigung",
        "subject": "Ihre Rechnung für {{MONTH}} — {{TENANT_NAME}}",
        "body_html": (
            '<h1 style="color: #333;">Ihre Rechnung kommt morgen</h1>'
            "<p>Hallo {{FIRST_NAME}},</p>"
            "<p>wir möchten Sie kurz informieren, dass Ihre Rechnung für "
            "<strong>{{MONTH}}</strong> morgen per E-Mail bei Ihnen eintrifft.</p>"
            "<p><strong>Betrag:</strong> {{AMOUNT}}<br>"
            "<strong>Leistungszeitraum:</strong> {{PERIOD}}</p>"
            "<p>Bei Fragen zur Rechnung stehen wir Ihnen gerne zur Verfügung.</p>"
            "<p>Beste Grüße,<br>Ihr {{TENANT_NAME}} Team</p>"
        ),
        "variables": ["FIRST_NAME", "TENANT_NAME", "MONTH", "AMOUNT", "PERIOD"],
    },
    {
        "slug": "briefkasten-hinweis",
        "name": "Briefkasten-Hinweis",
        "subject": "Post von {{TENANT_NAME}} ist unterwegs!",
        "body_html": (
            '<h1 style="color: #333;">Post ist unterwegs!</h1>'
            "<p>Hallo {{FIRST_NAME}},</p>"
            "<p>wir haben Ihnen etwas per Post geschickt — halten Sie in den "
            "nächsten Tagen Ausschau nach einem <strong>{{PACKAGE_TYPE}}</strong> "
            "von {{TENANT_NAME}}.</p>"
            "<p><strong>Sendungsnummer:</strong> {{TRACKING_NUMBER}}</p>"
            "<p>Wir freuen uns auf Ihr Feedback, sobald es angekommen ist!</p>"
            "<p>Beste Grüße,<br>Ihr {{TENANT_NAME}} Team</p>"
        ),
        "variables": ["FIRST_NAME", "TENANT_NAME", "PACKAGE_TYPE", "TRACKING_NUMBER"],
    },
    {
        "slug": "meeting-einladung",
        "name": "Meeting-Einladung",
        "subject": "Terminbestätigung: {{MEETING_TITLE}} — {{TENANT_NAME}}",
        "body_html": (
            '<h1 style="color: #333;">Ihr Termin steht fest</h1>'
            "<p>Hallo {{FIRST_NAME}},</p>"
            "<p>hiermit bestätigen wir Ihren Termin:</p>"
            "<p><strong>{{MEETING_TITLE}}</strong><br>"
            "Datum: {{MEETING_DATE}}<br>"
            "Uhrzeit: {{MEETING_TIME}}<br>"
            "Dauer: {{MEETING_DURATION}}</p>"
            "<p><strong>Agenda:</strong></p>"
            "<p>{{MEETING_AGENDA}}</p>"
            '<p><a href="{{MEETING_LINK}}" style="display: inline-block; padding: 12px 24px; '
            "background-color: #000; color: #fff; text-decoration: none; "
            'border-radius: 6px;">Zum Meeting</a></p>'
            "<p>Beste Grüße,<br>Ihr {{TENANT_NAME}} Team</p>"
        ),
        "variables": ["FIRST_NAME", "TENANT_NAME", "MEETING_TITLE", "MEETING_DATE", "MEETING_TIME", "MEETING_DURATION", "MEETING_AGENDA", "MEETING_LINK"],
    },
    {
        "slug": "meeting-erinnerung",
        "name": "Meeting-Erinnerung (24h)",
        "subject": "Erinnerung: {{MEETING_TITLE}} morgen — {{TENANT_NAME}}",
        "body_html": (
            '<h1 style="color: #333;">Erinnerung an Ihren Termin</h1>'
            "<p>Hallo {{FIRST_NAME}},</p>"
            "<p>nur eine kurze Erinnerung: Morgen findet Ihr Termin statt.</p>"
            "<p><strong>{{MEETING_TITLE}}</strong><br>"
            "Datum: {{MEETING_DATE}}<br>"
            "Uhrzeit: {{MEETING_TIME}}</p>"
            '<p><a href="{{MEETING_LINK}}" style="display: inline-block; padding: 12px 24px; '
            "background-color: #000; color: #fff; text-decoration: none; "
            'border-radius: 6px;">Zum Meeting</a></p>'
            "<p>Wir freuen uns auf das Gespräch!</p>"
            "<p>Beste Grüße,<br>Ihr {{TENANT_NAME}} Team</p>"
        ),
        "variables": ["FIRST_NAME", "TENANT_NAME", "MEETING_TITLE", "MEETING_DATE", "MEETING_TIME", "MEETING_LINK"],
    },
    {
        "slug": "zugangsdaten-bereitstellung",
        "name": "Zugänge eingerichtet",
        "subject": "Ihre Zugänge sind bereit — {{TENANT_NAME}}",
        "body_html": (
            '<h1 style="color: #333;">Ihre Zugänge stehen bereit</h1>'
            "<p>Hallo {{FIRST_NAME}},</p>"
            "<p>wir haben Ihre Zugänge eingerichtet. Sie können sich ab sofort "
            "in folgenden Tools anmelden:</p>"
            "<p>{{ACCESS_LIST}}</p>"
            '<p><a href="{{LOGIN_URL}}" style="display: inline-block; padding: 12px 24px; '
            "background-color: #000; color: #fff; text-decoration: none; "
            'border-radius: 6px;">Jetzt einloggen</a></p>'
            '<p style="color: #666; font-size: 14px;">'
            "Bitte ändern Sie Ihr Passwort beim ersten Login.</p>"
            "<p>Beste Grüße,<br>Ihr {{TENANT_NAME}} Team</p>"
        ),
        "variables": ["FIRST_NAME", "TENANT_NAME", "ACCESS_LIST", "LOGIN_URL"],
    },
    {
        "slug": "dokument-bereitstellung",
        "name": "Dokument bereitgestellt",
        "subject": "{{DOCUMENT_TITLE}} steht zum Download bereit — {{TENANT_NAME}}",
        "body_html": (
            '<h1 style="color: #333;">Ihr Dokument ist fertig</h1>'
            "<p>Hallo {{FIRST_NAME}},</p>"
            "<p>Ihr Dokument <strong>{{DOCUMENT_TITLE}}</strong> steht für Sie "
            "zum Download bereit.</p>"
            "<p>{{DOCUMENT_DESCRIPTION}}</p>"
            '<p><a href="{{DOCUMENT_URL}}" style="display: inline-block; padding: 12px 24px; '
            "background-color: #000; color: #fff; text-decoration: none; "
            'border-radius: 6px;">Dokument herunterladen</a></p>'
            "<p>Bei Fragen zum Inhalt melden Sie sich gerne.</p>"
            "<p>Beste Grüße,<br>Ihr {{TENANT_NAME}} Team</p>"
        ),
        "variables": ["FIRST_NAME", "TENANT_NAME", "DOCUMENT_TITLE", "DOCUMENT_DESCRIPTION", "DOCUMENT_URL"],
    },
    {
        "slug": "asset-erinnerung",
        "name": "Ausstehende Zulieferungen",
        "subject": "Erinnerung: Wir benötigen noch Zulieferungen — {{TENANT_NAME}}",
        "body_html": (
            '<h1 style="color: #333;">Ausstehende Zulieferungen</h1>'
            "<p>Hallo {{FIRST_NAME}},</p>"
            "<p>damit wir optimal für Sie arbeiten können, benötigen wir noch "
            "folgende Unterlagen bzw. Zugänge von Ihnen:</p>"
            "<p>{{ASSET_LIST}}</p>"
            "<p>Könnten Sie uns diese bis zum <strong>{{DEADLINE}}</strong> zukommen lassen? "
            "So stellen wir sicher, dass Ihr Projekt im Zeitplan bleibt.</p>"
            "<p>Bei Fragen stehen wir Ihnen gerne zur Verfügung.</p>"
            "<p>Beste Grüße,<br>Ihr {{TENANT_NAME}} Team</p>"
        ),
        "variables": ["FIRST_NAME", "TENANT_NAME", "ASSET_LIST", "DEADLINE"],
    },

    # =====================================================================
    # B. LIFECYCLE-LUECKEN (8)
    # =====================================================================
    {
        "slug": "kickoff-bestaetigung",
        "name": "Kickoff-Zusammenfassung",
        "subject": "Zusammenfassung Ihres Kickoff-Meetings — {{TENANT_NAME}}",
        "body_html": (
            '<h1 style="color: #333;">Kickoff-Zusammenfassung</h1>'
            "<p>Hallo {{FIRST_NAME}},</p>"
            "<p>vielen Dank für das produktive Kickoff-Meeting! Hier die wichtigsten "
            "Ergebnisse auf einen Blick:</p>"
            "<p><strong>Vereinbarte Ziele:</strong></p>"
            "<p>{{GOALS_SUMMARY}}</p>"
            "<p><strong>Nächste Schritte:</strong></p>"
            "<p>{{NEXT_STEPS}}</p>"
            "<p><strong>Zeitplan:</strong></p>"
            "<p>{{TIMELINE}}</p>"
            "<p>Das vollständige Protokoll finden Sie im Anhang bzw. in Ihrem Kundenportal.</p>"
            "<p>Beste Grüße,<br>Ihr {{TENANT_NAME}} Team</p>"
        ),
        "variables": ["FIRST_NAME", "TENANT_NAME", "GOALS_SUMMARY", "NEXT_STEPS", "TIMELINE"],
    },
    {
        "slug": "woechentliches-status-update",
        "name": "Wöchentliches Update",
        "subject": "Wöchentliches Update KW {{CALENDAR_WEEK}} — {{TENANT_NAME}}",
        "body_html": (
            '<h1 style="color: #333;">Ihr wöchentliches Update</h1>'
            "<p>Hallo {{FIRST_NAME}},</p>"
            "<p>hier ist Ihr Status-Update für <strong>KW {{CALENDAR_WEEK}}</strong>:</p>"
            "<p><strong>Erledigt diese Woche:</strong></p>"
            "<p>{{COMPLETED_TASKS}}</p>"
            "<p><strong>In Arbeit:</strong></p>"
            "<p>{{IN_PROGRESS_TASKS}}</p>"
            "<p><strong>Geplant für nächste Woche:</strong></p>"
            "<p>{{PLANNED_TASKS}}</p>"
            '<p><a href="{{DASHBOARD_URL}}" style="display: inline-block; padding: 12px 24px; '
            "background-color: #000; color: #fff; text-decoration: none; "
            'border-radius: 6px;">Zum Dashboard</a></p>'
            "<p>Beste Grüße,<br>Ihr {{TENANT_NAME}} Team</p>"
        ),
        "variables": ["FIRST_NAME", "TENANT_NAME", "CALENDAR_WEEK", "COMPLETED_TASKS", "IN_PROGRESS_TASKS", "PLANNED_TASKS", "DASHBOARD_URL"],
    },
    {
        "slug": "monatsreport",
        "name": "Monatsreport",
        "subject": "Ihr Monatsreport {{MONTH}} — {{TENANT_NAME}}",
        "body_html": (
            '<h1 style="color: #333;">Monatsreport {{MONTH}}</h1>'
            "<p>Hallo {{FIRST_NAME}},</p>"
            "<p>Ihr Monatsreport für <strong>{{MONTH}}</strong> ist fertig. "
            "Hier die wichtigsten Kennzahlen:</p>"
            "<p><strong>Highlights:</strong></p>"
            "<p>{{KPI_SUMMARY}}</p>"
            "<p><strong>Entwicklung:</strong></p>"
            "<p>{{TREND_SUMMARY}}</p>"
            '<p><a href="{{REPORT_URL}}" style="display: inline-block; padding: 12px 24px; '
            "background-color: #000; color: #fff; text-decoration: none; "
            'border-radius: 6px;">Vollständigen Report ansehen</a></p>'
            "<p>Beste Grüße,<br>Ihr {{TENANT_NAME}} Team</p>"
        ),
        "variables": ["FIRST_NAME", "TENANT_NAME", "MONTH", "KPI_SUMMARY", "TREND_SUMMARY", "REPORT_URL"],
    },
    {
        "slug": "quartals-review-einladung",
        "name": "Quartals-Review Einladung",
        "subject": "Einladung zum Quartals-Review — {{TENANT_NAME}}",
        "body_html": (
            '<h1 style="color: #333;">Quartals-Review steht an</h1>'
            "<p>Hallo {{FIRST_NAME}},</p>"
            "<p>es ist wieder Zeit für unseren gemeinsamen Quartals-Review! "
            "Wir möchten die Ergebnisse der letzten drei Monate besprechen und "
            "die Strategie für das nächste Quartal planen.</p>"
            "<p><strong>Vorgeschlagener Termin:</strong><br>"
            "{{MEETING_DATE}} um {{MEETING_TIME}}<br>"
            "Dauer: ca. 60 Minuten</p>"
            "<p><strong>Agenda:</strong></p>"
            "<ul>"
            "<li>Ergebnisse Q{{QUARTER}} im Überblick</li>"
            "<li>ROI-Analyse</li>"
            "<li>Strategie-Anpassungen</li>"
            "<li>Ziele Q{{NEXT_QUARTER}}</li>"
            "</ul>"
            '<p><a href="{{BOOKING_URL}}" style="display: inline-block; padding: 12px 24px; '
            "background-color: #000; color: #fff; text-decoration: none; "
            'border-radius: 6px;">Termin bestätigen</a></p>'
            "<p>Beste Grüße,<br>Ihr {{TENANT_NAME}} Team</p>"
        ),
        "variables": ["FIRST_NAME", "TENANT_NAME", "MEETING_DATE", "MEETING_TIME", "QUARTER", "NEXT_QUARTER", "BOOKING_URL"],
    },
    {
        "slug": "meilenstein-feier",
        "name": "Meilenstein erreicht",
        "subject": "Herzlichen Glückwunsch — Meilenstein erreicht! 🎉",
        "body_html": (
            '<h1 style="color: #333;">Meilenstein erreicht!</h1>'
            "<p>Hallo {{FIRST_NAME}},</p>"
            "<p>wir haben großartige Neuigkeiten: <strong>{{MILESTONE_TITLE}}</strong> "
            "wurde erreicht!</p>"
            "<p>{{MILESTONE_DETAILS}}</p>"
            "<p>Das ist ein tolles Ergebnis, das zeigt, dass unsere gemeinsame "
            "Strategie aufgeht. Weiter so!</p>"
            "<p>Herzliche Grüße,<br>Ihr {{TENANT_NAME}} Team</p>"
        ),
        "variables": ["FIRST_NAME", "TENANT_NAME", "MILESTONE_TITLE", "MILESTONE_DETAILS"],
    },
    {
        "slug": "30-tage-check-in",
        "name": "30-Tage Check-in",
        "subject": "Ihr erster Monat bei {{TENANT_NAME}} — wie läuft es?",
        "body_html": (
            '<h1 style="color: #333;">Ihr erster Monat</h1>'
            "<p>Hallo {{FIRST_NAME}},</p>"
            "<p>Sie sind jetzt seit 30 Tagen bei uns — ein guter Moment für "
            "ein kurzes Zwischenfazit!</p>"
            "<p><strong>Was bisher passiert ist:</strong></p>"
            "<p>{{PROGRESS_SUMMARY}}</p>"
            "<p>Wir möchten wissen: Wie zufrieden sind Sie bisher? Gibt es "
            "etwas, das wir verbessern können?</p>"
            '<p><a href="{{FEEDBACK_URL}}" style="display: inline-block; padding: 12px 24px; '
            "background-color: #000; color: #fff; text-decoration: none; "
            'border-radius: 6px;">Kurzes Feedback geben</a></p>'
            "<p>Beste Grüße,<br>Ihr {{TENANT_NAME}} Team</p>"
        ),
        "variables": ["FIRST_NAME", "TENANT_NAME", "PROGRESS_SUMMARY", "FEEDBACK_URL"],
    },
    {
        "slug": "vertragsverlaengerung-erinnerung",
        "name": "Vertragsverlängerung",
        "subject": "Ihre Vertragsverlängerung — {{TENANT_NAME}}",
        "body_html": (
            '<h1 style="color: #333;">Ihre Vertragsverlängerung steht an</h1>'
            "<p>Hallo {{FIRST_NAME}},</p>"
            "<p>Ihr aktueller Vertrag bei {{TENANT_NAME}} läuft am "
            "<strong>{{CONTRACT_END_DATE}}</strong> aus.</p>"
            "<p><strong>Ihre Ergebnisse auf einen Blick:</strong></p>"
            "<p>{{RESULTS_SUMMARY}}</p>"
            "<p>Wir würden uns freuen, die erfolgreiche Zusammenarbeit fortzusetzen. "
            "Gerne besprechen wir mit Ihnen die Optionen für die Verlängerung.</p>"
            '<p><a href="{{RENEWAL_URL}}" style="display: inline-block; padding: 12px 24px; '
            "background-color: #000; color: #fff; text-decoration: none; "
            'border-radius: 6px;">Verlängerung besprechen</a></p>'
            "<p>Beste Grüße,<br>Ihr {{TENANT_NAME}} Team</p>"
        ),
        "variables": ["FIRST_NAME", "TENANT_NAME", "CONTRACT_END_DATE", "RESULTS_SUMMARY", "RENEWAL_URL"],
    },
    {
        "slug": "halbjahres-review",
        "name": "Halbjahres-Review",
        "subject": "6-Monats-Review — {{TENANT_NAME}}",
        "body_html": (
            '<h1 style="color: #333;">Ihr Halbjahres-Review</h1>'
            "<p>Hallo {{FIRST_NAME}},</p>"
            "<p>ein halbes Jahr Zusammenarbeit — das ist ein guter Anlass, um "
            "zurückzublicken und nach vorne zu schauen.</p>"
            "<p><strong>Ergebnisse der letzten 6 Monate:</strong></p>"
            "<p>{{HALF_YEAR_SUMMARY}}</p>"
            "<p><strong>ROI:</strong> {{ROI_SUMMARY}}</p>"
            "<p>Wir möchten mit Ihnen besprechen, wie wir die nächsten 6 Monate "
            "noch erfolgreicher gestalten können.</p>"
            '<p><a href="{{BOOKING_URL}}" style="display: inline-block; padding: 12px 24px; '
            "background-color: #000; color: #fff; text-decoration: none; "
            'border-radius: 6px;">Review-Termin buchen</a></p>'
            "<p>Beste Grüße,<br>Ihr {{TENANT_NAME}} Team</p>"
        ),
        "variables": ["FIRST_NAME", "TENANT_NAME", "HALF_YEAR_SUMMARY", "ROI_SUMMARY", "BOOKING_URL"],
    },

    # =====================================================================
    # C. ENGAGEMENT / BEZIEHUNG (5)
    # =====================================================================
    {
        "slug": "tier-upgrade",
        "name": "Stufen-Upgrade",
        "subject": "Upgrade auf {{NEW_TIER}} — {{TENANT_NAME}}",
        "body_html": (
            '<h1 style="color: #333;">Herzlichen Glückwunsch zum Upgrade!</h1>'
            "<p>Hallo {{FIRST_NAME}},</p>"
            "<p>aufgrund Ihres Wachstums qualifizieren Sie sich jetzt für unser "
            "<strong>{{NEW_TIER}}</strong>-Paket!</p>"
            "<p><strong>Was sich für Sie ändert:</strong></p>"
            "<p>{{UPGRADE_BENEFITS}}</p>"
            "<p>Wir möchten die Details gerne persönlich mit Ihnen besprechen.</p>"
            '<p><a href="{{BOOKING_URL}}" style="display: inline-block; padding: 12px 24px; '
            "background-color: #000; color: #fff; text-decoration: none; "
            'border-radius: 6px;">Beratungstermin buchen</a></p>'
            "<p>Beste Grüße,<br>Ihr {{TENANT_NAME}} Team</p>"
        ),
        "variables": ["FIRST_NAME", "TENANT_NAME", "NEW_TIER", "UPGRADE_BENEFITS", "BOOKING_URL"],
    },
    {
        "slug": "empfehlungs-anfrage",
        "name": "Empfehlungs-Anfrage",
        "subject": "Kennen Sie jemanden, der von {{TENANT_NAME}} profitieren könnte?",
        "body_html": (
            '<h1 style="color: #333;">Empfehlen Sie uns weiter</h1>'
            "<p>Hallo {{FIRST_NAME}},</p>"
            "<p>wir freuen uns sehr über die erfolgreiche Zusammenarbeit mit Ihnen! "
            "Kennen Sie jemanden in Ihrem Netzwerk, der ebenfalls von unseren "
            "Services profitieren könnte?</p>"
            "<p><strong>Unser Empfehlungs-Programm:</strong></p>"
            "<p>{{REFERRAL_BENEFITS}}</p>"
            '<p><a href="{{REFERRAL_URL}}" style="display: inline-block; padding: 12px 24px; '
            "background-color: #000; color: #fff; text-decoration: none; "
            'border-radius: 6px;">Jetzt empfehlen</a></p>'
            "<p>Beste Grüße,<br>Ihr {{TENANT_NAME}} Team</p>"
        ),
        "variables": ["FIRST_NAME", "TENANT_NAME", "REFERRAL_BENEFITS", "REFERRAL_URL"],
    },
    {
        "slug": "upsell-angebot",
        "name": "Zusätzliche Services",
        "subject": "Neues Service-Angebot für Sie — {{TENANT_NAME}}",
        "body_html": (
            '<h1 style="color: #333;">Passend für Ihre Ziele</h1>'
            "<p>Hallo {{FIRST_NAME}},</p>"
            "<p>basierend auf Ihren bisherigen Ergebnissen sehen wir zusätzliches "
            "Potenzial in folgendem Bereich:</p>"
            "<p><strong>{{SERVICE_NAME}}</strong></p>"
            "<p>{{SERVICE_DESCRIPTION}}</p>"
            "<p><strong>Erwarteter Mehrwert:</strong></p>"
            "<p>{{EXPECTED_VALUE}}</p>"
            '<p><a href="{{OFFER_URL}}" style="display: inline-block; padding: 12px 24px; '
            "background-color: #000; color: #fff; text-decoration: none; "
            'border-radius: 6px;">Angebot ansehen</a></p>'
            "<p>Beste Grüße,<br>Ihr {{TENANT_NAME}} Team</p>"
        ),
        "variables": ["FIRST_NAME", "TENANT_NAME", "SERVICE_NAME", "SERVICE_DESCRIPTION", "EXPECTED_VALUE", "OFFER_URL"],
    },
    {
        "slug": "win-back",
        "name": "Win-Back",
        "subject": "Wir vermissen Sie, {{FIRST_NAME}} — {{TENANT_NAME}}",
        "body_html": (
            '<h1 style="color: #333;">Wir vermissen Sie!</h1>'
            "<p>Hallo {{FIRST_NAME}},</p>"
            "<p>es ist eine Weile her, seit wir zusammengearbeitet haben, und "
            "wir möchten gerne wissen, wie es Ihnen geht.</p>"
            "<p>Seitdem hat sich bei uns einiges getan:</p>"
            "<p>{{WHATS_NEW}}</p>"
            "<p>Wir würden uns freuen, wenn wir gemeinsam besprechen, ob und wie "
            "wir Ihnen erneut helfen können.</p>"
            '<p><a href="{{BOOKING_URL}}" style="display: inline-block; padding: 12px 24px; '
            "background-color: #000; color: #fff; text-decoration: none; "
            'border-radius: 6px;">Unverbindlich sprechen</a></p>'
            "<p>Herzliche Grüße,<br>Ihr {{TENANT_NAME}} Team</p>"
        ),
        "variables": ["FIRST_NAME", "TENANT_NAME", "WHATS_NEW", "BOOKING_URL"],
    },
    {
        "slug": "jubilaeum",
        "name": "Partnerschafts-Jubiläum",
        "subject": "{{ANNIVERSARY_DURATION}} gemeinsam — Danke, {{FIRST_NAME}}!",
        "body_html": (
            '<h1 style="color: #333;">Happy Anniversary!</h1>'
            "<p>Hallo {{FIRST_NAME}},</p>"
            "<p>heute vor <strong>{{ANNIVERSARY_DURATION}}</strong> hat unsere "
            "Zusammenarbeit begonnen — das möchten wir feiern!</p>"
            "<p><strong>Gemeinsam erreicht:</strong></p>"
            "<p>{{ACHIEVEMENTS_SUMMARY}}</p>"
            "<p>Vielen Dank für Ihr Vertrauen. Wir freuen uns auf viele weitere "
            "erfolgreiche Monate!</p>"
            "<p>Herzliche Grüße,<br>Ihr {{TENANT_NAME}} Team</p>"
        ),
        "variables": ["FIRST_NAME", "TENANT_NAME", "ANNIVERSARY_DURATION", "ACHIEVEMENTS_SUMMARY"],
    },

    # =====================================================================
    # D. CHURN-PRAEVENTION (5)
    # =====================================================================
    {
        "slug": "churn-warnung-intern",
        "name": "Churn-Warnung (intern)",
        "subject": "[INTERN] Churn-Risiko: {{CLIENT_NAME}} — Health Score {{HEALTH_SCORE}}",
        "body_html": (
            '<h1 style="color: #c00;">Churn-Warnung</h1>'
            "<p><strong>Mandant:</strong> {{CLIENT_NAME}}<br>"
            "<strong>Health Score:</strong> {{HEALTH_SCORE}}<br>"
            "<strong>Ansprechpartner:</strong> {{CONTACT_NAME}}<br>"
            "<strong>Vertragslaufzeit:</strong> {{CONTRACT_DURATION}}</p>"
            "<p><strong>Risikofaktoren:</strong></p>"
            "<p>{{RISK_FACTORS}}</p>"
            "<p><strong>Empfohlene Maßnahmen:</strong></p>"
            "<p>{{RECOMMENDED_ACTIONS}}</p>"
            "<p>Bitte innerhalb von 48 Stunden Kontakt aufnehmen.</p>"
        ),
        "variables": ["CLIENT_NAME", "HEALTH_SCORE", "CONTACT_NAME", "CONTRACT_DURATION", "RISK_FACTORS", "RECOMMENDED_ACTIONS"],
    },
    {
        "slug": "zufriedenheits-check",
        "name": "Zufriedenheits-Check",
        "subject": "Kurze Frage an Sie — {{TENANT_NAME}}",
        "body_html": (
            '<h1 style="color: #333;">Wie zufrieden sind Sie?</h1>'
            "<p>Hallo {{FIRST_NAME}},</p>"
            "<p>Ihre Meinung ist uns wichtig. Mit einer einzigen Frage möchten wir "
            "herausfinden, wie zufrieden Sie aktuell mit unserer Zusammenarbeit sind:</p>"
            "<p><strong>Auf einer Skala von 1-5: Wie zufrieden sind Sie derzeit mit "
            "unserer Betreuung?</strong></p>"
            '<p><a href="{{SURVEY_URL}}" style="display: inline-block; padding: 12px 24px; '
            "background-color: #000; color: #fff; text-decoration: none; "
            'border-radius: 6px;">Jetzt bewerten (10 Sek.)</a></p>'
            "<p>Beste Grüße,<br>Ihr {{TENANT_NAME}} Team</p>"
        ),
        "variables": ["FIRST_NAME", "TENANT_NAME", "SURVEY_URL"],
    },
    {
        "slug": "vertragsverlaengerung-nachfass",
        "name": "Vertragsverlängerung Nachfass",
        "subject": "Ihr Vertrag endet in 30 Tagen — {{TENANT_NAME}}",
        "body_html": (
            '<h1 style="color: #333;">Nur noch 30 Tage</h1>'
            "<p>Hallo {{FIRST_NAME}},</p>"
            "<p>Ihr Vertrag bei {{TENANT_NAME}} endet am "
            "<strong>{{CONTRACT_END_DATE}}</strong> — das ist in 30 Tagen.</p>"
            "<p>Wir haben Ihnen noch keine Rückmeldung zur Verlängerung erhalten. "
            "Damit es nahtlos weitergeht, würden wir gerne zeitnah mit Ihnen sprechen.</p>"
            "<p><strong>Ihre Optionen:</strong></p>"
            "<ul>"
            "<li>Vertrag zu aktuellen Konditionen verlängern</li>"
            "<li>Paket anpassen (Up-/Downgrade)</li>"
            "<li>Persönliches Gespräch über Ihre Wünsche</li>"
            "</ul>"
            '<p><a href="{{BOOKING_URL}}" style="display: inline-block; padding: 12px 24px; '
            "background-color: #000; color: #fff; text-decoration: none; "
            'border-radius: 6px;">Termin vereinbaren</a></p>'
            "<p>Beste Grüße,<br>Ihr {{TENANT_NAME}} Team</p>"
        ),
        "variables": ["FIRST_NAME", "TENANT_NAME", "CONTRACT_END_DATE", "BOOKING_URL"],
    },
    {
        "slug": "pause-statt-kuendigung",
        "name": "Pause statt Kündigung",
        "subject": "Eine Alternative zur Kündigung — {{TENANT_NAME}}",
        "body_html": (
            '<h1 style="color: #333;">Bevor Sie gehen...</h1>'
            "<p>Hallo {{FIRST_NAME}},</p>"
            "<p>wir haben verstanden, dass Sie über eine Kündigung nachdenken. "
            "Bevor Sie eine endgültige Entscheidung treffen, möchten wir Ihnen "
            "eine Alternative anbieten:</p>"
            "<p><strong>Pause statt Kündigung:</strong></p>"
            "<p>Sie können Ihren Vertrag für bis zu {{MAX_PAUSE_MONTHS}} Monate "
            "pausieren. Während der Pause:</p>"
            "<ul>"
            "<li>Keine Kosten</li>"
            "<li>Ihre Daten und Einstellungen bleiben erhalten</li>"
            "<li>Nahtloser Neustart jederzeit möglich</li>"
            "</ul>"
            '<p><a href="{{PAUSE_URL}}" style="display: inline-block; padding: 12px 24px; '
            "background-color: #000; color: #fff; text-decoration: none; "
            'border-radius: 6px;">Pause beantragen</a></p>'
            "<p>Oder sprechen Sie persönlich mit uns — vielleicht finden wir "
            "gemeinsam eine noch bessere Lösung.</p>"
            "<p>Beste Grüße,<br>Ihr {{TENANT_NAME}} Team</p>"
        ),
        "variables": ["FIRST_NAME", "TENANT_NAME", "MAX_PAUSE_MONTHS", "PAUSE_URL"],
    },
    {
        "slug": "reaktivierung",
        "name": "Reaktivierung nach Pause",
        "subject": "Willkommen zurück, {{FIRST_NAME}}! — {{TENANT_NAME}}",
        "body_html": (
            '<h1 style="color: #333;">Willkommen zurück!</h1>'
            "<p>Hallo {{FIRST_NAME}},</p>"
            "<p>Ihre Pause endet am <strong>{{PAUSE_END_DATE}}</strong>. "
            "Wir haben alles vorbereitet, damit Sie nahtlos wieder starten können!</p>"
            "<p><strong>Neustart-Überblick:</strong></p>"
            "<p>{{RESTART_SUMMARY}}</p>"
            "<p>Wir schlagen vor, mit einem kurzen Re-Kickoff zu starten, "
            "um Ihre aktuellen Ziele und Prioritäten abzustimmen.</p>"
            '<p><a href="{{BOOKING_URL}}" style="display: inline-block; padding: 12px 24px; '
            "background-color: #000; color: #fff; text-decoration: none; "
            'border-radius: 6px;">Re-Kickoff buchen</a></p>'
            "<p>Wir freuen uns, Sie wieder an Bord zu haben!</p>"
            "<p>Herzliche Grüße,<br>Ihr {{TENANT_NAME}} Team</p>"
        ),
        "variables": ["FIRST_NAME", "TENANT_NAME", "PAUSE_END_DATE", "RESTART_SUMMARY", "BOOKING_URL"],
    },
]

SEQUENCES = [
    {
        "slug": "aftersales-onboarding",
        "name": "After-Sales Onboarding",
        "description": "Automatisierte Onboarding-Sequenz fuer neue Kunden (Tag 0 bis Tag 180).",
        "steps": [
            {"template_slug": "willkommens-email", "position": 1, "delay_days": 0, "delay_hours": 0},
            {"template_slug": "team-vorstellung", "position": 2, "delay_days": 1, "delay_hours": 0},
            {"template_slug": "onboarding-checklist", "position": 3, "delay_days": 3, "delay_hours": 0},
            {"template_slug": "30-tage-check-in", "position": 4, "delay_days": 30, "delay_hours": 0},
            {"template_slug": "insights-feedback", "position": 5, "delay_days": 60, "delay_hours": 0},
            {"template_slug": "nps-review", "position": 6, "delay_days": 90, "delay_hours": 0},
            {"template_slug": "halbjahres-review", "position": 7, "delay_days": 180, "delay_hours": 0},
        ],
    },
    {
        "slug": "vertragsverlaengerung",
        "name": "Vertragsverlängerung",
        "description": "Automatisierte Erinnerungs-Sequenz zur Vertragsverlängerung (60 + 30 Tage vor Vertragsende).",
        "steps": [
            {"template_slug": "vertragsverlaengerung-erinnerung", "position": 1, "delay_days": 0, "delay_hours": 0},
            {"template_slug": "vertragsverlaengerung-nachfass", "position": 2, "delay_days": 30, "delay_hours": 0},
        ],
    },
    {
        "slug": "win-back-sequenz",
        "name": "Win-Back Sequenz",
        "description": "Automatisierte Rueckgewinnungs-Sequenz nach Churn (90 + 180 Tage nach Vertragsende).",
        "steps": [
            {"template_slug": "win-back", "position": 1, "delay_days": 0, "delay_hours": 0},
            {"template_slug": "win-back", "position": 2, "delay_days": 90, "delay_hours": 0},
        ],
    },
]
# fmt: on


class Command(BaseCommand):
    help = "Seed system-default email templates and sequences (tenant=NULL)."

    def handle(self, *args, **options):
        from apps.emails.models import EmailSequence, EmailTemplate, SequenceStep

        created_templates = 0
        updated_templates = 0

        for tpl_data in TEMPLATES:
            tpl, created = EmailTemplate.objects.update_or_create(
                tenant=None,
                slug=tpl_data["slug"],
                defaults={
                    "name": tpl_data["name"],
                    "subject": tpl_data["subject"],
                    "body_html": tpl_data["body_html"],
                    "variables": tpl_data["variables"],
                    "is_active": True,
                },
            )
            if created:
                created_templates += 1
            else:
                updated_templates += 1

        self.stdout.write(
            f"Templates: {created_templates} created, {updated_templates} updated."
        )

        created_sequences = 0
        updated_sequences = 0
        for seq_data in SEQUENCES:
            seq, created = EmailSequence.objects.update_or_create(
                tenant=None,
                slug=seq_data["slug"],
                defaults={
                    "name": seq_data["name"],
                    "description": seq_data["description"],
                    "is_active": True,
                },
            )
            if created:
                created_sequences += 1
            else:
                updated_sequences += 1

            # Bestehende Steps loeschen und neu erstellen fuer konsistente Reihenfolge
            seq.steps.all().delete()
            for step_data in seq_data["steps"]:
                template = EmailTemplate.objects.get(
                    tenant=None, slug=step_data["template_slug"],
                )
                SequenceStep.objects.create(
                    sequence=seq,
                    template=template,
                    position=step_data["position"],
                    delay_days=step_data["delay_days"],
                    delay_hours=step_data["delay_hours"],
                    is_active=True,
                )

        self.stdout.write(
            f"Sequences: {created_sequences} created, {updated_sequences} updated."
        )
        self.stdout.write(self.style.SUCCESS("Email seed data loaded successfully."))
