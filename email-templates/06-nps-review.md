# Email 6: NPS-Survey + Review-Anfrage

> **Versand:** Tag 90
> **Absender:** Account Manager (oder Customer Success)
> **Ziel:** Zufriedenheit messen, Social Proof sammeln, Testimonials generieren

---

## Platzhalter

| Variable | Beschreibung |
|---|---|
| `{{KUNDENNAME}}` | Vorname des Kunden |
| `{{FIRMENNAME}}` | Firmenname des Kunden |
| `{{AGENTURNAME}}` | Name der Agentur |
| `{{AM_NAME}}` | Name des Account Managers |
| `{{NPS_SURVEY_LINK}}` | Link zur NPS-Umfrage |
| `{{ERGEBNIS_HIGHLIGHT}}` | Bestes Ergebnis der letzten 90 Tage |

---

## Betreff

```
Deine Meinung zaehlt -- Kurze Umfrage (2 Min)
```

**Alternative Betreffs:**
- 90 Tage zusammen -- wie war's, {{KUNDENNAME}}?
- {{KUNDENNAME}}, eine kurze Frage an dich

---

## Email-Text

---

Hallo {{KUNDENNAME}},

es ist kaum zu glauben, aber wir arbeiten jetzt seit 90 Tagen zusammen! In dieser Zeit haben wir einiges erreicht -- zum Beispiel {{ERGEBNIS_HIGHLIGHT}}.

**Deine Meinung ist uns wichtig.**

Wir wollen sicherstellen, dass wir nicht nur gute Arbeit leisten, sondern dass du und dein Team wirklich zufrieden seid. Deshalb eine kurze Bitte:

**Wuerdest du dir 2 Minuten nehmen, um uns Feedback zu geben?**

[Zur Umfrage (2 Minuten)]({{NPS_SURVEY_LINK}})

Die Umfrage besteht aus nur 2 Fragen:
1. Wie wahrscheinlich wuerdest du uns weiterempfehlen? (0-10)
2. Eine offene Frage zu deinem Feedback

Deine ehrliche Rueckmeldung hilft uns, noch besser zu werden -- fuer dich und fuer zukuenftige Kunden.

Vielen Dank fuer dein Vertrauen und die tolle Zusammenarbeit!

Herzliche Gruesse,
{{AM_NAME}}

---

## Follow-up Emails (automatisiert basierend auf NPS-Score)

### Bei NPS 9-10: Testimonial-Anfrage (24-48h nach NPS)

**Betreff:** Danke fuer dein tolles Feedback! Eine kleine Bitte...

---

Hallo {{KUNDENNAME}},

vielen Dank fuer dein grossartiges Feedback -- das bedeutet uns wirklich viel und motiviert das ganze Team!

Darf ich dich um einen kleinen Gefallen bitten? Wir wuerden deine Erfahrung gerne mit anderen Unternehmen teilen. Das hilft uns enorm und dauert nur wenige Minuten.

**Du hast drei Optionen:**

**Option 1: Wir schreiben fuer dich** (einfachste Option)
Wir schreiben ein kurzes Testimonial basierend auf unseren Ergebnissen. Du musst nur pruefen und freigeben.
--> Antworte mit "Schreibt fuer mich" und wir senden dir einen Entwurf.

**Option 2: Google-Review** (2 Minuten)
Eine kurze Bewertung auf Google hilft anderen, uns zu finden:
[Google Review schreiben]({{GOOGLE_REVIEW_LINK}})
Als Dankeschoen schicken wir dir ein {{AGENTURNAME}}-Ueberraschungspaket!

**Option 3: Video-Testimonial** (15 Minuten)
Ein kurzer Video-Call, den wir professionell aufbereiten. Am ueberzeugendsten fuer andere Unternehmen.
--> Antworte mit "Video klingt gut" und wir vereinbaren einen Termin.

Was passt dir am besten?

Herzliche Gruesse,
{{AM_NAME}}

---

### Bei NPS 7-8: Verbesserungs-Gespraech (24-48h nach NPS)

**Betreff:** Danke fuer dein Feedback -- lass uns kurz sprechen

---

Hallo {{KUNDENNAME}},

vielen Dank fuer dein ehrliches Feedback! Wir freuen uns, dass viel gut laeuft, und wir wollen verstehen, wie wir noch besser werden koennen.

Haettest du naechste Woche 15 Minuten fuer einen kurzen Call? Ich wuerde gerne hoeren, was aus deiner Sicht fehlt, damit du uns uneingeschraenkt weiterempfehlen wuerdest.

Dein Feedback fliesst direkt in unsere Arbeit ein -- und ich verspreche dir, dass sich daraus konkrete Verbesserungen ergeben.

Herzliche Gruesse,
{{AM_NAME}}

---

### Bei NPS 0-6: Sofort-Reaktion (innerhalb von 24h nach NPS)

**Betreff:** {{KUNDENNAME}}, wir muessen reden

---

Hallo {{KUNDENNAME}},

danke, dass du uns ehrliches Feedback gegeben hast. Es tut mir leid, dass wir deine Erwartungen nicht erfuellt haben.

Ich moechte das persoenlich mit dir besprechen und sicherstellen, dass wir das aendern. Koennen wir diese Woche noch einen kurzen Call machen? Ich bin [Zeitfenster 1], [Zeitfenster 2] oder [Zeitfenster 3] verfuegbar.

Deine Zufriedenheit hat fuer mich hoechste Prioritaet.

Herzliche Gruesse,
{{AM_NAME}}

*Hinweis: Zusaetzlich zum Account Manager wird auch der Geschaeftsfuehrer informiert und gegebenenfalls einbezogen.*

---

## Versand-Hinweise

- **Timing:** Exakt Tag 90 (im CRM als Trigger hinterlegen)
- **Personalisierung:** Konkrete Ergebnisse der letzten 90 Tage erwaehnen
- **Wichtig:** Follow-up Emails sind kritisch -- IMMER auf NPS reagieren
- **CRM-Aktion:** NPS-Score im Kundenprofil speichern, Health Score aktualisieren
- **Automatisierung:** Follow-ups koennen automatisiert werden, aber persoenlicher Touch bevorzugt
- **Wiederholung:** NPS quartalsweise wiederholen (nicht nur einmalig bei Tag 90)
