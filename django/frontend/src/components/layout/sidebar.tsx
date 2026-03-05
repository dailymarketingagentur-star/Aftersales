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
  Wrench,
  type LucideIcon,
} from "lucide-react";

interface NavChild {
  href: string;
  label: string;
  icon?: LucideIcon;
  requiredRole?: string;
  children?: { href: string; label: string; icon?: LucideIcon }[];
}

interface NavItem {
  href: string;
  label: string;
  icon?: LucideIcon;
  requiredRole?: string;
  children?: NavChild[];
}

const allNavItems: NavItem[] = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/mandanten", label: "Mandanten", icon: Users },
  {
    href: "/tools",
    label: "Tools",
    icon: Wrench,
    children: [
      {
        href: "/aufgaben",
        label: "Vorlagen",
        icon: CheckSquare,
        children: [
          { href: "/aufgaben/listen", label: "Listen", icon: List },
          { href: "/aufgaben/vorlagen", label: "Vorlagen", icon: FileText },
        ],
      },
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
      { href: "/optionen/felder", label: "Service-Typen", icon: Tags },
    ],
  },
  { href: "/cashflow", label: "Cashflow", icon: TrendingUp, requiredRole: "owner" },
  {
    href: "/settings",
    label: "Einstellungen",
    icon: Settings,
    children: [
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
          { href: "/integrationen/nachrichten", label: "Nachrichten" },
          { href: "/integrationen/twilio", label: "Telefonie" },
        ],
      },
    ],
  },
];

export function Sidebar() {
  const pathname = usePathname();
  const { currentTenant } = useTenant();
  const role = currentTenant?.role;
  const [openSections, setOpenSections] = useState<string[]>(["/tools", "/settings"]);

  const navItems = useMemo(
    () => allNavItems.filter((item) => !item.requiredRole || role === item.requiredRole),
    [role]
  );

  function toggleSection(key: string) {
    setOpenSections((prev) =>
      prev.includes(key) ? prev.filter((s) => s !== key) : [...prev, key]
    );
  }

  function isPathActive(href: string, hasChildren: boolean) {
    if (href === "/") return pathname === "/";
    return hasChildren ? pathname.startsWith(href) : pathname === href || pathname.startsWith(href + "/");
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
          const isActive = isPathActive(item.href, !!item.children);

          // Top-level item without children — simple link
          if (!item.children) {
            return (
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
          }

          // Top-level item with children — collapsible section
          const visibleChildren = item.children.filter(
            (child) => !child.requiredRole || role === child.requiredRole
          );

          return (
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
                  {visibleChildren.map((child) => {
                    const ChildIcon = child.icon;
                    const isChildActive = isPathActive(child.href, !!child.children);

                    // Child without sub-children — simple link
                    if (!child.children) {
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
                    }

                    // Child with sub-children — nested collapsible
                    return (
                      <div key={child.href}>
                        <button
                          onClick={() => toggleSection(child.href)}
                          className={cn(
                            "flex w-full items-center gap-3 rounded-lg px-3 py-1.5 text-sm transition-colors",
                            isChildActive
                              ? "bg-sidebar-active text-sidebar-active-foreground font-semibold"
                              : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                          )}
                        >
                          {ChildIcon && <ChildIcon className="h-4 w-4 shrink-0" />}
                          <span className="flex-1 text-left">{child.label}</span>
                          {openSections.includes(child.href) ? (
                            <ChevronDown className="h-3 w-3 shrink-0" />
                          ) : (
                            <ChevronRight className="h-3 w-3 shrink-0" />
                          )}
                        </button>
                        {openSections.includes(child.href) && (
                          <div className="ml-4 space-y-1 mt-1">
                            {child.children.map((sub) => {
                              const SubIcon = sub.icon;
                              const isSubActive = pathname === sub.href || pathname.startsWith(sub.href + "/");
                              return (
                                <Link
                                  key={sub.href}
                                  href={sub.href}
                                  className={cn(
                                    "flex items-center gap-3 rounded-lg px-3 py-1.5 text-sm transition-colors",
                                    isSubActive
                                      ? "bg-sidebar-active text-sidebar-active-foreground font-semibold"
                                      : "text-muted-foreground hover:bg-accent hover:text-accent-foreground"
                                  )}
                                >
                                  {SubIcon && <SubIcon className="h-4 w-4 shrink-0" />}
                                  {sub.label}
                                </Link>
                              );
                            })}
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </nav>
    </aside>
  );
}
