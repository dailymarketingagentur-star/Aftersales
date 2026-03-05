"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useAuth } from "@/hooks/use-auth";
import { useTenant } from "@/hooks/use-tenant";
import { apiFetch } from "@/lib/api";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Building2, CreditCard, Users, CalendarClock, ListChecks, Loader2, Clock } from "lucide-react";
import type { DashboardTask, TaskStatus, TaskPriority, ActionType } from "@/types/task";

// ---------------------------------------------------------------------------
// Label-Konstanten (aus task-section.tsx uebernommen)
// ---------------------------------------------------------------------------
const STATUS_LABELS: Record<TaskStatus, string> = {
  planned: "Geplant",
  open: "Offen",
  in_progress: "In Bearbeitung",
  completed: "Erledigt",
  skipped: "Übersprungen",
};

const PRIORITY_COLORS: Record<string, string> = {
  low: "bg-gray-100 text-gray-700",
  medium: "bg-blue-100 text-blue-700",
  high: "bg-orange-100 text-orange-700",
  critical: "bg-red-100 text-red-700",
};

const PRIORITY_LABELS: Record<string, string> = {
  low: "Niedrig",
  medium: "Mittel",
  high: "Hoch",
  critical: "Kritisch",
};

const ACTION_LABELS: Record<string, string> = {
  email: "E-Mail",
  email_sequence: "E-Mail-Sequenz",
  package: "Paket",
  phone: "Telefonat",
  meeting: "Meeting",
  document: "Dokument",
  jira_project: "Jira-Projekt",
  jira_ticket: "Jira-Ticket",
  webhook: "Webhook",
  whatsapp: "WhatsApp",
  manual: "Manuell",
};

