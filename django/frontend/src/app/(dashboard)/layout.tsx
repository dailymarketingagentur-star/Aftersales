"use client";

import { Sidebar } from "@/components/layout/sidebar";
import { Header } from "@/components/layout/header";
import { TenantProvider } from "@/contexts/tenant-context";
import { TwilioCallProvider } from "@/contexts/twilio-call-context";
import { ActiveCallBar } from "@/components/twilio/active-call-bar";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  return (
    <TenantProvider>
      <TwilioCallProvider>
        <div className="flex min-h-screen">
          <Sidebar />
          <div className="flex flex-1 flex-col">
            <Header />
            <main className="flex-1 p-6">{children}</main>
          </div>
        </div>
        <ActiveCallBar />
      </TwilioCallProvider>
    </TenantProvider>
  );
}
