"""Seed ~28 system-wide TaskTemplates for the 11-phase after-sales process."""

from django.core.management.base import BaseCommand

from apps.emails.models import EmailTemplate
from apps.integrations.models import ActionSequence
from apps.tasks.models import TaskList, TaskListItem, TaskTemplate

# fmt: off
SYSTEM_TEMPLATES = [
    # Phase 0: Setup & Vorbereitung
    {
        "slug": "jira-projekt-erstellen",
        "name": "Jira-Projekt erstellen",
        "description": "Neues Jira-Projekt fuer den Mandanten anlegen mit Board und Standardtickets.",
        "action_type": "jira_project",
        "phase": 0,
        "day_offset": -3,
        "priority": "high",
        "trigger_mode": "manual",
        "default_subtasks": ["Projektschluessel festlegen", "Board erstellen", "Standardtickets anlegen"],
    },
    {
        "slug": "cloud-ordner-anlegen",
        "name": "Cloud-Ordner anlegen",
        "description": "Google Drive / SharePoint Ordnerstruktur fuer den Mandanten erstellen.",
        "action_type": "manual",
        "phase": 0,
        "day_offset": -3,
        "priority": "high",
        "trigger_mode": "manual",
        "default_subtasks": ["Hauptordner erstellen", "Unterordner anlegen", "Zugriffsrechte setzen", "Link im CRM hinterlegen"],
    },
    {
        "slug": "team-briefing",
        "name": "Team-Briefing durchfuehren",
        "description": "Internes Briefing mit allen beteiligten Teammitgliedern zum neuen Mandanten.",
        "action_type": "meeting",
        "phase": 0,
        "day_offset": -1,
        "priority": "high",
        "trigger_mode": "manual",
        "default_subtasks": [],
    },
    # Phase 1: Willkommen (Tag 0)
    {
        "slug": "willkommens-email",
        "name": "Willkommens-E-Mail versenden",
        "description": "Persoenliche Willkommens-E-Mail an den Mandanten senden.",
        "action_type": "email",
        "phase": 1,
        "day_offset": 0,
        "priority": "critical",
        "trigger_mode": "auto_on_due",
        "default_subtasks": [],
    },
    {
        "slug": "welcome-package",
        "name": "Welcome Package versenden",
        "description": "Physisches Welcome Package mit Branding-Materialien verschicken.",
        "action_type": "package",
        "phase": 1,
        "day_offset": 0,
        "priority": "high",
        "trigger_mode": "manual",
        "default_subtasks": ["Adresse pruefen", "Paket zusammenstellen", "Versandlabel erstellen", "Versand bestaetigen"],
    },
    {
        "slug": "welcome-package-versand-email",
        "name": "Welcome-Package-Versand per E-Mail ankuendigen",
        "description": "E-Mail senden, dass das physische Welcome Package unterwegs ist (inkl. Sendungsnummer).",
        "action_type": "email",
        "phase": 1,
        "day_offset": 1,
        "priority": "medium",
        "trigger_mode": "auto_on_due",
        "default_subtasks": [],
    },
    {
        "slug": "rechnung-ankuendigung",
        "name": "Rechnungsankuendigung senden",
        "description": "Ankuendigungs-E-Mail versenden, dass die Rechnung morgen kommt.",
        "action_type": "email",
        "phase": 1,
        "day_offset": 0,
        "priority": "medium",
        "trigger_mode": "auto_on_due",
        "default_subtasks": [],
    },
    # Phase 2: Onboarding (Tag 1-7)
    {
        "slug": "onboarding-fragebogen",
        "name": "Onboarding-Fragebogen senden",
        "description": "Fragebogen zur Erfassung aller relevanten Mandanten-Informationen versenden.",
        "action_type": "document",
        "phase": 2,
        "day_offset": 1,
        "priority": "high",
        "trigger_mode": "manual",
        "default_subtasks": [],
    },
    {
        "slug": "kickoff-meeting",
        "name": "Kickoff-Meeting durchfuehren",
        "description": "Erstes Strategiemeeting mit dem Mandanten. Ziele, Erwartungen und Meilensteine besprechen.",
        "action_type": "meeting",
        "phase": 2,
        "day_offset": 3,
        "priority": "critical",
        "trigger_mode": "manual",
        "default_subtasks": ["Agenda vorbereiten", "Meeting-Link senden", "Protokoll erstellen"],
    },
    {
        "slug": "kickoff-zusammenfassung",
        "name": "Kickoff-Zusammenfassung senden",
        "description": "E-Mail mit der Zusammenfassung des Kickoff-Meetings (Ziele, naechste Schritte, Zeitplan) versenden.",
        "action_type": "email",
        "phase": 2,
        "day_offset": 4,
        "priority": "high",
        "trigger_mode": "manual",
        "default_subtasks": [],
    },
    {
        "slug": "zugaenge-einrichten",
        "name": "Zugaenge einrichten",
        "description": "Alle notwendigen Tool-Zugaenge fuer den Mandanten einrichten.",
        "action_type": "manual",
        "phase": 2,
        "day_offset": 3,
        "priority": "high",
        "trigger_mode": "manual",
        "default_subtasks": ["Analytics-Zugang", "CMS-Zugang", "Social-Media-Zugaenge", "Ads-Konten verknuepfen"],
    },
    # Phase 3: Erste Woche (Tag 7-14)
    {
        "slug": "erste-woche-check-in",
        "name": "Check-in Anruf (Woche 1)",
        "description": "Kurzer Anruf nach der ersten Woche: Wie laeuft es? Offene Fragen?",
        "action_type": "phone",
        "phase": 3,
        "day_offset": 7,
        "priority": "high",
        "trigger_mode": "manual",
        "default_subtasks": [],
    },
    {
        "slug": "erste-woche-email",
        "name": "Woche-1-Status-Update senden",
        "description": "Status-Update E-Mail mit ersten Ergebnissen und naechsten Schritten.",
        "action_type": "email",
        "phase": 3,
        "day_offset": 7,
        "priority": "medium",
        "trigger_mode": "auto_on_due",
        "default_subtasks": [],
    },
    {
        "slug": "woechentliches-update",
        "name": "Woechentliches Status-Update senden",
        "description": "Regelmaessiges woechentliches Update per E-Mail an den Mandanten senden.",
        "action_type": "email",
        "phase": 3,
        "day_offset": 14,
        "priority": "medium",
        "trigger_mode": "auto_on_due",
        "default_subtasks": [],
    },
    # Phase 4: Quick Wins (Tag 14-21)
    {
        "slug": "quick-win-praesentation",
        "name": "Quick Wins praesentieren",
        "description": "Erste sichtbare Ergebnisse (Quick Wins) dem Mandanten praesentieren.",
        "action_type": "meeting",
        "phase": 4,
        "day_offset": 14,
        "priority": "high",
        "trigger_mode": "manual",
        "default_subtasks": ["Ergebnisse aufbereiten", "Praesentation erstellen", "Termin abstimmen"],
    },
    # Phase 5: Erster Monat (Tag 30)
    {
        "slug": "monats-review-1",
        "name": "1. Monats-Review",
        "description": "Umfassender Review des ersten Monats mit KPIs und Ergebnissen.",
        "action_type": "meeting",
        "phase": 5,
        "day_offset": 30,
        "priority": "high",
        "trigger_mode": "manual",
        "default_subtasks": ["KPI-Report erstellen", "Praesentation vorbereiten", "Naechste Ziele definieren"],
    },
    {
        "slug": "monats-report-email-1",
        "name": "Monatsreport E-Mail (Monat 1)",
        "description": "Schriftlichen Monatsreport per E-Mail senden.",
        "action_type": "email",
        "phase": 5,
        "day_offset": 30,
        "priority": "medium",
        "trigger_mode": "auto_on_due",
        "default_subtasks": [],
    },
    {
        "slug": "30-tage-check-in",
        "name": "30-Tage Check-in senden",
        "description": "Check-in E-Mail nach 30 Tagen: Wie zufrieden ist der Mandant? Gibt es Verbesserungswuensche?",
        "action_type": "email",
        "phase": 5,
        "day_offset": 30,
        "priority": "high",
        "trigger_mode": "auto_on_due",
        "default_subtasks": [],
    },
    # Phase 6: Laufende Betreuung (Tag 60)
    {
        "slug": "check-in-monat-2",
        "name": "Check-in Anruf (Monat 2)",
        "description": "Regelmaessiger Check-in: Zufriedenheit, offene Punkte, neue Anforderungen.",
        "action_type": "phone",
        "phase": 6,
        "day_offset": 60,
        "priority": "medium",
        "trigger_mode": "manual",
        "default_subtasks": [],
    },
    {
        "slug": "monats-report-email-2",
        "name": "Monatsreport E-Mail (Monat 2)",
        "description": "Schriftlichen Monatsreport per E-Mail senden.",
        "action_type": "email",
        "phase": 6,
        "day_offset": 60,
        "priority": "medium",
        "trigger_mode": "auto_on_due",
        "default_subtasks": [],
    },
    # Phase 7: NPS & Feedback (Tag 90)
    {
        "slug": "nps-umfrage",
        "name": "NPS-Umfrage senden",
        "description": "Net Promoter Score Umfrage nach 90 Tagen versenden.",
        "action_type": "email",
        "phase": 7,
        "day_offset": 90,
        "priority": "high",
        "trigger_mode": "auto_on_due",
        "default_subtasks": [],
    },
    {
        "slug": "testimonial-anfrage",
        "name": "Testimonial / Bewertung anfragen",
        "description": "Bei zufriedenen Mandanten (NPS >= 9) um Testimonial oder Google-Bewertung bitten.",
        "action_type": "email",
        "phase": 7,
        "day_offset": 95,
        "priority": "medium",
        "trigger_mode": "manual",
        "default_subtasks": [],
    },
    # Phase 8: Quartal-Review (Tag 90)
    {
        "slug": "quartals-review",
        "name": "Quartals-Review Meeting",
        "description": "Umfassender Quartals-Review: Ergebnisse, ROI, Strategie-Anpassung.",
        "action_type": "meeting",
        "phase": 8,
        "day_offset": 90,
        "priority": "high",
        "trigger_mode": "manual",
        "default_subtasks": ["Quartalsbericht erstellen", "ROI berechnen", "Strategie anpassen"],
    },
    {
        "slug": "quartals-review-einladung",
        "name": "Quartals-Review Einladung senden",
        "description": "Einladungs-E-Mail fuer den Quartals-Review 7-10 Tage vorher versenden.",
        "action_type": "email",
        "phase": 8,
        "day_offset": 83,
        "priority": "medium",
        "trigger_mode": "auto_on_due",
        "default_subtasks": [],
    },
    # Phase 9: Upselling (ab Tag 90)
    {
        "slug": "upselling-check",
        "name": "Upselling-Potenzial pruefen",
        "description": "Pruefen ob zusaetzliche Services fuer den Mandanten sinnvoll sind.",
        "action_type": "manual",
        "phase": 9,
        "day_offset": 100,
        "priority": "medium",
        "trigger_mode": "manual",
        "default_subtasks": ["Aktuelle Services reviewen", "Potenziale identifizieren", "Angebot vorbereiten"],
    },
    # Phase 10: Anti-Churn (laufend)
    {
        "slug": "health-check",
        "name": "Health-Check durchfuehren",
        "description": "Mandanten-Gesundheitscheck: Zufriedenheit, Engagement, Risikofaktoren pruefen.",
        "action_type": "manual",
        "phase": 10,
        "day_offset": 120,
        "priority": "high",
        "trigger_mode": "manual",
        "default_subtasks": ["Health Score aktualisieren", "Risikofaktoren pruefen", "Massnahmen ableiten"],
    },
    {
        "slug": "health-score-fragebogen",
        "name": "Health-Score Fragebogen ausfuellen",
        "description": "7 Kategorien (Ergebnis-Zufriedenheit, Kommunikation, Engagement, Beziehung, Zahlungsverhalten, Wachstumspotenzial, Empfehlungsbereitschaft) bewerten.",
        "action_type": "health_check",
        "phase": 10,
        "day_offset": 30,
        "priority": "high",
        "trigger_mode": "manual",
        "default_subtasks": [],
    },
    {
        "slug": "churn-warnsignale-pruefen",
        "name": "Churn-Warnsignale pruefen",
        "description": "10 Warnsignale fuer drohende Kuendigung pruefen (langsamere Antworten, verpasste Check-ins, Wettbewerber-Erwaehnung etc.).",
        "action_type": "churn_check",
        "phase": 10,
        "day_offset": 30,
        "priority": "high",
        "trigger_mode": "manual",
        "default_subtasks": [],
    },
    {
        "slug": "jubilaeum-email",
        "name": "Jubiläums-E-Mail senden",
        "description": "Partnerschafts-Jubilaeum feiern (6 Monate, 1 Jahr etc.) per E-Mail.",
        "action_type": "email",
        "phase": 10,
        "day_offset": 180,
        "priority": "low",
        "trigger_mode": "auto_on_due",
        "default_subtasks": [],
    },
    {
        "slug": "vertragsverlaengerung-start",
        "name": "Vertragsverlaengerung starten",
        "description": "Vertragsverlängerungs-Sequenz starten: Erinnerung 60 Tage vor Vertragsende senden.",
        "action_type": "email",
        "phase": 10,
        "day_offset": 305,
        "priority": "high",
        "trigger_mode": "auto_on_due",
        "default_subtasks": [],
    },
]
# fmt: on


