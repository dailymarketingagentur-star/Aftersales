"use client";

import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";
import { useTwilioCall } from "@/hooks/use-twilio-call";
import { useTenant } from "@/hooks/use-tenant";
import { apiFetch } from "@/lib/api";
import type { TwilioConnection } from "@/types/integration";

interface CallButtonProps {
  phoneNumber: string;
  contactName: string;
}

export function CallButton({ phoneNumber, contactName }: CallButtonProps) {
  const { currentTenantId } = useTenant();
  const { callStatus, startCall, hangUp, toggleMute, isMuted, callDuration } =
    useTwilioCall();
  const [twilioAvailable, setTwilioAvailable] = useState(false);
  const [callerId, setCallerId] = useState("");

  useEffect(() => {
    if (!currentTenantId) return;
    apiFetch<TwilioConnection>("/api/v1/integrations/twilio/connection/", {
      tenantId: currentTenantId,
    })
      .then((conn) => {
        setTwilioAvailable(conn.is_active);
        setCallerId(conn.phone_number);
      })
      .catch(() => setTwilioAvailable(false));
  }, [currentTenantId]);

  function formatDuration(seconds: number) {
    const m = Math.floor(seconds / 60);
    const s = seconds % 60;
    return `${m}:${s.toString().padStart(2, "0")}`;
  }

  // Twilio nicht verfuegbar: Telefonnummer als plain text
  if (!twilioAvailable) {
    return <span>{phoneNumber}</span>;
  }

  // Waehrend eines Anrufs zu dieser Nummer
  const isThisCall =
    callStatus !== "idle" && callStatus !== "disconnected";

  if (isThisCall) {
    return (
      <div className="flex items-center gap-2">
        <span className="font-medium">{phoneNumber}</span>
        {callStatus === "connecting" && (
          <span className="text-xs text-yellow-600">Verbinde...</span>
        )}
        {callStatus === "ringing" && (
          <span className="text-xs text-blue-600">Klingelt...</span>
        )}
        {callStatus === "connected" && (
          <>
            <span className="text-xs text-green-600">
              {formatDuration(callDuration)}
            </span>
            <Button
              size="sm"
              variant={isMuted ? "destructive" : "outline"}
              onClick={toggleMute}
              className="h-7 px-2 text-xs"
            >
              {isMuted ? "Stumm" : "Mikro"}
            </Button>
          </>
        )}
        <Button
          size="sm"
          variant="destructive"
          onClick={hangUp}
          className="h-7 px-2 text-xs"
        >
          Auflegen
        </Button>
      </div>
    );
  }

  // Idle — klickbare Nummer
  return (
    <button
      onClick={() =>
        currentTenantId &&
        startCall(phoneNumber, callerId, contactName, currentTenantId)
      }
      className="inline-flex items-center gap-1 text-green-700 underline underline-offset-4 hover:text-green-900"
      title="Anrufen"
    >
      <svg
        xmlns="http://www.w3.org/2000/svg"
        width="14"
        height="14"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z" />
      </svg>
      {phoneNumber}
    </button>
  );
}
