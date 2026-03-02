# Churn-Warning Entscheidungsbaum

> 10 Warnsignale mit Sofort-Massnahmen, Eskalationspfaden und Win-Back-Optionen.
> Basierend auf: [vorlagen/client-health-scorecard.md](../vorlagen/client-health-scorecard.md)

---

## Diagramm 1: Warnsignale und Sofort-Massnahmen

```mermaid
flowchart TD

    START(["Warnsignal erkannt"])

    subgraph KOM["Kommunikation"]
        W1["Antwortet\nlangsamer"]
        W2["Verpasst Calls /\nverschiebt wiederholt"]
        W8["Feedback wird\nkritischer oder\nbleibt aus"]
    end

    subgraph ENG["Engagement"]
        W3["Dashboard-/Portal-\nNutzung sinkt"]
        W10["Weniger\nFreigabe-Anfragen"]
    end

    subgraph BIZ["Business"]
        W4["Fragt nach\nKuendigungsfristen"]
        W5["Neuer Entscheider /\nAnsprechpartner"]
        W6["Erwaehnt\nBudgetkuerzungen"]
        W9["Zahlungen\nverzoegern sich"]
    end

    subgraph WETTB["Wettbewerb"]
        W7["Wettbewerber werden\nerwaehnt / verglichen"]
    end

    START --> KOM
    START --> ENG
    START --> BIZ
    START --> WETTB

    %% Sofort-Massnahmen
    W1 --> A1["Persoenlicher Anruf\n(nicht Email!)"]
    W2 --> A2["Flexibleren Termin\n+ Agenda vorab"]
    W8 --> A8["Proaktiv nachfragen\n+ Verbesserung anbieten"]
    W3 --> A3["Kurze Video-\nEinweisung senden"]
    W10 --> A10["Check-in: Laeuft\nalles wie gewuenscht?"]
    W4 --> A4["Geschaeftsfuehrer\nsofort einbeziehen"]
    W5 --> A5["Kennenlern-Call\nvereinbaren"]
    W6 --> A6["Flexibles Modell\nanbieten"]
    W9 --> A9["Freundliche\nErinnerung senden"]
    W7 --> A7["USPs hervorheben\nErgebnisse zeigen"]

    %% 1-Woche-Follow-Up
    A1 --> F1["Vor-Ort-Meeting\nanbieten"]
    A2 --> F2["Wert der Calls\nverdeutlichen"]
    A3 --> F3["Dashboard\nvereinfachen"]
    A4 --> F4["Verbesserungsplan\npraesentieren"]
    A5 --> F5["Erfolge neu\npraesentieren"]
    A6 --> F6["Downgrade statt\nKuendigung"]
    A7 --> F7["Exklusives\nAngebot erstellen"]

    %% Eskalation
    F4 --> ESC

    ESC{{"Keine Besserung\nnach 2 Wochen?"}}
    F1 --> ESC
    F2 --> ESC
    F3 --> ESC
    F5 --> ESC
    F6 --> ESC
    F7 --> ESC

    ESC -->|Ja| EXIT["Exit-Prevention\nProtokoll aktivieren"]

    classDef warning fill:#f39c12,stroke:#d68910,color:#333
    classDef action fill:#27ae60,stroke:#1e8449,color:#fff
    classDef followup fill:#3498db,stroke:#2471a3,color:#fff
    classDef escalation fill:#e74c3c,stroke:#c0392b,color:#fff

    class W1,W2,W3,W4,W5,W6,W7,W8,W9,W10 warning
    class A1,A2,A3,A4,A5,A6,A7,A8,A9,A10 action
    class F1,F2,F3,F4,F5,F6,F7 followup
    class ESC,EXIT escalation
```

---

## Diagramm 2: Exit-Prevention und Win-Back

```mermaid
flowchart TD

    EXIT["Exit-Prevention\nProtokoll aktiviert"]

    EXIT --> INT["Exit-Interview\n(Video, 30 Min)"]

    INT --> Q1{"Hauptgrund\nidentifiziert?"}

    Q1 -->|Ergebnisse| OA["Option A:\nVerbesserungsplan\nmit konkreten Massnahmen"]
    Q1 -->|Budget| OB["Option B:\nDowngrade auf\nkleineres Paket"]
    Q1 -->|Timing| OC["Option C:\nPause statt Kuendigung\n(1-3 Monate)"]
    Q1 -->|Endgueltig| FINAL["Professionell abschliessen\nTuer offen lassen"]

    OA --> CHECK{{"Kunde bleibt?"}}
    OB --> CHECK
    OC --> CHECK

    CHECK -->|Ja| RETAIN["Retention erfolgreich\nHealth Score neu bewerten"]
    CHECK -->|Nein| FINAL

    FINAL --> WB3["Win-Back Kontakt\nnach 3 Monaten"]
    WB3 --> WB6["Win-Back Kontakt\nnach 6 Monaten"]
    WB6 --> ARCHIVE["Kunde archivieren\nLearnings dokumentieren"]

    classDef process fill:#3498db,stroke:#2471a3,color:#fff
    classDef decision fill:#f39c12,stroke:#d68910,color:#333
    classDef option fill:#27ae60,stroke:#1e8449,color:#fff
    classDef winback fill:#9b59b6,stroke:#7d3c98,color:#fff
    classDef final fill:#e74c3c,stroke:#c0392b,color:#fff

    class EXIT,INT process
    class Q1,CHECK decision
    class OA,OB,OC option
    class RETAIN option
    class WB3,WB6 winback
    class FINAL,ARCHIVE final
```

---

## Legende

### Farbkodierung Diagramm 1

| Farbe | Bedeutung |
|---|---|
| Orange | Warnsignal (10 Frueh-Indikatoren) |
| Gruen | Sofort-Massnahme (innerhalb 24h) |
| Blau | Follow-Up (innerhalb 1 Woche) |
| Rot | Eskalation (Exit-Prevention) |

### Farbkodierung Diagramm 2

| Farbe | Bedeutung |
|---|---|
| Blau | Prozess-Schritte |
| Orange | Entscheidungs-Punkte |
| Gruen | Optionen / Retention |
| Lila | Win-Back-Kontakte |
| Rot | Endgueltige Schritte |

### Warnsignal-Kategorien

| Kategorie | Signale | Schweregrad |
|---|---|---|
| **Kommunikation** | Langsame Antworten, verpasste Calls, fehlendes Feedback | Mittel-Hoch |
| **Engagement** | Sinkende Dashboard-Nutzung, weniger Freigaben | Mittel |
| **Business** | Kuendigungsfragen, neuer Entscheider, Budgetkuerzung, Zahlungsverzug | Hoch-Kritisch |
| **Wettbewerb** | Vergleiche mit Wettbewerbern | Hoch |

---

## Verknuepfte Dokumente

- [vorlagen/client-health-scorecard.md](../vorlagen/client-health-scorecard.md) -- Warnsignale-Checkliste und Exit-Prevention Protokoll
- [diagramme/06-health-scorecard-dashboard.md](06-health-scorecard-dashboard.md) -- Score-Zonen (ab wann wird eskaliert)
- [After-Sales-Prozess.md](../After-Sales-Prozess.md) -- Phase 11: Retention & Anti-Churn
