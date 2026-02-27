"use client"

import { MessageSquare, Users, TrendingUp, Clock } from "lucide-react"
import type { DashboardStats } from "@/lib/api"

interface StatsCardsProps {
  stats: DashboardStats
}

const cards = [
  {
    title: "Mensagens Enviadas",
    key: "mensagens_enviadas" as const,
    icon: MessageSquare,
    format: (v: number) => v.toLocaleString("pt-BR"),
    subKey: "mensagens_hoje" as const,
    subLabel: "hoje",
    iconColor: "#0ea5e9",
    iconBg: "rgba(14,165,233,0.1)",
  },
  {
    title: "Pacientes Atendidos",
    key: "pacientes_atendidos" as const,
    icon: Users,
    format: (v: number) => v.toLocaleString("pt-BR"),
    subKey: null,
    subLabel: "este mes",
    iconColor: "#10b981",
    iconBg: "rgba(16,185,129,0.1)",
  },
  {
    title: "Taxa de Conversao",
    key: "taxa_conversao" as const,
    icon: TrendingUp,
    format: (v: number) => `${v}%`,
    subKey: null,
    subLabel: "de leads convertidos",
    iconColor: "#0ea5e9",
    iconBg: "rgba(14,165,233,0.1)",
  },
  {
    title: "Tempo Medio de Resposta",
    key: "tempo_medio_resposta" as const,
    icon: Clock,
    format: (v: string) => v,
    subKey: null,
    subLabel: "media geral",
    iconColor: "#10b981",
    iconBg: "rgba(16,185,129,0.1)",
  },
]

export function StatsCards({ stats }: StatsCardsProps) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {cards.map((card) => {
        const value = stats[card.key]
        const formattedValue =
          typeof value === "number"
            ? (card.format as (v: number) => string)(value)
            : (card.format as (v: string) => string)(value as string)

        return (
          <div key={card.key} className="rounded-xl border border-border bg-card p-6">
            <div className="flex items-center justify-between pb-2">
              <p className="text-sm font-medium text-muted-foreground">
                {card.title}
              </p>
              <div
                className="flex h-9 w-9 items-center justify-center rounded-lg"
                style={{ backgroundColor: card.iconBg }}
              >
                <card.icon className="h-4 w-4" style={{ color: card.iconColor }} />
              </div>
            </div>
            <div className="text-2xl font-bold text-card-foreground">{formattedValue}</div>
            <p className="mt-1 text-xs text-muted-foreground">
              {card.subKey && stats[card.subKey] !== undefined && (
                <span className="font-semibold text-primary">
                  {String(stats[card.subKey])}{" "}
                </span>
              )}
              {card.subLabel}
            </p>
          </div>
        )
      })}
    </div>
  )
}
