"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
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
    color: "text-primary",
    bgColor: "bg-primary/10",
  },
  {
    title: "Pacientes Atendidos",
    key: "pacientes_atendidos" as const,
    icon: Users,
    format: (v: number) => v.toLocaleString("pt-BR"),
    subLabel: "este mes",
    color: "text-accent",
    bgColor: "bg-accent/10",
  },
  {
    title: "Taxa de Conversao",
    key: "taxa_conversao" as const,
    icon: TrendingUp,
    format: (v: number) => `${v}%`,
    subLabel: "de leads convertidos",
    color: "text-primary",
    bgColor: "bg-primary/10",
  },
  {
    title: "Tempo Medio de Resposta",
    key: "tempo_medio_resposta" as const,
    icon: Clock,
    format: (v: string) => v,
    subLabel: "media geral",
    color: "text-accent",
    bgColor: "bg-accent/10",
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
          <Card key={card.key} className="relative overflow-hidden">
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {card.title}
              </CardTitle>
              <div className={`flex h-9 w-9 items-center justify-center rounded-lg ${card.bgColor}`}>
                <card.icon className={`h-4.5 w-4.5 ${card.color}`} />
              </div>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{formattedValue}</div>
              <p className="mt-1 text-xs text-muted-foreground">
                {card.subKey && (
                  <span className={`font-semibold ${card.color}`}>
                    {stats[card.subKey]}{" "}
                  </span>
                )}
                {card.subLabel}
              </p>
            </CardContent>
          </Card>
        )
      })}
    </div>
  )
}
