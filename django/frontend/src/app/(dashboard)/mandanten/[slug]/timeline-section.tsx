"use client";

import { useCallback, useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { apiFetch } from "@/lib/api";
import type { ClientActivity, ActivityType } from "@/types/task";

const TYPE_LABELS: Record<ActivityType, string> = {
  comment: "Kommentar",
  task_created: "Aufgabe erstellt",
  task_completed: "Aufgabe erledigt",
  task_skipped: "Aufgabe übersprungen",
  status_changed: "Status geändert",
  email_sent: "E-Mail gesendet",
  jira_executed: "Jira ausgeführt",
};

const TYPE_COLORS: Record<ActivityType, string> = {
  comment: "bg-blue-100 text-blue-700",
  task_created: "bg-green-100 text-green-700",
  task_completed: "bg-emerald-100 text-emerald-700",
  task_skipped: "bg-gray-100 text-gray-600",
  status_changed: "bg-yellow-100 text-yellow-700",
  email_sent: "bg-purple-100 text-purple-700",
  jira_executed: "bg-indigo-100 text-indigo-700",
};

interface TimelineSectionProps {
  slug: string;
  tenantId: string;
}

export function TimelineSection({ slug, tenantId }: TimelineSectionProps) {
  const [activities, setActivities] = useState<ClientActivity[]>([]);
  const [comment, setComment] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const fetchActivities = useCallback(async () => {
    try {
      const data = await apiFetch<ClientActivity[]>(
        `/api/v1/clients/${slug}/activities/`,
        { tenantId }
      );
      setActivities(data);
    } catch {
      /* ignore */
    }
  }, [slug, tenantId]);

  useEffect(() => {
    fetchActivities();
  }, [fetchActivities]);

  async function handleSubmitComment(e: React.FormEvent) {
    e.preventDefault();
    if (!comment.trim()) return;
    setSubmitting(true);
    try {
      await apiFetch(`/api/v1/clients/${slug}/activities/`, {
        method: "POST",
        body: JSON.stringify({ content: comment }),
        tenantId,
      });
      setComment("");
      fetchActivities();
    } catch {
      /* ignore */
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Aktivitäten</CardTitle>
      </CardHeader>
      <CardContent>
        {/* Comment input */}
        <form onSubmit={handleSubmitComment} className="mb-4 flex gap-2">
          <textarea
            className="flex-1 rounded-md border border-input bg-background px-3 py-2 text-sm"
            rows={2}
            placeholder="Kommentar schreiben..."
            value={comment}
            onChange={(e) => setComment(e.target.value)}
          />
          <Button type="submit" size="sm" disabled={submitting || !comment.trim()}>
            {submitting ? "..." : "Senden"}
          </Button>
        </form>

        {/* Timeline */}
        {activities.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Noch keine Aktivitäten vorhanden.
          </p>
        ) : (
          <div className="space-y-3">
            {activities.map((activity) => (
              <div key={activity.id} className="flex gap-3 border-b pb-3 last:border-0">
                {/* Type badge */}
                <span
                  className={`mt-0.5 h-fit shrink-0 rounded px-2 py-0.5 text-xs font-medium ${TYPE_COLORS[activity.activity_type]}`}
                >
                  {TYPE_LABELS[activity.activity_type]}
                </span>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <p className="text-sm whitespace-pre-wrap">{activity.content}</p>
                  {activity.task_title && (
                    <p className="text-xs text-muted-foreground">
                      Aufgabe: {activity.task_title}
                    </p>
                  )}
                  <p className="mt-1 text-xs text-muted-foreground">
                    {activity.author_email && `${activity.author_email} · `}
                    {new Date(activity.created_at).toLocaleString("de-DE")}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}
