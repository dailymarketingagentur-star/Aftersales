"use client";

import { useCallback, useEffect, useState } from "react";
import { useParams, useSearchParams } from "next/navigation";

interface SurveyData {
  tenant_name: string;
  client_first_name: string;
  is_expired: boolean;
  is_responded: boolean;
}

const SCORE_COLORS: Record<number, string> = {
  0: "bg-red-500 hover:bg-red-600",
  1: "bg-red-500 hover:bg-red-600",
  2: "bg-red-400 hover:bg-red-500",
  3: "bg-orange-400 hover:bg-orange-500",
  4: "bg-orange-400 hover:bg-orange-500",
  5: "bg-yellow-400 hover:bg-yellow-500",
  6: "bg-yellow-400 hover:bg-yellow-500",
  7: "bg-yellow-300 hover:bg-yellow-400",
  8: "bg-lime-400 hover:bg-lime-500",
  9: "bg-green-400 hover:bg-green-500",
  10: "bg-green-500 hover:bg-green-600",
};

function getSegmentQuestion(score: number): string {
  if (score >= 9) return "Wunderbar! Was gefaellt Ihnen besonders an unserer Zusammenarbeit?";
  if (score >= 7) return "Danke! Was koennten wir verbessern, um Ihre Erwartungen noch besser zu erfuellen?";
  return "Das tut uns leid. Was koennen wir konkret verbessern?";
}

function getThankYouMessage(segment: string): string {
  if (segment === "promoter")
    return "Vielen Dank fuer Ihre hervorragende Bewertung! Wir freuen uns sehr ueber Ihr positives Feedback und werden uns in Kuerze bei Ihnen melden.";
  if (segment === "passive")
    return "Vielen Dank fuer Ihr Feedback! Wir werden daran arbeiten, Ihre Erwartungen noch besser zu erfuellen.";
  return "Vielen Dank fuer Ihr ehrliches Feedback. Wir nehmen Ihre Rueckmeldung sehr ernst und werden uns zeitnah bei Ihnen melden.";
}

