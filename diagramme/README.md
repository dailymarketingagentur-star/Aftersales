# Diagramme -- Visuelle Uebersicht

> Mermaid-Visualisierungen der Kernprozesse, Kundenreise und Steuerungsinstrumente des After-Sales-Systems.

---

## Uebersicht

| # | Diagramm | Mermaid-Typ | Beschreibung |
|---|---|---|---|
| 01 | [Gesamtprozess-Flowchart](01-gesamtprozess-flowchart.md) | `flowchart LR` | Alle 11 Phasen als Flussdiagramm mit Verantwortlichkeiten und Feedback-Loop |
| 02 | [Customer Journey Map](02-customer-journey-map.md) | `journey` | Emotionskurve der ersten 90 Tage mit ~25 Touchpoints |
| 03 | [Email-Sequenz-Timeline](03-email-sequenz-timeline.md) | `gantt` | 90-Tage Gantt-Chart aller Kommunikations-Touchpoints |
| 04 | [Churn-Warning Entscheidungsbaum](04-churn-warning-entscheidungsbaum.md) | `flowchart TD` | 10 Warnsignale mit Massnahmen, Eskalation und Win-Back |
| 05 | [Tier-Progression](05-tier-progression.md) | `stateDiagram-v2` + `flowchart LR` | Bronze-bis-Platin Stufensystem mit Kriterien und Vorteilen |
| 06 | [Health Scorecard Dashboard](06-health-scorecard-dashboard.md) | `mindmap` + `flowchart LR` | 7 Metriken und 5 Score-Zonen visuell dargestellt |

---

## Verwendung

Die Diagramme nutzen [Mermaid](https://mermaid.js.org/) Syntax und koennen gerendert werden in:

- **VS Code** mit der Erweiterung "Markdown Preview Mermaid Support"
- **GitHub** (native Unterstuetzung in `.md`-Dateien)
- **Online** unter [mermaid.live](https://mermaid.live/)

---

## Quelldokumente

| Diagramm | Primaere Quelle |
|---|---|
| 01, 02, 03 | [After-Sales-Prozess.md](../After-Sales-Prozess.md) |
| 04, 05, 06 | [vorlagen/client-health-scorecard.md](../vorlagen/client-health-scorecard.md) |
