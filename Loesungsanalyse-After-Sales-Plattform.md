# After-Sales Plattform: Vollstaendige Loesungsanalyse

## Kontext

**Situation:** Marketing-Agentur mit 100+ Kunden. CRM (HubSpot), Confluence, Jira vorhanden. Dedizierte After-Sales-Person (Basis-Kenntnisse, kein Coding) soll eigenstaendig arbeiten.

**Kernprobleme:**
1. Upsell-Termine werden vergessen
2. Follow-ups fuer Ergebnis-Besprechungen finden nicht statt
3. E-Mails werden nicht versendet
4. KPIs (letzter Kontakt, Zahlungsmoral) sind unbekannt
5. Umfragen werden nicht versendet
6. Confluence wird nicht gepflegt (Adoption-Problem)

**Bestehendes Asset:** WordPress-Plugin "Client Operations Hub" (Paket 1) — 8 DB-Tabellen, 20 Task-Templates, Task-Engine, Reminders, API-Vault, REST API, HubSpot/ClickUp/Slack-Integration.

---

## KATEGORIE A: Kaufloesungen (SaaS)

---

### A1. Dedizierte Customer Success Plattformen

Diese Tools sind *exakt* fuer euren Use-Case gebaut: Kunden-Health-Monitoring, automatisierte Touchpoints, Churn-Prevention, Upsell-Tracking.

#### Gainsight CS
- **Preis:** ab ~2.500 USD/Monat (jaehrlich, Verhandlungssache)
- **Staerken:** Marktfuehrer. AI-basierte Churn-Prediction, Playbooks (automatisierte Aktionsketten), 360-Grad-Kundenansicht, NPS nativ, Health Scores, Journey Orchestrator, CRM-Sync (HubSpot nativ), Stakeholder-Mapping
- **Schwaechen:** Teuer, Enterprise-fokussiert, lange Implementierung (4-8 Wochen), steile Lernkurve
- **Fuer euch:** Overkill bei 100 Kunden, interessant ab 200+. Beste Loesung wenn Geld keine Rolle spielt

#### ChurnZero
- **Preis:** ab ~1.500 USD/Monat (je nach Kundenanzahl)
- **Staerken:** Real-time Usage-Alerts, Playbooks, In-App-Kommunikation, Segmentation, Health Scores, Renewals-Management, HubSpot-Integration, gutes Preis-Leistungs-Verhaeltnis vs. Gainsight
- **Schwaechen:** Primaer fuer SaaS/Tech-Unternehmen optimiert, weniger Agency-spezifisch
- **Fuer euch:** Gute Alternative zu Gainsight, wenn Budget da ist

#### Planhat
- **Preis:** ab 1.150 EUR/Monat (Starter), ab 2.350 EUR/Monat (Professional)
- **Staerken:** EU-basiert (DSGVO nativ), cleane moderne UI, Revenue-Tracking, Health Scores, Playbooks, HubSpot-Integration, Kundenportal, guter Support
- **Schwaechen:** Kleiner als Gainsight/ChurnZero, weniger AI-Features
- **Fuer euch:** Beste EU-Option. DSGVO ist hier kein Thema. Preis moderat

#### Totango
- **Preis:** Starter kostenlos (bis 100 Accounts!), Enterprise ab ~1.000 USD/Monat
- **Staerken:** Freemium fuer bis zu 100 Accounts, SuccessBlocs (vorgefertigte Playbooks), Segmentation, Health Scores, HubSpot-Integration
- **Schwaechen:** Freemium ist funktional eingeschraenkt, UI weniger modern als Planhat
- **Fuer euch:** Interessant wegen Freemium-Start — koenntet sofort anfangen und sehen ob es passt

#### Custify
- **Preis:** ab ~300 EUR/Monat
- **Staerken:** Guenstigster Einstieg, Health Scores, Playbooks, Lifecycle-Tracking, HubSpot-Integration
- **Schwaechen:** Kleinster Anbieter, weniger Features, Community kleiner
- **Fuer euch:** Budget-Option wenn ihr CS-Features wollt ohne Enterprise-Preise

