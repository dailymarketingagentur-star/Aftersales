# Health Scorecard Dashboard

> 7 Bewertungskategorien und Score-Zonen visuell dargestellt.
> Basierend auf: [vorlagen/client-health-scorecard.md](../vorlagen/client-health-scorecard.md)

---

## Diagramm 1: Die 7 Metriken

```mermaid
mindmap
  root((Health\nScore\n7-35 Pkt))
    Ergebnis-Zufriedenheit
      KPIs erreicht?
      ROI positiv?
      Erwartungen erfuellt?
    Kommunikation
      Antwortet zeitnah?
      Nimmt an Calls teil?
      Proaktiver Kontakt?
    Engagement
      Dashboard-Nutzung
      Portal-Nutzung
      Gibt Feedback
    Beziehung
      Zwischenmenschlich
      Vertrauen vorhanden
      Offener Austausch
    Zahlungsverhalten
      Puenktliche Zahlung
      Keine Rueckfragen
      Stabile Zahlungen
    Wachstumspotenzial
      Upsell moeglich
      Cross-Sell moeglich
      Budget vorhanden
    Referral-Bereitschaft
      Wuerde empfehlen
      Hat bereits empfohlen
      NPS 9-10
```

---

## Diagramm 2: Score-Zonen und Aktionen

```mermaid
flowchart LR

    subgraph SCORING["Score-Berechnung"]
        S["7 Kategorien\nx Skala 1-5\n= max. 35 Punkte"]
    end

    S --> E["30-35\nExzellent"]
    S --> G["24-29\nGut"]
    S --> N["18-23\nNeutral"]
    S --> R["12-17\nRisiko"]
    S --> K["7-11\nKritisch"]

    E --> EA["Testimonial anfragen\nReferral-Gespraech fuehren"]
    G --> GA["Wow-Moment planen\nUpsell-Chance pruefen"]
    N --> NA["Proaktiv Feedback einholen\nVerbesserungen identifizieren"]
    R --> RA["Sofort Massnahmen-Plan\nGF einbeziehen"]
    K --> KA["Rettungs-Meeting 48h\nExit-Prevention aktivieren"]

    classDef exzellent fill:#27ae60,stroke:#1e8449,color:#fff
    classDef gut fill:#85c1e9,stroke:#2980b9,color:#333
    classDef neutral fill:#f9e79f,stroke:#f1c40f,color:#333
    classDef risiko fill:#f0b27a,stroke:#e67e22,color:#333
    classDef kritisch fill:#e74c3c,stroke:#c0392b,color:#fff
    classDef aktion fill:#ecf0f1,stroke:#bdc3c7,color:#333
    classDef basis fill:#d5d8dc,stroke:#95a5a6,color:#333

    class S basis
    class E exzellent
    class G gut
    class N neutral
    class R risiko
    class K kritisch
    class EA,GA,NA,RA,KA aktion
```

---

## Legende

### Score-Skala pro Kategorie

| Score | Bedeutung |
|---|---|
| **1** | Kritisch -- sofort handeln |
| **2** | Schlecht -- Verbesserungsplan noetig |
| **3** | Neutral -- beobachten |
| **4** | Gut -- halten |
| **5** | Exzellent -- Testimonial/Referral-Chance |

### Score-Zonen Farbkodierung

| Zone | Score | Farbe | Aktion |
|---|---|---|---|
| Exzellent | 30-35 | Gruen | Testimonial + Referral |
| Gut | 24-29 | Blau | Wow-Moment + Upsell |
| Neutral | 18-23 | Gelb | Feedback + Verbesserung |
| Risiko | 12-17 | Orange | Massnahmen-Plan + GF |
| Kritisch | 7-11 | Rot | Rettungs-Meeting 48h |

### Bewertungsfrequenz

- Monatliche Aktualisierung durch Account Manager
- Quartalsweiser interner Portfolio-Review aller Kunden
- Sofortige Neubewertung bei Warnsignalen

---

## Verknuepfte Dokumente

- [vorlagen/client-health-scorecard.md](../vorlagen/client-health-scorecard.md) -- Vollstaendige Scorecard-Vorlage
- [diagramme/04-churn-warning-entscheidungsbaum.md](04-churn-warning-entscheidungsbaum.md) -- Was tun bei Risiko/Kritisch
- [diagramme/05-tier-progression.md](05-tier-progression.md) -- Stufen-System fuer Exzellent-Kunden
