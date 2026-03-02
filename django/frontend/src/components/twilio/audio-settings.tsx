"use client";

import { useEffect, useState } from "react";
import { Label } from "@/components/ui/label";

export function AudioSettingsPanel() {
  const [open, setOpen] = useState(false);
  const [audioInputs, setAudioInputs] = useState<MediaDeviceInfo[]>([]);
  const [audioOutputs, setAudioOutputs] = useState<MediaDeviceInfo[]>([]);
  const [selectedInput, setSelectedInput] = useState(
    () => (typeof window !== "undefined" && localStorage.getItem("twilio_audio_input")) || ""
  );
  const [selectedOutput, setSelectedOutput] = useState(
    () => (typeof window !== "undefined" && localStorage.getItem("twilio_audio_output")) || ""
  );

  useEffect(() => {
    if (!open) return;

    async function loadDevices() {
      try {
        // Request permission first so labels are populated
        await navigator.mediaDevices.getUserMedia({ audio: true });
        const devices = await navigator.mediaDevices.enumerateDevices();
        setAudioInputs(devices.filter((d) => d.kind === "audioinput"));
        setAudioOutputs(devices.filter((d) => d.kind === "audiooutput"));
      } catch {
        // Permission denied or no devices
      }
    }

    loadDevices();
  }, [open]);

  function handleInputChange(deviceId: string) {
    setSelectedInput(deviceId);
    localStorage.setItem("twilio_audio_input", deviceId);
  }

  function handleOutputChange(deviceId: string) {
    setSelectedOutput(deviceId);
    localStorage.setItem("twilio_audio_output", deviceId);
  }

  return (
    <div className="mt-1">
      <button
        onClick={() => setOpen(!open)}
        className="inline-flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
        title="Audio-Einstellungen"
      >
        <svg
          xmlns="http://www.w3.org/2000/svg"
          width="12"
          height="12"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
        >
          <path d="M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.08a2 2 0 0 1-1-1.74v-.5a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z" />
          <circle cx="12" cy="12" r="3" />
        </svg>
        Audio-Einstellungen
      </button>

      {open && (
        <div className="mt-2 space-y-3 rounded-lg border bg-background p-3">
          <div>
            <Label htmlFor="audio-input" className="text-xs">
              Mikrofon
            </Label>
            <select
              id="audio-input"
              className="mt-1 h-8 w-full rounded-md border border-input bg-background px-2 text-xs"
              value={selectedInput}
              onChange={(e) => handleInputChange(e.target.value)}
            >
              <option value="">Standard</option>
              {audioInputs.map((d) => (
                <option key={d.deviceId} value={d.deviceId}>
                  {d.label || `Mikrofon ${d.deviceId.slice(0, 8)}`}
                </option>
              ))}
            </select>
          </div>
          <div>
            <Label htmlFor="audio-output" className="text-xs">
              Lautsprecher / Kopfhörer
            </Label>
            <select
              id="audio-output"
              className="mt-1 h-8 w-full rounded-md border border-input bg-background px-2 text-xs"
              value={selectedOutput}
              onChange={(e) => handleOutputChange(e.target.value)}
            >
              <option value="">Standard</option>
              {audioOutputs.map((d) => (
                <option key={d.deviceId} value={d.deviceId}>
                  {d.label || `Lautsprecher ${d.deviceId.slice(0, 8)}`}
                </option>
              ))}
            </select>
          </div>
        </div>
      )}
    </div>
  );
}