export default function SurveyPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const token = params.token as string;

  const [surveyData, setSurveyData] = useState<SurveyData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  // Survey flow states
  const [selectedScore, setSelectedScore] = useState<number | null>(null);
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [resultSegment, setResultSegment] = useState("");

  // Kundenstimme (post-submit comment)
  const [testimonialComment, setTestimonialComment] = useState("");
  const [testimonialSubmitting, setTestimonialSubmitting] = useState(false);
  const [testimonialSubmitted, setTestimonialSubmitted] = useState(false);
  const [testimonialError, setTestimonialError] = useState("");

  // Auto-submit: Score aus URL lesen
  const urlScore = searchParams.get("score");
  const [autoSubmitDone, setAutoSubmitDone] = useState(false);

  const fetchSurvey = useCallback(async () => {
    try {
      const res = await fetch(`/api/v1/nps/public/${token}/`);
      if (!res.ok) {
        setError("Umfrage nicht gefunden.");
        return;
      }
      const data: SurveyData = await res.json();
      setSurveyData(data);
    } catch {
      setError("Umfrage konnte nicht geladen werden.");
    } finally {
      setLoading(false);
    }
  }, [token]);

  useEffect(() => {
    fetchSurvey();
  }, [fetchSurvey]);

  // Auto-Submit wenn ?score=X in URL und Survey geladen
  useEffect(() => {
    if (autoSubmitDone || !surveyData || submitted || submitting) return;
    if (!urlScore) return;

    const score = parseInt(urlScore, 10);
    if (isNaN(score) || score < 0 || score > 10) return;

    // Survey muss beantwortbar sein
    if (surveyData.is_expired || surveyData.is_responded) return;

    setAutoSubmitDone(true);
    setSelectedScore(score);

    // Sofort submitten (ohne Kommentar)
    (async () => {
      setSubmitting(true);
      try {
        const res = await fetch(`/api/v1/nps/public/${token}/respond/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ score }),
        });

        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          setError(data.detail || "Fehler beim Absenden.");
          return;
        }

        const data = await res.json();
        setResultSegment(data.segment);
        setSubmitted(true);
      } catch {
        setError("Fehler beim Absenden.");
      } finally {
        setSubmitting(false);
      }
    })();
  }, [surveyData, urlScore, autoSubmitDone, submitted, submitting, token]);

  async function handleSubmit() {
    if (selectedScore === null) return;
    setSubmitting(true);
    setError("");

    try {
      const res = await fetch(`/api/v1/nps/public/${token}/respond/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ score: selectedScore, comment }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError(data.detail || "Fehler beim Absenden.");
        return;
      }

      const data = await res.json();
      setResultSegment(data.segment);
      setSubmitted(true);
    } catch {
      setError("Fehler beim Absenden.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleTestimonialSubmit() {
    if (!testimonialComment.trim()) return;
    setTestimonialSubmitting(true);
    setTestimonialError("");

    try {
      const res = await fetch(`/api/v1/nps/public/${token}/comment/`, {
        method: "PATCH",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ comment: testimonialComment }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setTestimonialError(data.detail || "Fehler beim Speichern.");
        return;
      }

      setTestimonialSubmitted(true);
    } catch {
      setTestimonialError("Fehler beim Speichern.");
    } finally {
      setTestimonialSubmitting(false);
    }
  }

  if (loading || (urlScore && !autoSubmitDone && !error)) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Laden...</p>
      </div>
    );
  }

  if (error && !surveyData) {
    return (
      <div className="text-center py-12">
        <h1 className="text-2xl font-bold mb-2">Fehler</h1>
        <p className="text-muted-foreground">{error}</p>
      </div>
    );
  }

  if (!surveyData) return null;

  // Already responded (ohne Auto-Submit)
  if (surveyData.is_responded && !submitted) {
    return (
      <div className="text-center py-12">
        <h1 className="text-2xl font-bold mb-2">Bereits beantwortet</h1>
        <p className="text-muted-foreground">Sie haben diese Umfrage bereits beantwortet. Vielen Dank!</p>
      </div>
    );
  }

  // Expired
  if (surveyData.is_expired) {
    return (
      <div className="text-center py-12">
        <h1 className="text-2xl font-bold mb-2">Umfrage abgelaufen</h1>
        <p className="text-muted-foreground">Diese Umfrage ist leider nicht mehr verfuegbar.</p>
      </div>
    );
  }

  // Auto-submit in progress
  if (submitting && urlScore) {
    return (
      <div className="text-center py-12">
        <p className="text-muted-foreground">Wird gesendet...</p>
      </div>
    );
  }

  // Error during auto-submit
  if (error && urlScore && !submitted) {
    return (
      <div className="text-center py-12">
        <h1 className="text-2xl font-bold mb-2">Fehler</h1>
        <p className="text-muted-foreground">{error}</p>
      </div>
    );
  }

  // Thank you page (with optional Kundenstimme textarea)
  if (submitted) {
    return (
      <div className="text-center py-12 space-y-4">
        <div className="text-5xl mb-4">
          {resultSegment === "promoter" ? "🎉" : resultSegment === "passive" ? "👍" : "🙏"}
        </div>
        <h1 className="text-2xl font-bold">Vielen Dank!</h1>
        <p className="text-muted-foreground max-w-md mx-auto">
          {getThankYouMessage(resultSegment)}
        </p>

        {/* Kundenstimme Textarea — nur anzeigen wenn noch nicht submitted */}
        {!testimonialSubmitted ? (
          <div className="max-w-md mx-auto mt-8 space-y-3 text-left">
            <h2 className="text-lg font-semibold text-center">Ihre Kundenstimme</h2>
            <p className="text-sm text-muted-foreground text-center">
              Moechten Sie uns noch etwas mitteilen? Ihr Feedback hilft uns, besser zu werden.
            </p>
            <textarea
              className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm min-h-[100px] resize-y"
              placeholder="Ihre Kundenstimme (optional)..."
              value={testimonialComment}
              onChange={(e) => setTestimonialComment(e.target.value)}
            />
            {testimonialError && <p className="text-sm text-destructive">{testimonialError}</p>}
            <button
              onClick={handleTestimonialSubmit}
              disabled={testimonialSubmitting || !testimonialComment.trim()}
              className="w-full h-11 rounded-md bg-primary text-primary-foreground font-medium text-sm hover:bg-primary/90 disabled:opacity-50 transition-colors"
            >
              {testimonialSubmitting ? "Wird gespeichert..." : "Kundenstimme absenden"}
            </button>
          </div>
        ) : (
          <p className="text-sm text-green-600 font-medium mt-4">
            Ihre Kundenstimme wurde gespeichert. Vielen Dank!
          </p>
        )}

        <p className="text-sm text-muted-foreground mt-8">— {surveyData.tenant_name}</p>
      </div>
    );
  }

  // Normal flow (kein ?score in URL) — Score-Auswahl auf der Seite
  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="text-center space-y-2">
        <p className="text-sm text-muted-foreground">{surveyData.tenant_name}</p>
        <h1 className="text-2xl font-bold">
          {surveyData.client_first_name ? `Hallo ${surveyData.client_first_name}!` : "Hallo!"}
        </h1>
        <p className="text-muted-foreground">
          Wie wahrscheinlich ist es, dass Sie uns einem Freund oder Kollegen weiterempfehlen?
        </p>
      </div>

      {/* Score selector (0-10) */}
      <div className="space-y-3">
        <div className="flex justify-between text-xs text-muted-foreground px-1">
          <span>Unwahrscheinlich</span>
          <span>Sehr wahrscheinlich</span>
        </div>
        <div className="grid grid-cols-11 gap-1">
          {Array.from({ length: 11 }, (_, i) => (
            <button
              key={i}
              onClick={() => setSelectedScore(i)}
              className={`
                h-12 rounded-md text-sm font-bold transition-all
                ${
                  selectedScore === i
                    ? `${SCORE_COLORS[i]} text-white ring-2 ring-offset-2 ring-primary scale-110`
                    : "bg-muted text-muted-foreground hover:bg-muted/80"
                }
              `}
            >
              {i}
            </button>
          ))}
        </div>
      </div>

      {/* Follow-up question + comment */}
      {selectedScore !== null && (
        <div className="space-y-4 animate-in fade-in slide-in-from-bottom-2">
          <p className="text-sm font-medium">{getSegmentQuestion(selectedScore)}</p>
          <textarea
            className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm min-h-[100px] resize-y"
            placeholder="Ihr Feedback (optional)..."
            value={comment}
            onChange={(e) => setComment(e.target.value)}
          />
          {error && <p className="text-sm text-destructive">{error}</p>}
          <button
            onClick={handleSubmit}
            disabled={submitting}
            className="w-full h-11 rounded-md bg-primary text-primary-foreground font-medium text-sm hover:bg-primary/90 disabled:opacity-50 transition-colors"
          >
            {submitting ? "Wird gesendet..." : "Feedback absenden"}
          </button>
        </div>
      )}
    </div>
  );
}
