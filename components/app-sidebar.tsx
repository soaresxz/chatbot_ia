"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import {
  LayoutDashboard,
  MessageSquare,
  BarChart3,
  Sparkles,
} from "lucide-react"

const navItems = [
  { label: "Visao Geral", href: "/", icon: LayoutDashboard },
  { label: "Conversas", href: "/conversations", icon: MessageSquare },
  { label: "Relatorios", href: "/reports", icon: BarChart3 },
]

export function AppSidebar() {
  const pathname = usePathname()

  return (
    <aside className="hidden lg:flex lg:flex-col lg:w-64 bg-sidebar-bg text-sidebar-fg border-r border-sidebar-border h-screen sticky top-0 shrink-0">
      <div className="flex items-center gap-3 px-6 py-6">
        <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary">
          <Sparkles className="h-5 w-5 text-primary-foreground" />
        </div>
        <span className="text-lg font-semibold tracking-tight">ClinicAI</span>
      </div>

      <nav className="flex-1 px-3 py-4">
        <ul className="flex flex-col gap-1">
          {navItems.map((item) => {
            const isActive = pathname === item.href
            return (
              <li key={item.href}>
                <Link
                  href={item.href}
                  className={cn(
                    "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                    isActive
                      ? "bg-sidebar-accent text-primary"
                      : "text-sidebar-fg/70 hover:bg-sidebar-accent hover:text-sidebar-fg"
                  )}
                >
                  <item.icon className="h-4 w-4" />
                  {item.label}
                </Link>
              </li>
            )
          })}
        </ul>
      </nav>

      <div className="px-4 pb-6">
        <div className="rounded-lg border border-sidebar-border bg-sidebar-accent/50 p-4">
          <p className="text-xs font-medium text-sidebar-fg/70">Plano Atual</p>
          <p className="mt-1 text-sm font-semibold">Professional</p>
          <p className="mt-1 text-xs text-sidebar-fg/50">
            1.284 mensagens este mes
          </p>
        </div>
      </div>
    </aside>
  )
}
