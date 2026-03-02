"use client";

import { useMemo, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useTenant } from "@/hooks/use-tenant";
import {
  LayoutDashboard,
  Users,
  CheckSquare,
  List,
  FileText,
  TrendingUp,
  UserPlus,
  CreditCard,
  Plug,
  Settings2,
  Tags,
  Settings,
  BarChart3,
  ChevronDown,
  ChevronRight,
  type LucideIcon,
} from "lucide-react";

interface NavItem {
  href: string;
  label: string;
  icon?: LucideIcon;
  requiredRole?: string;
  children?: { href: string; label: string; icon?: LucideIcon }[];
}

const allNavItems: NavItem[] = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/mandanten", label: "Mandanten", icon: Users },
  {
    href: "/nps",
    label: "NPS & Feedback",
    icon: BarChart3,
    children: [
      { href: "/nps/antworten", label: "Antworten" },
      { href: "/nps/kampagnen", label: "Kampagnen" },
      { href: "/nps/testimonials", label: "Testimonials" },
    ],
  },
  {
    href: "/aufgaben",
    label: "Aufgaben",
    icon: CheckSquare,
    children: [
      { href: "/aufgaben/listen", label: "Listen", icon: List },
      { href: "/aufgaben/vorlagen", label: "Vorlagen", icon: FileText },
    ],
  },
  { href: "/cashflow", label: "Cashflow", icon: TrendingUp, requiredRole: "owner" },
  { href: "/team", label: "Team", icon: UserPlus },
  { href: "/billing", label: "Abrechnung", icon: CreditCard },
  {
    href: "/integrationen",
    label: "Integrationen",
    icon: Plug,
    requiredRole: "owner",
    children: [
      { href: "/integrationen/jira", label: "Jira" },
      { href: "/integrationen/webhooks", label: "Webhooks" },
      { href: "/integrationen/email", label: "E-Mail" },
      { href: "/integrationen/twilio", label: "Telefonie" },
    ],
  },
  {
    href: "/optionen",
    label: "Optionen",
    icon: Settings2,
    children: [{ href: "/optionen/felder", label: "Felder", icon: Tags }],
  },
  { href: "/settings", label: "Einstellungen", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { currentTenant } = useTenant();
  const [openSections, setOpenSections] = useState<string[]>(["/aufgaben", "/nps", "/optionen", "/integrationen"]);

  const navItems = useMemo(
    () => allNavItems.filter((item) => !item.requiredRole || currentTenant?.role === item.requiredRole),
    [currentTenant?.role]
  );

  function toggleSection(href: string) {
    setOpenSections((prev) =>
      prev.includes(href) ? prev.filter((s) => s !== href) : [...prev, href]
    );
  }

  return (
    <aside className="hidden md:flex w-64 flex-col border-r bg-sidebar">
      <div className="flex h-14 items-center border-b px-6 gap-3">
        <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary text-primary-foreground text-sm font-bold">
          A
        </div>
        <Link href="/" className="flex items-center gap-2 font-semibold">
          <span className="text-xl">Aftersales</span>
        </Link>
      </div>
      <nav className="flex-1 space-y-1 p-4">
        {navItems.map((item) => {
          const Icon = item.icon;
          const isActive = item.children
            ? pathname.startsWith(item.href)
            : pathname === item.href;

          return item.children ? (
            <div key={item.href}>
              <button
                onClick={() => toggleSection(item.href)}
                className={cn(
                  "flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                  isActive
                    ? "bg-sidebar-active text-sidebar-active-foreground font-semibold"
                    : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                )}
              >
                {Icon && <Icon className="h-4 w-4 shrink-0" />}
                <span className="flex-1 text-left">{item.label}</span>
                {openSections.includes(item.href) ? (
                  <ChevronDown className="h-4 w-4 shrink-0" />
                ) : (
                  <ChevronRight className="h-4 w-4 shrink-0" />
                )}
              </button>
              {openSections.includes(item.href) && (
                <div className="ml-4 space-y-1 mt-1">
                  {item.children.map((child) => {
                    const ChildIcon = child.icon;
                    const isChildActive = pathname === child.href || pathname.startsWith(child.href + "/");
                    return (
                      <Link
                        key={child.href}
                        href={child.href}
                        className={cn(
                          "flex items-center gap-3 rounded-lg px-3 py-1.5 text-sm transition-colors",
                          isChildActive
                            ? "bg-sidebar-active text-sidebar-active-foreground font-semibold"
                            : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                        )}
                      >
                        {ChildIcon && <ChildIcon className="h-4 w-4 shrink-0" />}
                        {child.label}
                      </Link>
                    );
                  })}
                </div>
              )}
            </div>
          ) : (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
                isActive
                  ? "bg-sidebar-active text-sidebar-active-foreground font-semibold"
                  : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
              )}
            >
              {Icon && <Icon className="h-4 w-4 shrink-0" />}
              {item.label}
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
