"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from "react";
import type { Device, Call } from "@twilio/voice-sdk";
import { apiFetch } from "@/lib/api";
import type { TwilioAccessToken } from "@/types/integration";

type CallStatus =
  | "idle"
  | "connecting"
  | "ringing"
  | "connected"
  | "disconnected";

interface TwilioCallContextValue {
  callStatus: CallStatus;
  calleeName: string;
  calleeNumber: string;
  callDuration: number;
  isMuted: boolean;
  isAvailable: boolean;
  startCall: (
    to: string,
    callerId: string,
    calleeName: string,
    tenantId: string
  ) => Promise<void>;
  hangUp: () => void;
  toggleMute: () => void;
}

const TwilioCallContext = createContext<TwilioCallContextValue | null>(null);

export function TwilioCallProvider({
  children,
}: {
  children: React.ReactNode;
}) {
  const [callStatus, setCallStatus] = useState<CallStatus>("idle");
  const [calleeName, setCalleeName] = useState("");
  const [calleeNumber, setCalleeNumber] = useState("");
  const [callDuration, setCallDuration] = useState(0);
  const [isMuted, setIsMuted] = useState(false);
  const [isAvailable, setIsAvailable] = useState(false);

  const deviceRef = useRef<Device | null>(null);
  const callRef = useRef<Call | null>(null);
  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);

  // Clean up timer on unmount
  useEffect(() => {
    return () => {
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  const startTimer = useCallback(() => {
    setCallDuration(0);
    timerRef.current = setInterval(() => {
      setCallDuration((prev) => prev + 1);
    }, 1000);
  }, []);

  const stopTimer = useCallback(() => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
  }, []);

  const startCall = useCallback(
    async (
      to: string,
      callerId: string,
      contactName: string,
      tenantId: string
    ) => {
      if (callStatus !== "idle" && callStatus !== "disconnected") return;

      setCalleeName(contactName);
      setCalleeNumber(to);
      setCallStatus("connecting");
      setIsMuted(false);

      try {
        // 1. Get token from backend
        const tokenData = await apiFetch<TwilioAccessToken>(
          "/api/v1/integrations/twilio/token/",
          { method: "POST", tenantId }
        );

        // 2. Initialize Device (lazy — new device per call for simplicity)
        const { Device: TwilioDevice } = await import("@twilio/voice-sdk");

        if (deviceRef.current) {
          deviceRef.current.destroy();
        }

        const device = new TwilioDevice(tokenData.token, {
          codecPreferences: ["opus" as never, "pcmu" as never],
        });

        // Apply saved audio device preferences
        const inputId = localStorage.getItem("twilio_audio_input");
        const outputId = localStorage.getItem("twilio_audio_output");
        if (inputId) {
          try {
            await device.audio?.setInputDevice(inputId);
          } catch {
            /* device might not exist anymore */
          }
        }
        if (outputId) {
          try {
            await device.audio?.speakerDevices.set(outputId);
          } catch {
            /* device might not exist anymore */
          }
        }

        await device.register();
        deviceRef.current = device;

        // 3. Start outgoing call
        const call = await device.connect({
          params: {
            To: to,
            CallerId: callerId,
          },
        });

        callRef.current = call;
        setCallStatus("ringing");

        call.on("accept", () => {
          setCallStatus("connected");
          startTimer();
        });

        call.on("disconnect", () => {
          setCallStatus("disconnected");
          stopTimer();
          callRef.current = null;
        });

        call.on("cancel", () => {
          setCallStatus("disconnected");
          stopTimer();
          callRef.current = null;
        });

        call.on("error", () => {
          setCallStatus("disconnected");
          stopTimer();
          callRef.current = null;
        });

        setIsAvailable(true);
      } catch {
        setCallStatus("disconnected");
      }
    },
    [callStatus, startTimer, stopTimer]
  );

  const hangUp = useCallback(() => {
    if (callRef.current) {
      callRef.current.disconnect();
      callRef.current = null;
    }
    setCallStatus("disconnected");
    stopTimer();
  }, [stopTimer]);

  const toggleMute = useCallback(() => {
    if (callRef.current) {
      const newMuted = !callRef.current.isMuted();
      callRef.current.mute(newMuted);
      setIsMuted(newMuted);
    }
  }, []);

  const value: TwilioCallContextValue = {
    callStatus,
    calleeName,
    calleeNumber,
    callDuration,
    isMuted,
    isAvailable,
    startCall,
    hangUp,
    toggleMute,
  };

  return (
    <TwilioCallContext value={value}>{children}</TwilioCallContext>
  );
}

export function useTwilioCallContext(): TwilioCallContextValue {
  const ctx = useContext(TwilioCallContext);
  if (!ctx) {
    throw new Error(
      "useTwilioCallContext must be used within a <TwilioCallProvider>"
    );
  }
  return ctx;
}
