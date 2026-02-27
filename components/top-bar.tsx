"use client"

import { usePathname } from "next/navigation"
import { MobileNav } from "@/components/mobile-nav"
import { Moon, Sun, Sparkles } from "lucide-react"
import { useTheme } from "next-themes"

export function TopBar() {
  const pathname = usePathname()
  const { theme, setTheme } = useTheme()

  const pageTitle =
    pathname === "/"
      ? "Visao Geral"
      : pathname === "/conversations"
      ? "Conversas"
      : pathname === "/reports"
      ? "Relatorios"
      : "Dashboard"

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b border-border bg-background/80 backdrop-blur-sm px-4 lg:px-8">
      <MobileNav />

      <div className="flex flex-1 items-center gap-4">
        <div className="lg:hidden flex items-center gap-2">
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-primary">
            <Sparkles className="h-4 w-4 text-primary-foreground" />
          </div>
          <span className="text-base font-semibold">ClinicAI</span>
        </div>
        <h1 className="hidden lg:block text-lg font-semibold text-balance">{pageTitle}</h1>
      </div>

      <p className="hidden md:block text-sm text-muted-foreground font-medium">
        Sua clinica no piloto automatico
      </p>

      <div className="flex items-center gap-2">
        <button
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          className="relative flex items-center justify-center h-9 w-9 rounded-md border border-border hover:bg-muted transition-colors"
          aria-label="Alternar tema"
        >
          <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
        </button>

        <div className="flex h-9 w-9 items-center justify-center rounded-full bg-primary/10 text-primary text-xs font-semibold">
          DR
        </div>
      </div>
    </header>
  )
}