class Command(BaseCommand):
    help = "Seed system-wide TaskTemplates for the 11-phase after-sales process."

    def handle(self, *args, **options):
        created = 0
        updated = 0

        for tpl_data in SYSTEM_TEMPLATES:
            slug = tpl_data["slug"]
            defaults = {k: v for k, v in tpl_data.items() if k != "slug"}

            _, was_created = TaskTemplate.objects.update_or_create(
                tenant=None,
                slug=slug,
                defaults=defaults,
            )
            if was_created:
                created += 1
            else:
                updated += 1

        self.stdout.write(
            self.style.SUCCESS(f"TaskTemplates: {created} erstellt, {updated} aktualisiert.")
        )

        # --- Zweiter Pass: Email-Templates und Jira-Sequenzen verknuepfen ---
        EMAIL_LINKS = {
            # Bestehende (korrigiert)
            "willkommens-email": ["willkommens-email"],
            "onboarding-fragebogen": ["onboarding-checklist"],
            "erste-woche-email": ["woechentliches-status-update"],
            "monats-report-email-1": ["monatsreport"],
            "monats-report-email-2": ["monatsreport"],
            "nps-umfrage": [
                "nps-review",
                "nps-followup-promoter",
                "nps-followup-passive",
                "nps-followup-detractor",
            ],
            "testimonial-anfrage": ["nps-followup-promoter"],
            # Neue Verknuepfungen
            "rechnung-ankuendigung": ["rechnung-ankuendigung"],
            "welcome-package-versand-email": ["briefkasten-hinweis"],
            "kickoff-zusammenfassung": ["kickoff-bestaetigung"],
            "woechentliches-update": ["woechentliches-status-update"],
            "30-tage-check-in": ["30-tage-check-in"],
            "quartals-review-einladung": ["quartals-review-einladung"],
            "jubilaeum-email": ["jubilaeum"],
            "vertragsverlaengerung-start": ["vertragsverlaengerung-erinnerung"],
        }

        JIRA_LINKS = {
            "jira-projekt-erstellen": {"action_sequence": "client-onboarding"},
        }

        linked = 0
        for task_slug, email_slugs in EMAIL_LINKS.items():
            try:
                tpl = TaskTemplate.objects.get(tenant=None, slug=task_slug)
            except TaskTemplate.DoesNotExist:
                continue
            email_tpls = EmailTemplate.objects.filter(
                tenant=None, slug__in=email_slugs, is_active=True,
            )
            if email_tpls.exists():
                tpl.email_templates.set(email_tpls)
                linked += 1

        for task_slug, jira_data in JIRA_LINKS.items():
            try:
                tpl = TaskTemplate.objects.get(tenant=None, slug=task_slug)
            except TaskTemplate.DoesNotExist:
                continue
            seq_slug = jira_data.get("action_sequence")
            if seq_slug:
                try:
                    seq = ActionSequence.objects.get(tenant=None, slug=seq_slug)
                    tpl.action_sequence = seq
                    tpl.save(update_fields=["action_sequence"])
                    linked += 1
                except ActionSequence.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f"ActionSequence '{seq_slug}' nicht gefunden — uebersprungen.")
                    )

        self.stdout.write(
            self.style.SUCCESS(f"Verknuepfungen: {linked} Templates mit Email/Jira verlinkt.")
        )

        # --- Dritter Pass: System-Aufgabenlisten erstellen ---
        PHASE_GROUP_LABELS = {
            0: "Setup & Vorbereitung",
            1: "Willkommen",
            2: "Onboarding",
            3: "Erste Woche",
            4: "Quick Wins",
            5: "Erster Monat",
            6: "Laufende Betreuung",
            7: "NPS & Feedback",
            8: "Quartal-Review",
            9: "Upselling",
            10: "Anti-Churn",
        }

        SYSTEM_LISTS = [
            {
                "slug": "onboarding-standard",
                "name": "Onboarding Standard",
                "description": "Vollstaendiger Onboarding-Workflow mit allen 11 Phasen.",
                "template_slugs": [tpl["slug"] for tpl in SYSTEM_TEMPLATES],
            },
        ]

        lists_created = 0
        for list_data in SYSTEM_LISTS:
            task_list, was_created = TaskList.objects.update_or_create(
                tenant=None,
                slug=list_data["slug"],
                defaults={
                    "name": list_data["name"],
                    "description": list_data["description"],
                },
            )
            if was_created:
                lists_created += 1

            # Items synchronisieren: bestehende loeschen und neu erstellen
            task_list.items.all().delete()
            for i, tpl_slug in enumerate(list_data["template_slugs"]):
                try:
                    tpl = TaskTemplate.objects.get(tenant=None, slug=tpl_slug)
                    TaskListItem.objects.create(
                        task_list=task_list,
                        task_template=tpl,
                        position=i,
                        group_label=PHASE_GROUP_LABELS.get(tpl.phase, ""),
                        group_position=tpl.phase,
                        day_offset=tpl.day_offset,
                    )
                except TaskTemplate.DoesNotExist:
                    self.stdout.write(
                        self.style.WARNING(f"Template '{tpl_slug}' fuer Liste '{list_data['slug']}' nicht gefunden.")
                    )

        self.stdout.write(
            self.style.SUCCESS(f"Aufgabenlisten: {lists_created} erstellt, {len(SYSTEM_LISTS) - lists_created} aktualisiert.")
        )
