"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import { cn } from "@/lib/utils"
import {
  LayoutDashboard,
  MessageSquare,
  BarChart3,
  Menu,
  Sparkles,
  X,
} from "lucide-react"
import { useState, useEffect, useRef } from "react"

const navItems = [
  { label: "Visao Geral", href: "/", icon: LayoutDashboard },
  { label: "Conversas", href: "/conversations", icon: MessageSquare },
  { label: "Relatorios", href: "/reports", icon: BarChart3 },
]

export function MobileNav() {
  const pathname = usePathname()
  const [open, setOpen] = useState(false)
  const drawerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (drawerRef.current && !drawerRef.current.contains(event.target as Node)) {
        setOpen(false)
      }
    }
    if (open) {
      document.addEventListener("mousedown", handleClickOutside)
      document.body.style.overflow = "hidden"
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside)
      document.body.style.overflow = ""
    }
  }, [open])

  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="lg:hidden flex items-center justify-center h-9 w-9 rounded-md hover:bg-muted transition-colors"
        aria-label="Abrir menu"
      >
        <Menu className="h-5 w-5" />
      </button>

      {open && (
        <div className="fixed inset-0 z-50 bg-foreground/20 backdrop-blur-sm lg:hidden">
          <div
            ref={drawerRef}
            className="fixed inset-y-0 left-0 w-64 bg-sidebar-bg text-sidebar-fg shadow-xl animate-in slide-in-from-left duration-200"
          >
            <div className="flex items-center justify-between px-6 py-6 border-b border-sidebar-border">
              <div className="flex items-center gap-3">
                <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-primary">
                  <Sparkles className="h-5 w-5 text-primary-foreground" />
                </div>
                <span className="text-lg font-semibold tracking-tight">ClinicAI</span>
              </div>
              <button
                onClick={() => setOpen(false)}
                className="flex items-center justify-center h-8 w-8 rounded-md hover:bg-sidebar-accent transition-colors"
                aria-label="Fechar menu"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
            <nav className="px-3 py-4">
              <ul className="flex flex-col gap-1">
                {navItems.map((item) => {
                  const isActive = pathname === item.href
                  return (
                    <li key={item.href}>
                      <Link
                        href={item.href}
                        onClick={() => setOpen(false)}
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
          </div>
        </div>
      )}
    </>
  )
}
