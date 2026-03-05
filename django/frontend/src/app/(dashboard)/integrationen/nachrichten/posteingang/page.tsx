"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { useTenant } from "@/hooks/use-tenant";
import { apiFetch } from "@/lib/api";
import type { InboundEmail, WhatsAppMessage } from "@/types/email";

type ChannelTab = "all" | "email" | "whatsapp";
type AssignTab = "all" | "unassigned";

interface PaginatedResponse<T> {
  count: number;
  results: T[];
}

type UnifiedMessage =
  | { channel: "email"; data: InboundEmail }
  | { channel: "whatsapp"; data: WhatsAppMessage };

export default function PosteingangPage() {
  return (
    <Suspense fallback={<p className="text-sm text-muted-foreground">Laden...</p>}>
      <PosteingangContent />
    </Suspense>
  );
}

function PosteingangContent() {
  const { currentTenantId } = useTenant();
  const searchParams = useSearchParams();
  const clientId = searchParams.get("client");
  const clientSlug = searchParams.get("slug");
  const [emails, setEmails] = useState<InboundEmail[]>([]);
  const [waMessages, setWaMessages] = useState<WhatsAppMessage[]>([]);
  const [unassignedCount, setUnassignedCount] = useState(0);
  const [channelTab, setChannelTab] = useState<ChannelTab>("all");
  const [assignTab, setAssignTab] = useState<AssignTab>("all");
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [clientName, setClientName] = useState<string>("");

  useEffect(() => {
    if (!currentTenantId) return;
    setLoading(true);

    const emailParams = clientId ? `?client=${clientId}` : assignTab === "unassigned" ? "?assigned=false" : "";
    const waParams = clientId ? `?client=${clientId}` : "?direction=inbound";

    // Fetch emails
    const emailFetch = (channelTab === "whatsapp" && !clientId)
      ? Promise.resolve({ count: 0, results: [] as InboundEmail[] })
      : apiFetch<PaginatedResponse<InboundEmail>>(`/api/v1/emails/inbound/${emailParams}`, { tenantId: currentTenantId })
          .catch(() => ({ count: 0, results: [] as InboundEmail[] }));

    // Fetch WhatsApp messages
    const waFetch = (channelTab === "email" && !clientId)
      ? Promise.resolve({ count: 0, results: [] as WhatsAppMessage[] })
      : apiFetch<PaginatedResponse<WhatsAppMessage>>(`/api/v1/emails/whatsapp/${waParams}`, { tenantId: currentTenantId })
          .catch(() => ({ count: 0, results: [] as WhatsAppMessage[] }));

    Promise.all([emailFetch, waFetch]).then(([emailData, waData]) => {
      setEmails(emailData.results);
      setWaMessages(waData.results);
      if (clientId && emailData.results.length > 0 && emailData.results[0].client_name) {
        setClientName(emailData.results[0].client_name);
      } else if (clientId && waData.results.length > 0 && waData.results[0].client_name) {
        setClientName(waData.results[0].client_name);
      }
      setLoading(false);
    });

    // Unassigned count for emails (badge)
    if (!clientId) {
      apiFetch<PaginatedResponse<InboundEmail>>("/api/v1/emails/inbound/?assigned=false", { tenantId: currentTenantId })
        .then((data) => setUnassignedCount(data.count))
        .catch(() => setUnassignedCount(0));
    }
  }, [currentTenantId, channelTab, assignTab, clientId]);

  // Build unified message list sorted by created_at
  const unified: UnifiedMessage[] = [];
  if (channelTab !== "whatsapp") {
    for (const e of emails) unified.push({ channel: "email", data: e });
  }
  if (channelTab !== "email") {
    for (const w of waMessages) unified.push({ channel: "whatsapp", data: w });
  }
  unified.sort((a, b) => new Date(b.data.created_at).getTime() - new Date(a.data.created_at).getTime());

  const unreadCount = unified.filter((m) => !m.data.is_read).length;

  async function handleExpand(msg: UnifiedMessage) {
    const id = msg.data.id;
    if (expandedId === id) {
      setExpandedId(null);
      return;
    }
    setExpandedId(id);

    if (!msg.data.is_read) {
      try {
        if (msg.channel === "email") {
          await apiFetch(`/api/v1/emails/inbound/${id}/`, { tenantId: currentTenantId! });
          setEmails((prev) => prev.map((e) => (e.id === id ? { ...e, is_read: true } : e)));
        } else {
          await apiFetch(`/api/v1/emails/whatsapp/${id}/`, { tenantId: currentTenantId! });
          setWaMessages((prev) => prev.map((w) => (w.id === id ? { ...w, is_read: true } : w)));
        }
      } catch {
        // Ignore
      }
    }
  }

  return (
    <div className="space-y-6">
      {clientId && clientSlug && (
        <nav className="flex items-center gap-1 text-sm text-muted-foreground">
          <Link href="/mandanten" className="hover:text-foreground">Mandanten</Link>
          <span>/</span>
          <Link href={`/mandanten/${clientSlug}`} className="hover:text-foreground">{clientName || "Stammdaten"}</Link>
          <span>/</span>
          <span className="text-foreground font-medium">Posteingang</span>
        </nav>
      )}

      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <h1 className="text-2xl font-bold">
            {clientId ? `Posteingang — ${clientName || "Mandant"}` : "Posteingang"}
          </h1>
          {unreadCount > 0 && (
            <span className="inline-flex h-6 min-w-6 items-center justify-center rounded-full bg-blue-600 px-2 text-xs font-medium text-white">
              {unreadCount}
            </span>
          )}
        </div>
        {clientId && clientSlug ? (
          <Link href={`/mandanten/${clientSlug}`}>
            <Button variant="outline" size="sm">Zurück zu Stammdaten</Button>
          </Link>
        ) : (
          <Link href="/integrationen/nachrichten">
            <Button variant="outline" size="sm">Zurück</Button>
          </Link>
        )}
      </div>

      {/* Channel Tabs */}
      <div className="flex gap-2 border-b">
        {(["all", "email", "whatsapp"] as ChannelTab[]).map((tab) => (
          <button
            key={tab}
            onClick={() => setChannelTab(tab)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ${
              channelTab === tab
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            {tab === "all" ? "Alle" : tab === "email" ? "E-Mail" : "WhatsApp"}
          </button>
        ))}

        {/* Unassigned sub-tab (only in email or all view, not client-filtered) */}
        {!clientId && channelTab !== "whatsapp" && (
          <button
            onClick={() => setAssignTab(assignTab === "unassigned" ? "all" : "unassigned")}
            className={`flex items-center gap-2 px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors ml-auto ${
              assignTab === "unassigned"
                ? "border-amber-500 text-amber-700"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            Nicht zugeordnet
            {unassignedCount > 0 && (
              <span className="inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-amber-500 px-1.5 text-xs font-medium text-white">
                {unassignedCount}
              </span>
            )}
          </button>
        )}
      </div>

      {loading ? (
        <p className="text-sm text-muted-foreground">Laden...</p>
      ) : unified.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          {channelTab === "whatsapp" ? "Keine WhatsApp-Nachrichten vorhanden." : "Keine Nachrichten vorhanden."}
        </p>
      ) : (
        <div className="space-y-1">
          {unified.map((msg) => {
            const isUnread = !msg.data.is_read;
            const isEmail = msg.channel === "email";
            const emailData = isEmail ? (msg.data as InboundEmail) : null;
            const waData = !isEmail ? (msg.data as WhatsAppMessage) : null;

            return (
              <Card key={msg.data.id} className={isUnread ? "border-blue-200 bg-blue-50/30" : ""}>
                <CardContent className="p-0">
                  <button
                    onClick={() => handleExpand(msg)}
                    className="flex w-full items-start gap-3 px-4 py-3 text-left hover:bg-muted/50"
                  >
                    {/* Unread dot */}
                    <div className="mt-1.5 flex-shrink-0">
                      {isUnread ? (
                        <span className="inline-block h-2 w-2 rounded-full bg-blue-600" />
                      ) : (
                        <span className="inline-block h-2 w-2" />
                      )}
                    </div>

                    {/* Channel badge */}
                    <div className="mt-1 flex-shrink-0">
                      <span className={`inline-block rounded px-1.5 py-0.5 text-[10px] font-medium ${
                        isEmail ? "bg-blue-100 text-blue-700" : "bg-green-100 text-green-700"
                      }`}>
                        {isEmail ? "E-Mail" : "WA"}
                      </span>
                    </div>

                    <div className="min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-2">
                        <span className={`truncate text-sm ${isUnread ? "font-semibold" : ""}`}>
                          {isEmail
                            ? (emailData!.from_name || emailData!.from_email)
                            : waData!.from_number}
                        </span>
                        <span className="flex-shrink-0 text-xs text-muted-foreground">
                          {new Date(msg.data.created_at).toLocaleString("de-DE", {
                            day: "2-digit",
                            month: "2-digit",
                            hour: "2-digit",
                            minute: "2-digit",
                          })}
                        </span>
                      </div>
                      <p className={`truncate text-sm ${isUnread ? "font-medium" : "text-muted-foreground"}`}>
                        {isEmail
                          ? (emailData!.subject || "(Kein Betreff)")
                          : (waData!.body_text || "(Kein Inhalt)")}
                      </p>
                      <div className="mt-0.5 flex items-center gap-2">
                        {isEmail ? (
                          emailData!.is_assigned ? (
                            <span className="text-xs text-muted-foreground">{emailData!.client_name || "Mandant"}</span>
                          ) : (
                            <span className="text-xs font-medium text-amber-600">Nicht zugeordnet</span>
                          )
                        ) : (
                          waData!.client_name ? (
                            <span className="text-xs text-muted-foreground">{waData!.client_name}</span>
                          ) : (
                            <span className="text-xs font-medium text-amber-600">Nicht zugeordnet</span>
                          )
                        )}
                      </div>
                    </div>
                  </button>

                  {/* Expanded body */}
                  {expandedId === msg.data.id && (
                    <div className="border-t px-4 py-3">
                      {isEmail ? (
                        <>
                          <div className="mb-2 space-y-1 text-xs text-muted-foreground">
                            <p>Von: {emailData!.from_name ? `${emailData!.from_name} <${emailData!.from_email}>` : emailData!.from_email}</p>
                            <p>An: {emailData!.to_email}</p>
                            <p>Betreff: {emailData!.subject || "(Kein Betreff)"}</p>
                          </div>
                          {emailData!.has_attachments && (
                            <div className="mb-2 rounded border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-800">
                              Diese E-Mail enthält Anhänge. Bitte im Original-Postfach öffnen.
                            </div>
                          )}
                        </>
                      ) : (
                        <div className="mb-2 space-y-1 text-xs text-muted-foreground">
                          <p>Von: {waData!.from_number}</p>
                          <p>An: {waData!.to_number}</p>
                          <p>Typ: {waData!.message_type}</p>
                        </div>
                      )}
                      <pre className="whitespace-pre-wrap text-sm">
                        {isEmail ? (emailData!.body_text || "(Kein Inhalt)") : (waData!.body_text || "(Kein Inhalt)")}
                      </pre>
                    </div>
                  )}
                </CardContent>
              </Card>
            );
          })}
        </div>
      )}
    </div>
  );
}
