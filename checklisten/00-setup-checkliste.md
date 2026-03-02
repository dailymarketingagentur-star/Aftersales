# Phase 0: Setup-Checkliste

> Alle Systeme und Vorlagen, die VOR dem ersten Kunden eingerichtet sein muessen.
> Verantwortlich: Operations + Geschaeftsfuehrer

---

## 1. CRM & Automationen

- [ ] CRM auswaehlen und Account erstellen (Empfehlung: HubSpot)
- [ ] Kontakt-Felder definieren:
  - Firmenname, Ansprechpartner, Branche
  - Vertragsstart, Vertragswert, CLV-Schaetzung
  - Zugewiesener Account Manager
  - Kunden-Stufe (Bronze/Silber/Gold/Platin)
  - NPS-Score (letzter Wert + Datum)
  - Referral-Quelle
- [ ] Pipeline-Stufen einrichten:
  - Neukunde (Tag 0)
  - Onboarding (Tag 1-14)
  - Aktiv (ab Tag 14)
  - Review-Phase (Tag 90)
  - Verlaengerung (Monat 11)
  - Churn-Risiko
- [ ] Automatische Erinnerungen konfigurieren:
  - Handgeschriebene Karte alle 6 Wochen
  - 30/60/90-Tage Check-ins
  - Quartalsweise Business Reviews
  - Monat-11 Verlaengerungs-Trigger
- [ ] Email-Sequenzen anlegen (siehe `email-templates/`)

## 2. Projektmanagement

- [ ] PM-Tool auswaehlen (Empfehlung: ClickUp oder Asana)
- [ ] Kunden-Projekt-Template erstellen mit Standard-Tasks:
  - Onboarding-Phase (Tag 0-14)
  - Discovery & Setup (Tag 1-7)
  - Strategie & Kickoff (Tag 7-14)
  - Laufende Betreuung
- [ ] Standard-Kommunikations-Kanaele definieren
- [ ] Team-Rollen und Berechtigungen festlegen

## 3. Client Portal

- [ ] Portal-Tool einrichten (ManyRequests oder Moxo)
- [ ] Branding anpassen (Logo, Farben, Schriften)
- [ ] Standard-Bereiche erstellen:
  - Projektstatus / Dashboard
  - Dokumente & Downloads
  - Kommunikation / Nachrichten
  - Rechnungen & Vertraege
- [ ] Zugangsverwaltung testen

## 4. Email-Sequenzen

- [ ] Alle 6 Email-Templates erstellen (siehe `email-templates/`)
- [ ] Platzhalter-System testen:
  - `{{KUNDENNAME}}` -- Name des Kunden
  - `{{FIRMENNAME}}` -- Firmenname
  - `{{AGENTURNAME}}` -- Eigener Agenturname
  - `{{AM_NAME}}` -- Account Manager Name
  - `{{AM_EMAIL}}` -- Account Manager Email
  - `{{AM_TELEFON}}` -- Account Manager Telefon
  - `{{PROJEKT_ZIEL}}` -- Hauptziel des Projekts
- [ ] Automatische Versand-Trigger konfigurieren
- [ ] Test-Durchlauf mit internem Account

## 5. Welcome Package

- [ ] Lieferanten fuer physische Artikel identifizieren:
  - Hochwertige Versandboxen mit Branding
  - Seidenpapier in Markenfarben
  - Premium-Notizbuecher mit Logo
  - Hochwertige Kugelschreiber
  - Personalisierbare Tassen/Flaschen
  - Artisan-Kekse / Spezialitaetenkaffee
- [ ] Budget pro Package festlegen (0,5-1% des CLV)
- [ ] Lagerbestand fuer schnelle Lieferung sicherstellen
- [ ] Assembly-Prozess dokumentieren
- [ ] Versandprozess definieren (Lieferzeit max. 3 Tage)

> Detaillierte Spezifikation: [`02-welcome-package.md`](02-welcome-package.md)

## 6. Onboarding-Fragebogen

- [ ] Fragebogen erstellen (siehe `vorlagen/onboarding-fragebogen.md`)
- [ ] In Online-Tool uebertragen (Typeform, Google Forms, Content Snare)
- [ ] Asset-Upload-Bereich einrichten
- [ ] Automatische Erinnerungen bei fehlenden Antworten