// ---------------------------------------------------------------------------
// TaskRow Komponente
// ---------------------------------------------------------------------------
function TaskRow({ task }: { task: DashboardTask }) {
  const dueDateStr = task.due_date
    ? new Date(task.due_date).toLocaleDateString("de-DE", {
        day: "2-digit",
        month: "2-digit",
        year: "numeric",
      })
    : "—";

  const isOverdue =
    task.due_date && new Date(task.due_date) < new Date(new Date().toDateString());

  return (
    <div className="flex items-center gap-3 rounded-md border px-4 py-3 text-sm hover:bg-muted/50">
      {/* Titel + Mandant */}
      <div className="min-w-0 flex-1">
        <p className="truncate font-medium">{task.title}</p>
        <Link
          href={`/mandanten/${task.client_slug}`}
          className="text-xs text-muted-foreground hover:underline"
        >
          {task.client_name}
        </Link>
      </div>

      {/* Faelligkeit */}
      <div className={`w-24 shrink-0 text-center text-xs ${isOverdue ? "font-semibold text-red-600" : "text-muted-foreground"}`}>
        {dueDateStr}
      </div>

      {/* Prioritaet */}
      <span className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-medium ${PRIORITY_COLORS[task.priority] || ""}`}>
        {PRIORITY_LABELS[task.priority] || task.priority}
      </span>

      {/* Aktionstyp */}
      <span className="w-28 shrink-0 text-center text-xs text-muted-foreground">
        {ACTION_LABELS[task.action_type] || task.action_type}
      </span>

      {/* Status */}
      <span className="w-28 shrink-0 text-center text-xs">
        {STATUS_LABELS[task.status] || task.status}
      </span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// TaskList Komponente
// ---------------------------------------------------------------------------
function TaskListView({
  tasks,
  loading,
  emptyMessage,
}: {
  tasks: DashboardTask[];
  loading: boolean;
  emptyMessage: string;
}) {
  if (loading) {
    return (
      <div className="flex items-center justify-center py-12 text-muted-foreground">
        <Loader2 className="mr-2 h-5 w-5 animate-spin" />
        Lade Aufgaben…
      </div>
    );
  }

  if (tasks.length === 0) {
    return (
      <p className="py-12 text-center text-muted-foreground">{emptyMessage}</p>
    );
  }

  return (
    <div className="space-y-1">
      {tasks.map((task) => (
        <TaskRow key={task.id} task={task} />
      ))}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Dashboard Page
// ---------------------------------------------------------------------------
export default function DashboardPage() {
  const { user } = useAuth();
  const { currentTenant } = useTenant();

  const [todayTasks, setTodayTasks] = useState<DashboardTask[]>([]);
  const [allOpenTasks, setAllOpenTasks] = useState<DashboardTask[]>([]);
  const [plannedTasks, setPlannedTasks] = useState<DashboardTask[]>([]);
  const [loadingToday, setLoadingToday] = useState(true);
  const [loadingAll, setLoadingAll] = useState(true);
  const [loadingPlanned, setLoadingPlanned] = useState(true);

  useEffect(() => {
    if (!currentTenant) return;

    apiFetch("/api/v1/tasks/dashboard/?due_date=today&status=open,in_progress")
      .then((res) => res.json())
      .then((data) => setTodayTasks(data))
      .catch(() => setTodayTasks([]))
      .finally(() => setLoadingToday(false));

    apiFetch("/api/v1/tasks/dashboard/?status=open,in_progress")
      .then((res) => res.json())
      .then((data) => setAllOpenTasks(data))
      .catch(() => setAllOpenTasks([]))
      .finally(() => setLoadingAll(false));

    apiFetch("/api/v1/tasks/dashboard/?status=planned")
      .then((res) => res.json())
      .then((data) => setPlannedTasks(data))
      .catch(() => setPlannedTasks([]))
      .finally(() => setLoadingPlanned(false));
  }, [currentTenant]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Willkommen zurück{user ? `, ${user.first_name}` : ""}.
        </p>
      </div>

      {/* Stat Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card className="border-t-4 border-t-primary">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Building2 className="h-5 w-5 text-primary" />
              Organisation
            </CardTitle>
            <CardDescription>Aktuelle Organisation</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{currentTenant?.name || "\u2014"}</p>
          </CardContent>
        </Card>
        <Card className="border-t-4 border-t-primary">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CreditCard className="h-5 w-5 text-primary" />
              Abonnement
            </CardTitle>
            <CardDescription>Aktueller Status</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{"\u2014"}</p>
          </CardContent>
        </Card>
        <Card className="border-t-4 border-t-primary">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5 text-primary" />
              Team
            </CardTitle>
            <CardDescription>Mitglieder</CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-2xl font-bold">{"\u2014"}</p>
          </CardContent>
        </Card>
      </div>

      {/* Aufgaben-Tabs */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ListChecks className="h-5 w-5" />
            Aufgaben
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="heute">
            <TabsList>
              <TabsTrigger value="heute" className="gap-1.5">
                <CalendarClock className="h-4 w-4" />
                Heute
                {!loadingToday && (
                  <span className="ml-1 rounded-full bg-muted px-1.5 py-0.5 text-xs">
                    {todayTasks.length}
                  </span>
                )}
              </TabsTrigger>
              <TabsTrigger value="alle" className="gap-1.5">
                <ListChecks className="h-4 w-4" />
                Alle offenen
                {!loadingAll && (
                  <span className="ml-1 rounded-full bg-muted px-1.5 py-0.5 text-xs">
                    {allOpenTasks.length}
                  </span>
                )}
              </TabsTrigger>
              <TabsTrigger value="geplant" className="gap-1.5">
                <Clock className="h-4 w-4" />
                Geplant
                {!loadingPlanned && (
                  <span className="ml-1 rounded-full bg-muted px-1.5 py-0.5 text-xs">
                    {plannedTasks.length}
                  </span>
                )}
              </TabsTrigger>
            </TabsList>
            <TabsContent value="heute" className="mt-4">
              <TaskListView
                tasks={todayTasks}
                loading={loadingToday}
                emptyMessage="Keine Aufgaben für heute fällig."
              />
            </TabsContent>
            <TabsContent value="alle" className="mt-4">
              <TaskListView
                tasks={allOpenTasks}
                loading={loadingAll}
                emptyMessage="Keine offenen Aufgaben vorhanden."
              />
            </TabsContent>
            <TabsContent value="geplant" className="mt-4">
              <TaskListView
                tasks={plannedTasks}
                loading={loadingPlanned}
                emptyMessage="Keine geplanten Aufgaben vorhanden."
              />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