| Tool | Preis/Monat | Health Scores | Playbooks | NPS | HubSpot | Churn AI | Kundenportal |
|------|-------------|:---:|:---:|:---:|:---:|:---:|:---:|
| Gainsight | ~2.500 USD | Ja | Ja | Ja | Ja | Ja | Ja |
| ChurnZero | ~1.500 USD | Ja | Ja | Ja | Ja | Ja | Ja |
| Planhat | ab 1.150 EUR | Ja | Ja | Ja | Ja | Begrenzt | Ja |
| Totango | 0-1.000 USD | Ja | Ja | Ja | Ja | Ja | Nein |
| Custify | ~300 EUR | Ja | Ja | Begrenzt | Ja | Nein | Nein |

**Vorteile aller CS-Plattformen:**
- Purpose-built fuer Customer Success / After-Sales
- Health Scores, Playbooks, Automations out-of-the-box
- After-Sales-Person kann eigenstaendig arbeiten
- Schnelle Implementierung (Tage bis wenige Wochen)
- Professionelle UI, Mobile-Zugang
- Skaliert problemlos auf 500+ Kunden

**Nachteile aller CS-Plattformen:**
- Laufende Kosten (300-2.500+ EUR/Monat)
- Vendor Lock-in
- Muss an euren spezifischen 11-Phasen-Prozess angepasst werden
- Bestehendes Plugin-Investment waere verloren
- Noch ein Tool im Stack

---

### A2. CRM-Erweiterung: HubSpot Service Hub

**Beschreibung:** Euer bestehendes HubSpot um Service Hub Professional erweitern.

- **Preis:** Service Hub Professional ab ~100 EUR/Seat/Monat, Enterprise ab ~130 EUR/Seat/Monat
- **Was ihr bekommt:**
  - Ticket-Pipelines fuer After-Sales-Tasks
  - Feedback-Umfragen (NPS, CSAT, CES) nativ
  - Kundenportal
  - Wissensdatenbank
  - Workflows fuer automatische E-Mail-Sequenzen
  - SLA-Tracking
  - Custom Reports und Dashboards
  - Playbooks (Sales/Service Hub Enterprise)

**Vorteile:**
- Bereits im Einsatz — kein neues Tool
- Alle Kundendaten an einem Ort
- After-Sales-Person arbeitet in gleicher Oberflaeche wie Vertrieb
- Native E-Mail-Versand mit Tracking (Opens, Clicks)
- Workflows koennen alles automatisieren (E-Mails, Tasks, Deals)
- Reports/Dashboards fuer KPIs eingebaut
- Mobile App vorhanden

**Nachteile:**
- Nicht spezialisiert fuer Customer Success (eher Support/Ticketing)
- Keine echten Health Scores (muss ueber Custom Properties + Berechnete Felder simuliert werden)
- Keine Playbooks im CS-Sinne (Workflows sind generisch)
- 11-Phasen-Prozess schwer als Pipeline abbildbar
- Kosten addieren sich (Sales Hub + Service Hub + Marketing Hub)
- Eingeschraenkte bedingte Logik (Tier-basiert, Phase-basiert)
- Upsell-Tracking existiert nur als Deal-Pipeline

---

### A3. Projektmanagement-Tools als After-Sales Hub

#### ClickUp
- **Preis:** Business ab 12 USD/User/Monat, Enterprise individuell
- **Staerken:** Flexibelste Views (Board, List, Timeline, Calendar, Gantt), starke Automations, Docs, Forms, Dashboards, Goals, Time Tracking, HubSpot-Integration
- **Schwaechen:** Kein CRM, kein Health Score, keine E-Mail-Engine, kein NPS

#### Monday.com
- **Preis:** Pro ab 16 EUR/Seat/Monat, Enterprise individuell
- **Staerken:** Intuitive UI, gute Automations, Dashboards, Integrationen, CRM-Addon verfuegbar
- **Schwaechen:** Wird schnell teuer bei vielen Users, kein CS-spezifisches Feature-Set

#### Asana
- **Preis:** Business ab 25 USD/User/Monat
- **Staerken:** Portfolios, Goals, Rules (Automations), Timeline, Reporting
- **Schwaechen:** Weniger flexibel als ClickUp, keine Dashboards auf Monday-Niveau

**Vorteile aller PM-Tools:**
- Moderne UI, einfach zu bedienen
- Automations fuer wiederkehrende Tasks
- Templates fuer Onboarding-Prozesse
- Guenstig (12-25 EUR/User/Monat)
- Schnelle Einrichtung

**Nachteile aller PM-Tools:**
- Kein CRM-Charakter — Kundenansicht muss gebaut werden
- Keine E-Mail-Engine (nur Notifications)
- Kein Health Score, kein NPS, keine Churn-Prediction
- Daten-Silos (CRM + PM-Tool + Jira)
- Adoption-Risiko (noch ein Tool)
- Begrenzte KPI-Moeglichkeiten