## 7. Dashboard-Templates

- [ ] Reporting-Tool einrichten (AgencyAnalytics oder Looker Studio)
- [ ] Standard-Dashboard-Template erstellen:
  - Website-Traffic (Sessions, Nutzer, Bounce Rate)
  - Conversion-Metriken (Leads, Anfragen, Kaeufe)
  - SEO-Metriken (Rankings, Sichtbarkeit, Backlinks)
  - Social Media (Follower, Engagement, Reichweite)
  - Paid Ads (Klicks, CPC, ROAS, Conversions)
  - Action-Metriken (erledigte Tasks, gelieferte Inhalte)
- [ ] Automatischen Reporting-Versand konfigurieren (Dienstag 9:00 Uhr)
- [ ] Client-Zugang testen

## 8. NPS & Feedback

- [ ] NPS-Tool einrichten (SurveyMonkey oder AskNicely)
- [ ] NPS-Umfrage erstellen:
  - Hauptfrage: "Wie wahrscheinlich wuerdest du uns weiterempfehlen? (0-10)"
  - Folgefrage bei 0-6: "Was koennen wir verbessern?"
  - Folgefrage bei 7-8: "Was fehlt, um uns weiterzuempfehlen?"
  - Folgefrage bei 9-10: "Was gefaellt dir am meisten?"
- [ ] Automatische Testimonial-Anfrage bei Score 9-10 konfigurieren
- [ ] Alert bei Score 0-6 an Account Manager einrichten

## 9. Workflow-Automationen

- [ ] Zapier oder n8n einrichten
- [ ] Workflows erstellen:
  - **Neuer Kunde in CRM** --> Slack-Benachrichtigung an Team
  - **Neuer Kunde in CRM** --> PM-Projekt aus Template erstellen
  - **Neuer Kunde in CRM** --> Welcome-Email-Sequenz starten
  - **NPS Score 9-10** --> Testimonial-Anfrage senden (24-48h Delay)
  - **NPS Score 0-6** --> Alert an Account Manager + Geschaeftsfuehrer
  - **Vertragsende in 30 Tagen** --> Erinnerung an Account Manager
  - **Kein Kontakt seit 21 Tagen** --> Erinnerung an Account Manager
- [ ] Alle Workflows testen

## 10. Interne Dokumentation

- [ ] Standard Operating Procedures (SOPs) erstellen fuer:
  - Neukunden-Onboarding (Schritt-fuer-Schritt)
  - Discovery Call Durchfuehrung
  - Welcome Package Versand
  - Monatliches Reporting
  - Quarterly Business Review
  - Kuendigungs-/Exit-Prozess
  - Referral-Anfrage-Prozess
- [ ] Team-Training durchfuehren
- [ ] Feedback-Schleife fuer Prozessverbesserung einrichten

## 11. Video-Tool

- [ ] Loom oder Vidyard Account erstellen
- [ ] Video-Vorlage/Skript fuer personalisierte Willkommens-Videos vorbereiten
- [ ] Aufnahme-Setup testen (Webcam, Mikrofon, Hintergrund)
- [ ] Branding-Overlay einrichten (falls verfuegbar)

## 12. Branded Merchandise

- [ ] Branded Items fuer T-Shirt-Strategie bestellen:
  - T-Shirts (mehrere Groessen)
  - Hoodies (optional)
  - Weitere Branded Items
- [ ] Review-Tausch-Prozess definieren:
  - Kunde schreibt Review auf Google/Facebook
  - Screenshot als Nachweis
  - Branded Item versenden
- [ ] Lagerbestand planen

---

## Abnahme

| Bereich | Verantwortlich | Erledigt | Datum |
|---|---|---|---|
| CRM & Automationen | | [ ] | |
| Projektmanagement | | [ ] | |
| Client Portal | | [ ] | |
| Email-Sequenzen | | [ ] | |
| Welcome Package | | [ ] | |
| Onboarding-Fragebogen | | [ ] | |
| Dashboard-Templates | | [ ] | |
| NPS & Feedback | | [ ] | |
| Workflow-Automationen | | [ ] | |
| Interne Dokumentation | | [ ] | |
| Video-Tool | | [ ] | |
| Branded Merchandise | | [ ] | |

**Alle Bereiche abgenommen am:** _______________
**Durch:** _______________
