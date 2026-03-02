# Email-Sequenz & Touchpoint-Timeline (90 Tage)

> Alle Kommunikations-Touchpoints der ersten 90 Tage als Gantt-Diagramm.
> Basierend auf: [After-Sales-Prozess.md](../After-Sales-Prozess.md) (Teil 4 & 5)

**Hinweis:** Das Startdatum 2025-01-01 ist fiktiv und steht fuer "Tag 0 = Vertragsabschluss". Alle Zeitangaben sind relativ zum Vertragsabschluss zu lesen.

---

## Diagramm

```mermaid
gantt
    title After-Sales Timeline (erste 90 Tage)
    dateFormat YYYY-MM-DD
    axisFormat %d. Tag

    section Emails
    Email 1 - Willkommen + Engagement       :milestone, e1, 2025-01-01, 0d
    Email 2 - Team-Vorstellung + Prozess     :milestone, e2, 2025-01-02, 0d
    Email 3 - Onboarding + Asset-Anfrage     :milestone, e3, 2025-01-04, 0d
    Email 4 - Erste Ergebnisse               :milestone, e4, 2025-01-22, 0d
    Email 5 - Insights + Feedback            :milestone, e5, 2025-02-01, 0d
    Email 6 - NPS + Review-Anfrage           :milestone, e6, 2025-04-01, 0d

    section Calls & Meetings
    Glueckwunsch-Anruf (GF)                  :milestone, c1, 2025-01-01, 0d
    Discovery Call                            :c2, 2025-01-02, 2d
    Kickoff-Meeting                           :milestone, c3, 2025-01-14, 0d
    Woechentliche Status-Emails              :c4, 2025-01-14, 77d
    Check-in Calls (alle 2 Wochen)           :c5, 2025-01-14, 77d
    30-Tage Check-in                         :milestone, c6, 2025-01-31, 0d
    Monatlicher Strategie-Review             :milestone, c7, 2025-02-01, 0d
    90-Tage Review                           :milestone, c8, 2025-04-01, 0d

    section Physisch
    Handgeschriebene Karte (Tag 0)           :milestone, p1, 2025-01-01, 0d
    Welcome Package versenden                :p2, 2025-01-01, 3d
    Handgeschriebene Karte (6 Wochen)        :milestone, p3, 2025-02-12, 0d
    Handgeschriebene Karte (12 Wochen)       :milestone, p4, 2025-03-26, 0d

    section Meilensteine
    Internes Setup (PM, Slack, Briefing)     :m1, 2025-01-01, 1d
    Fragebogen + Asset-Sammlung              :m2, 2025-01-03, 3d
    Tool-Zugriffe einrichten                 :m3, 2025-01-03, 3d
    Marketing-/Projekt-Audit                 :m4, 2025-01-07, 4d
    Quick Win liefern                        :crit, m5, 2025-01-07, 14d
    Strategie + 30/60/90-Tage-Plan           :m6, 2025-01-10, 5d
    Dashboards einrichten                    :m7, 2025-01-14, 1d
    Erste Meilenstein-Feier                  :milestone, m8, 2025-01-22, 0d
    Quarterly Business Review                :milestone, m9, 2025-04-01, 0d
```

---

## Legende

| Symbol | Bedeutung |
|---|---|
| Raute (Milestone) | Einmaliges Punkt-Event |
| Balken | Fortlaufende Aktivitaet mit Dauer |
| Roter Balken (crit) | Kritischer Meilenstein -- Quick Win |

### Sektionen erklaert

| Sektion | Inhalt |
|---|---|
| **Emails** | 6 automatisierte Emails der Post-Purchase-Sequenz |
| **Calls & Meetings** | Alle persoenlichen Touchpoints (Anrufe, Video-Calls, Reviews) |
| **Physisch** | Haptische Touchpoints (Karten, Welcome Package) |
| **Meilensteine** | Interne Arbeitspakete und Kunden-Erfolgsmomente |

### Wiederkehrende Aktivitaeten (ueber 90 Tage hinaus)

| Aktivitaet | Frequenz |
|---|---|
| Status-Email | Woechentlich |
| Check-in Call | Alle 2 Wochen |
| Strategie-Review | Monatlich |
| Handgeschriebene Karte | Alle 6 Wochen |
| Quarterly Business Review | Quartalsweise |
| NPS-Survey | Quartalsweise |
| Popsicle Moments | Laufend (ungeplant) |

---

## Verknuepfte Dokumente

- [email-templates/01-willkommens-email.md](../email-templates/01-willkommens-email.md) -- Email 1
- [email-templates/02-team-vorstellung.md](../email-templates/02-team-vorstellung.md) -- Email 2
- [email-templates/03-onboarding-checklist.md](../email-templates/03-onboarding-checklist.md) -- Email 3
- [email-templates/04-erste-ergebnisse.md](../email-templates/04-erste-ergebnisse.md) -- Email 4
- [email-templates/05-insights-feedback.md](../email-templates/05-insights-feedback.md) -- Email 5
- [email-templates/06-nps-review.md](../email-templates/06-nps-review.md) -- Email 6
- [vorlagen/kickoff-agenda.md](../vorlagen/kickoff-agenda.md) -- Kickoff-Meeting