---

### A4. Spezialisierte Einzel-Tools (Ergaenzend)

Diese Tools loesen *einzelne* Probleme und koennen mit jeder Hauptloesung kombiniert werden:

| Problem | Tool | Preis | Funktion |
|---------|------|-------|----------|
| NPS/Umfragen | **AskNicely** | ab 200 USD/Mo | NPS-Automation, HubSpot-Sync |
| NPS/Umfragen | **Delighted** | ab 224 USD/Mo | NPS/CSAT/CES, Automations |
| NPS/Umfragen | **SurveyMonkey** | ab 30 EUR/Mo | Flexible Umfragen |
| NPS/Umfragen | **Typeform** | ab 25 EUR/Mo | Schoene Formulare, Integrationen |
| E-Mail-Sequenzen | **ActiveCampaign** | ab 29 USD/Mo | Automations, Segmentation, CRM-lite |
| E-Mail-Sequenzen | **Customer.io** | ab 100 USD/Mo | Event-basierte E-Mails, Segmentation |
| E-Mail-Sequenzen | **Mailchimp** | ab 13 EUR/Mo | E-Mail-Marketing, basische Automations |
| Termin-Booking | **Calendly** | ab 10 EUR/Seat/Mo | Automatische Terminplanung |
| Reporting/KPIs | **Looker Studio** | kostenlos | Dashboards aus jeder Datenquelle |
| Reporting/KPIs | **Databox** | ab 72 USD/Mo | KPI-Dashboards, Multi-Source |
| Reporting/KPIs | **AgencyAnalytics** | ab 79 USD/Mo | Agency-spezifische Reports |
| Workflow-Automation | **n8n** | self-hosted kostenlos | Beliebige Integrationen |
| Workflow-Automation | **Make (Integromat)** | ab 9 EUR/Mo | Visuelle Automations |
| Workflow-Automation | **Zapier** | ab 20 USD/Mo | Einfachste Automations |
| Kunden-Kommunikation | **Intercom** | ab 74 USD/Mo | In-App Messaging, Chatbot |
| Kundenportal | **ManyRequests** | ab 99 USD/Mo | Agency Client Portal |
| Kundenportal | **Moxo** | individuell | Enterprise Client Portal |

---

## KATEGORIE B: Eigenentwicklung (Build)

---

### B1. WordPress Plugin (Client Operations Hub) zu Paket 2+3 ausbauen

**Beschreibung:** Bestehendes Plugin fertigstellen.

**Geschaetzter Aufwand:** 80-120 Stunden Entwicklung

**Was noch fehlt (Paket 2+3):**
- Dashboard UI (Visualisierung der vorhandenen Daten)
- Client Detail Pages (Activity Timeline, Task-Uebersicht)
- E-Mail-Template-Engine (Personalisierung + automatischer Versand)
- Health Score Berechnung (7 Kategorien, automatisch)
- Churn-Warning System (10 Warnsignale mit Eskalation)
- Upsell-Opportunity Tracker
- Referral Pipeline
- NPS-Integration
- Bi-direktionale Syncs (HubSpot, ClickUp)
- KPI-Dashboard (Cross-Client Aggregation)
- Compliance Reports

**Vorteile:**
- Fundament existiert (8 Tabellen, Task-Engine, API, Integrations)
- Massgeschneidert fuer euren 11-Phasen-Prozess
- Keine laufenden Lizenzkosten
- Volle Kontrolle ueber Features und Daten
- DSGVO — Daten auf eigenem Server

**Nachteile:**
- WordPress-Admin UI ist nicht modern genug fuer 100+ Kunden-Management
- Skalierung bei 100+ Kunden problematisch (WordPress nicht fuer CRM-Workloads gebaut)
- After-Sales-Person muss WordPress-Admin navigieren
- Wartung, Updates, Security liegen bei euch
- Kein Mobile-App
- Single Point of Failure (Entwickler-Abhaengigkeit)

**Bewertung bei 100+ Kunden: BEDINGT GEEIGNET** — Fundament ist wertvoll, aber WordPress ist als Frontend bei dieser Kundenzahl suboptimal.

---

### B2. Custom Web App (Django, Next.js, oder anderes Framework)

**Beschreibung:** Eigenstaendige Web-Applikation als After-Sales-Plattform.

