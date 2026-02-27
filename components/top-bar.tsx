"use client"

import { usePathname } from "next/navigation"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { MobileNav } from "@/components/mobile-nav"
import { Moon, Sun, Sparkles, LogOut, Settings, User } from "lucide-react"
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
        <h1 className="hidden lg:block text-lg font-semibold">{pageTitle}</h1>
      </div>

      <p className="hidden md:block text-sm text-muted-foreground font-medium">
        Sua clinica no piloto automatico
      </p>

      <div className="flex items-center gap-2">
        <Button variant="outline" size="sm" asChild>
          <Link href="#plans">Ver Planos</Link>
        </Button>
        <Button size="sm" className="bg-primary text-primary-foreground hover:bg-primary/90">
          <Sparkles className="mr-1.5 h-3.5 w-3.5" />
          Acessar Dashboard
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="h-9 w-9"
          onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
          aria-label="Alternar tema"
        >
          <Sun className="h-4 w-4 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
          <Moon className="absolute h-4 w-4 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
        </Button>

        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" className="relative h-9 w-9 rounded-full">
              <Avatar className="h-9 w-9">
                <AvatarImage src="/placeholder-user.jpg" alt="Usuario" />
                <AvatarFallback className="bg-primary/10 text-primary text-xs font-semibold">DR</AvatarFallback>
              </Avatar>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="w-56" align="end">
            <div className="flex items-center gap-2 px-2 py-1.5">
              <Avatar className="h-8 w-8">
                <AvatarFallback className="bg-primary/10 text-primary text-xs">DR</AvatarFallback>
              </Avatar>
              <div className="flex flex-col">
                <p className="text-sm font-medium">Dr. Rodrigo</p>
                <p className="text-xs text-muted-foreground">dr@clinicai.com</p>
              </div>
            </div>
            <DropdownMenuSeparator />
            <DropdownMenuItem>
              <User className="mr-2 h-4 w-4" />
              Perfil
            </DropdownMenuItem>
            <DropdownMenuItem>
              <Settings className="mr-2 h-4 w-4" />
              Configuracoes
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem className="text-destructive">
              <LogOut className="mr-2 h-4 w-4" />
              Sair
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  )
}
