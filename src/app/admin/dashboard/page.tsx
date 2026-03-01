"use client"

import { Building2, MessageSquare, Users, Zap } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

const stats = [
  { label: "Clinicas Ativas", value: "12", icon: Building2, change: "+2 este mes" },
  { label: "Conversas Hoje", value: "348", icon: MessageSquare, change: "+18% vs ontem" },
  { label: "Pacientes Atendidos", value: "1.245", icon: Users, change: "+156 esta semana" },
  { label: "Taxa de Automacao", value: "87%", icon: Zap, change: "+3% vs mes anterior" },
]

export default function AdminDashboardPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-balance">Dashboard</h1>
        <p className="text-muted-foreground">
          Visao geral da plataforma OdontoIA
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.label}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {stat.label}
              </CardTitle>
              <stat.icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stat.value}</div>
              <p className="text-xs text-primary">{stat.change}</p>
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  )
}