**Geschaetzter Aufwand:** 200-400 Stunden (je nach Umfang)

**Tech-Stack Optionen:**

| Stack | Vorteile | Nachteile |
|-------|----------|-----------|
| **Django + HTMX** | Python-Oekosystem, schnelle Entwicklung, Admin gratis, ORM stark | Weniger moderne UI ohne JS-Framework |
| **Django + React** | Bestes aus beiden Welten, Django REST + React Frontend | Zwei Codebases zu warten |
| **Next.js + Supabase** | Modernste UI, Echtzeit-Features, schnelles Deployment | Kein Python, Supabase-Abhaengigkeit |
| **Laravel + Livewire** | PHP (wie WordPress), schnelle Entwicklung, elegantes Framework | PHP-Oekosystem kleiner als Python |

**Vorteile:**
- Volle Kontrolle ueber alles
- Skaliert beliebig (100, 500, 1000+ Kunden)
- Moderne, professionelle UI
- Mobile-first / PWA moeglich
- API-first — alle Integrationen moeglich
- Datenmodell aus Plugin kann uebernommen werden
- Keine Vendor-Abhaengigkeit

**Nachteile:**
- Hoher Initialaufwand (200-400h)
- Alles muss selbst gebaut werden (Auth, Dashboard, E-Mail, etc.)
- Laufende Wartung (Server, Updates, Bugfixes)
- Entwickler-Abhaengigkeit
- Hosting-Kosten (gering, aber vorhanden)
- Keine Community/Support
- Time-to-Market: Monate statt Wochen

**Bewertung bei 100+ Kunden: GUT GEEIGNET** — wenn langfristig gedacht und Budget/Zeit vorhanden.

---

### B3. Plugin-Backend + Standalone Dashboard (Hybrid)

**Beschreibung:** WordPress-Plugin als Datenschicht/API behalten, modernes Frontend davor.

**Geschaetzter Aufwand:** 100-160 Stunden (Plugin Paket 2 + Dashboard)

**Vorteile:**
- Bestehendes Investment wird genutzt
- REST API (15 Endpoints) existiert bereits
- Modernes Frontend moeglich
- Schrittweise umsetzbar

**Nachteile:**
- Zwei Systeme zu warten
- WordPress als Backend fuer 100+ Kunden fragwuerdig
- CORS/Auth-Komplexitaet
- Irgendwann will man komplett migrieren

**Bewertung bei 100+ Kunden: UEBERGANGSLOESUNG** — kann funktionieren, aber langfristig ist ein richtiges Backend besser.

---

## KATEGORIE B: Eigenentwicklung (Build)

---

## KATEGORIE C: Hybrid-Loesungen (Buy + Build/Configure)

---

### C1. HubSpot (Zentrale) + n8n (Automation) + Einzel-Tools

**Beschreibung:** HubSpot als Single Source of Truth, n8n automatisiert die Luecken, spezialisierte Tools fuer NPS/E-Mail.

**Kosten:**
- HubSpot Service Hub Professional: ~100 EUR/Seat/Monat
- n8n: kostenlos (self-hosted) oder 20 EUR/Monat (Cloud)
- Typeform/SurveyMonkey: ~30 EUR/Monat
- Calendly: ~10 EUR/Seat/Monat
- Looker Studio: kostenlos
- **Gesamt: ~160-200 EUR/Monat**

**Was n8n automatisiert:**
- E-Mail-Sequenzen nach Zeitplan (personalisiert aus HubSpot-Daten)
- Task-Erstellung in Jira/ClickUp fuer Follow-ups
- NPS-Umfragen automatisch nach 30/60/90 Tagen
- Health-Score-Berechnung aus HubSpot-Aktivitaeten
- Upsell-Reminder basierend auf Vertragsdaten
- Slack-Alerts bei Churn-Warnsignalen
- KPI-Aggregation fuer Looker Studio Dashboard

**Vorteile:**
- After-Sales-Person arbeitet hauptsaechlich in HubSpot (bekannt)
- Alle Probleme automatisch geloest (E-Mails, Follow-ups, Umfragen, KPIs)
- Moderate Kosten
- Schrittweise umsetzbar (ein Workflow nach dem anderen)
- DSGVO-konform (n8n self-hosted)

