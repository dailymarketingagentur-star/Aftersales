"use client";

import { useTwilioCallContext } from "@/contexts/twilio-call-context";

export function useTwilioCall() {
  return useTwilioCallContext();
}