**Nachteile:**
- Kein dediziertes After-Sales-Dashboard (muss in HubSpot/Looker Studio gebaut werden)
- Viele bewegliche Teile (HubSpot + n8n + Typeform + Looker Studio)
- n8n-Workflows brauchen technische Wartung
- Health Scores in HubSpot sind "gehackt" (Custom Properties)
- Kein Playbook-Konzept

---

### C2. ClickUp (Operativ) + HubSpot (CRM) + ActiveCampaign (E-Mail)

**Beschreibung:** ClickUp als operatives Zentrum fuer die After-Sales-Person, HubSpot fuer Kundendaten, ActiveCampaign fuer E-Mail-Automationen.

**Kosten:**
- ClickUp Business: ~12 USD/User/Monat
- HubSpot (bestehend): bereits vorhanden
- ActiveCampaign: ab 29 USD/Monat
- Zapier/Make fuer Sync: ab 20 USD/Monat
- **Gesamt: ~80-100 EUR/Monat**

**Vorteile:**
- ClickUp hat beste UI fuer operatives Task-Management
- ActiveCampaign hat starke E-Mail-Automations
- Guenstig
- After-Sales-Person arbeitet primaer in ClickUp (einfach)

**Nachteile:**
- Drei Tools die synchron gehalten werden muessen
- Kein Health Score ohne Custom-Aufbau
- Kein NPS nativ (braucht weiteres Tool)
- Daten-Silos

---

### C3. Totango (Free) + HubSpot + Automations

**Beschreibung:** Totango Freemium (bis 100 Accounts) als CS-Plattform nutzen, HubSpot als CRM behalten.

**Kosten:**
- Totango Starter: kostenlos (bis 100 Accounts)
- HubSpot: bereits vorhanden
- **Gesamt: 0 EUR/Monat (bei <100 aktiven Kunden in Totango)**

**Vorteile:**
- Kostenloser Einstieg in eine echte CS-Plattform
- Health Scores, Segmentation, SuccessBlocs eingebaut
- HubSpot-Integration vorhanden
- Professionelle UI
- Sofort einsatzbereit

**Nachteile:**
- Freemium ist funktional eingeschraenkt (keine Playbooks, limitierte Automations)
- Bei >100 Accounts wird es kostenpflichtig (~1.000 USD/Monat)
- US-Anbieter (DSGVO-Bedenken)
- Weniger modern als Planhat
- Kein E-Mail-Versand (braucht Integration)

---

### C4. Planhat + HubSpot (Premium-Variante)

**Beschreibung:** Planhat als dedizierte CS-Plattform, HubSpot als CRM.

**Kosten:**
- Planhat Starter: ab 1.150 EUR/Monat
- HubSpot: bereits vorhanden
- **Gesamt: ab 1.150 EUR/Monat**

**Vorteile:**
- EU-basiert, DSGVO-nativ
- Beste UI unter den CS-Plattformen
- Health Scores, Playbooks, Revenue Tracking, Kundenportal
- HubSpot-Integration nativ
- After-Sales-Person hat perfektes Werkzeug
- Skaliert problemlos

**Nachteile:**
- 1.150+ EUR/Monat
- Noch ein Tool im Stack
- Implementierungsaufwand (2-4 Wochen)

---

## KATEGORIE D: Jira/Confluence optimieren (Minimaler Eingriff)

---

### D1. Jira Automation Rules + Confluence Templates

**Beschreibung:** Bestehende Tools besser nutzen statt neue einfuehren.

**Kosten:** Keine zusaetzlichen (Jira Cloud enthaelt Automation)

**Was moeglich ist:**
- Jira Automation: "Erstelle Issue 30 Tage nach Onboarding-Abschluss"
- Jira Automation: "Sende Reminder wenn Issue X Tage ueberfaellig"
- Jira Custom Fields fuer Health Score, Tier, Letzter Kontakt
- Confluence Templates fuer Kunden-Steckbriefe
- Jira Dashboard mit Filtern fuer After-Sales

**Vorteile:**
- Keine neuen Tools
- Keine Kosten
- Sofort umsetzbar

**Nachteile:**
- Loest das Grundproblem NICHT — wenn Mitarbeiter Confluence nicht pflegen, pflegen sie auch Jira-Fields nicht
- Jira ist kein CRM — Kundenansicht fehlt
- Keine E-Mail-Engine
- Keine NPS/Umfragen
- Keine Health Scores (nur manuelle Custom Fields)
- Keine Playbooks
- Schlechte UX fuer After-Sales-Aufgaben

**Bewertung: NICHT EMPFOHLEN** als alleinige Loesung bei 100+ Kunden.

---

## Gesamtvergleich (100+ Kunden, After-Sales-Person mit Basis-Kenntnissen)

| # | Loesung | Monatl. Kosten | Setup-Zeit | Skalierbar | Eigenstaendig bedienbar | Alle 6 Probleme geloest | Bestehendes Investment |
|---|---------|---------------|-----------|:----------:|:----------------------:|:----------------------:|:---------------------:|
| A1a | Gainsight | 2.500+ USD | 4-8 Wo | Ja | Ja | Ja | Verloren |
| A1b | ChurnZero | 1.500+ USD | 2-4 Wo | Ja | Ja | Ja | Verloren |
| A1c | Planhat | 1.150+ EUR | 2-4 Wo | Ja | Ja | Ja | Verloren |
| A1d | Totango Free | 0 EUR | 1-2 Wo | Begrenzt | Ja | Teilweise | Verloren |
| A1e | Custify | ~300 EUR | 1-2 Wo | Ja | Ja | Groesstenteils | Verloren |
| A2 | HubSpot Service | ~100 EUR/Seat | 1-2 Wo | Ja | Ja | Teilweise | Teilw. genutzt |
| A3 | ClickUp/Monday | 12-25 EUR/User | 1 Wo | Mittel | Ja | Teilweise | Teilw. genutzt |
| B1 | WP Plugin Ausbau | 0 EUR | 2-3 Mo | Begrenzt | Mittel | Ja | Voll genutzt |
| B2 | Custom Web App | 0 EUR* | 3-6 Mo | Ja | Ja | Ja | Teilw. genutzt |
| B3 | Plugin + Dashboard | 0 EUR | 2-3 Mo | Begrenzt | Ja | Ja | Voll genutzt |
| C1 | HubSpot + n8n | ~160-200 EUR | 2-4 Wo | Ja | Mittel | Ja | Teilw. genutzt |
| C2 | ClickUp + AC | ~80-100 EUR | 1-2 Wo | Mittel | Ja | Groesstenteils | Teilw. genutzt |
| C3 | Totango + HubSpot | 0 EUR | 1-2 Wo | Begrenzt | Ja | Teilweise | Verloren |
| C4 | Planhat + HubSpot | 1.150+ EUR | 2-4 Wo | Ja | Ja | Ja | Verloren |
| D1 | Jira optimieren | 0 EUR | 1 Wo | Nein | Nein | Nein | - |

*Custom Web App: Einmalige Entwicklungskosten (200-400h), minimale Server-Kosten danach

---

## Bewertung und Empfehlungsszenarien

### Szenario 1: "Schnell starten, Budget vorhanden"
**Empfehlung: Planhat (C4) oder Custify (A1e)**
- Sofort einsatzbereit
- Alle 6 Probleme geloest
- After-Sales-Person kann eigenstaendig arbeiten
- Professionelle UI

### Szenario 2: "Schnell starten, minimale Kosten"
**Empfehlung: Totango Free + HubSpot (C3)**
- 0 EUR bis 100 Accounts
- Echte CS-Plattform
- Sofort testen ob CS-Software der richtige Weg ist
- Bei Wachstum auf Paid upgraden oder wechseln

### Szenario 3: "Langfristig eigene Plattform, Zeit vorhanden"
**Empfehlung: Custom Web App (B2) — z.B. mit Django**
- Volle Kontrolle
- Keine laufenden Lizenzkosten
- Skaliert beliebig
- Datenmodelle aus Plugin uebertragbar
- Kurzfristig n8n-Automationen als Ueberbrueckung (C1)

### Szenario 4: "Bestehende Tools maximieren"
**Empfehlung: HubSpot Service Hub + n8n (C1)**
- Kein neues Tool fuer Mitarbeiter
- Automationen loesen die akuten Probleme
- Moderate Kosten
- Schrittweise ausbaubar

### Szenario 5: "Bestehendes Plugin-Investment schuetzen"
**Empfehlung: Plugin Backend + modernes Dashboard (B3), mittelfristig Migration zu Django (B2)**
- REST API wird weiterverwendet
- Datenmodell bleibt
- UI wird modern
- Spaeter vollstaendige Migration

---

## Naechste Schritte

Dies ist eine Entscheidungsgrundlage. Sobald die Richtung klar ist (Buy vs. Build vs. Hybrid), erstelle ich einen konkreten Projektplan fuer die gewaehlte Loesung.
