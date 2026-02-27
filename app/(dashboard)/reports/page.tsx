"use client"

import useSWR from "swr"
import { fetchReports } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import {
  CalendarCheck,
  HelpCircle,
  XCircle,
  RefreshCw,
  Target,
  Smile,
  TrendingUp,
} from "lucide-react"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  AreaChart,
  Area,
  PieChart,
  Pie,
  Cell,
} from "recharts"
import { Skeleton } from "@/components/ui/skeleton"

const weekData = [
  { day: "Seg", mensagens: 42, resolvidas: 36 },
  { day: "Ter", mensagens: 56, resolvidas: 48 },
  { day: "Qua", mensagens: 38, resolvidas: 31 },
  { day: "Qui", mensagens: 65, resolvidas: 55 },
  { day: "Sex", mensagens: 48, resolvidas: 42 },
  { day: "Sab", mensagens: 22, resolvidas: 20 },
  { day: "Dom", mensagens: 12, resolvidas: 11 },
]

const monthTrend = [
  { week: "Sem 1", agendamentos: 28, duvidas: 52 },
  { week: "Sem 2", agendamentos: 35, duvidas: 68 },
  { week: "Sem 3", agendamentos: 42, duvidas: 75 },
  { week: "Sem 4", agendamentos: 51, duvidas: 94 },
]

const CHART_PRIMARY = "#0ea5e9"
const CHART_ACCENT = "#10b981"

const satisfactionData = [
  { name: "Muito Satisfeito", value: 52, color: "#10b981" },
  { name: "Satisfeito", value: 30, color: "#0ea5e9" },
  { name: "Neutro", value: 12, color: "#f59e0b" },
  { name: "Insatisfeito", value: 6, color: "#ef4444" },
]

function ReportCardLoading() {
  return (
    <div className="rounded-xl border border-border bg-card p-6">
      <Skeleton className="h-4 w-32 mb-4" />
      <Skeleton className="h-8 w-20 mb-2" />
      <Skeleton className="h-3 w-24" />
    </div>
  )
}

export default function ReportsPage() {
  const { data: reports, isLoading } = useSWR("reports", fetchReports, {
    refreshInterval: 60000,
  })

  const reportCards = reports
    ? [
        {
          title: "Agendamentos pela IA",
          value: reports.agendamentos_pela_ia,
          icon: CalendarCheck,
          color: "text-primary",
          bgColor: "bg-primary/10",
          badge: reports.taxa_sucesso_agendamento,
          badgeLabel: "taxa de sucesso",
        },
        {
          title: "Duvidas Resolvidas sem Humano",
          value: reports.duvidas_resolvidas_sem_humano,
          icon: HelpCircle,
          color: "text-accent",
          bgColor: "bg-accent/10",
          badge: reports.taxa_sucesso_duvidas,
          badgeLabel: "resolvidas automaticamente",
        },
        {
          title: "Cancelamentos Processados",
          value: reports.cancelamentos_processados,
          icon: XCircle,
          color: "text-chart-5",
          bgColor: "bg-chart-5/10",
          badge: null,
          badgeLabel: "este mes",
        },
        {
          title: "Reagendamentos Automaticos",
          value: reports.reagendamentos_automaticos,
          icon: RefreshCw,
          color: "text-chart-3",
          bgColor: "bg-chart-3/10",
          badge: null,
          badgeLabel: "este mes",
        },
        {
          title: "Taxa de Sucesso",
          value: reports.taxa_sucesso_agendamento,
          icon: Target,
          color: "text-primary",
          bgColor: "bg-primary/10",
          badge: null,
          badgeLabel: "agendamentos confirmados",
        },
        {
          title: "Satisfacao dos Pacientes",
          value: "82%",
          icon: Smile,
          color: "text-accent",
          bgColor: "bg-accent/10",
          badge: null,
          badgeLabel: "muito satisfeitos ou satisfeitos",
        },
      ]
    : []

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-xl font-semibold">Relatorios</h2>
        <p className="text-sm text-muted-foreground">
          Acompanhe o desempenho da IA no atendimento da sua clinica
        </p>
      </div>

      {/* Report Cards */}
      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {isLoading
          ? Array.from({ length: 6 }).map((_, i) => <ReportCardLoading key={i} />)
          : reportCards.map((card) => (
              <Card key={card.title} className="relative overflow-hidden">
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <CardTitle className="text-sm font-medium text-muted-foreground">
                    {card.title}
                  </CardTitle>
                  <div
                    className={`flex h-9 w-9 items-center justify-center rounded-lg ${card.bgColor}`}
                  >
                    <card.icon className={`h-4.5 w-4.5 ${card.color}`} />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="flex items-center gap-2">
                    <span className="text-2xl font-bold">
                      {typeof card.value === "number" ? card.value.toLocaleString("pt-BR") : card.value}
                    </span>
                    {card.badge && (
                      <Badge variant="secondary" className="text-xs">
                        <TrendingUp className="mr-0.5 h-3 w-3" />
                        {card.badge}
                      </Badge>
                    )}
                  </div>
                  <p className="mt-1 text-xs text-muted-foreground">{card.badgeLabel}</p>
                </CardContent>
              </Card>
            ))}
      </div>

      {/* Charts */}
      <div className="grid gap-6 xl:grid-cols-2">
        {/* Weekly Bar Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-semibold">
              Mensagens vs Resolvidas por Dia
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={weekData} barCategoryGap="20%">
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                  <XAxis
                    dataKey="day"
                    tickLine={false}
                    axisLine={false}
                    fontSize={12}
                    stroke="hsl(var(--muted-foreground))"
                  />
                  <YAxis
                    tickLine={false}
                    axisLine={false}
                    fontSize={12}
                    stroke="hsl(var(--muted-foreground))"
                  />
                  <Tooltip
                    cursor={{ fill: "hsl(var(--muted))", opacity: 0.5 }}
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "8px",
                      fontSize: "12px",
                    }}
                    labelStyle={{ color: "hsl(var(--foreground))", fontWeight: 600 }}
                  />
                  <Bar dataKey="mensagens" fill={CHART_PRIMARY} radius={[6, 6, 0, 0]} name="Mensagens" />
                  <Bar dataKey="resolvidas" fill={CHART_ACCENT} radius={[6, 6, 0, 0]} name="Resolvidas" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>

        {/* Monthly Trend Area Chart */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base font-semibold">
              Tendencia Mensal
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={monthTrend}>
                  <defs>
                    <linearGradient id="colorAgendamentos" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={CHART_PRIMARY} stopOpacity={0.3} />
                      <stop offset="95%" stopColor={CHART_PRIMARY} stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="colorDuvidas" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={CHART_ACCENT} stopOpacity={0.3} />
                      <stop offset="95%" stopColor={CHART_ACCENT} stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
                  <XAxis
                    dataKey="week"
                    tickLine={false}
                    axisLine={false}
                    fontSize={12}
                    stroke="hsl(var(--muted-foreground))"
                  />
                  <YAxis
                    tickLine={false}
                    axisLine={false}
                    fontSize={12}
                    stroke="hsl(var(--muted-foreground))"
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "8px",
                      fontSize: "12px",
                    }}
                    labelStyle={{ color: "hsl(var(--foreground))", fontWeight: 600 }}
                  />
                  <Area
                    type="monotone"
                    dataKey="agendamentos"
                    stroke={CHART_PRIMARY}
                    fill="url(#colorAgendamentos)"
                    strokeWidth={2}
                    name="Agendamentos"
                  />
                  <Area
                    type="monotone"
                    dataKey="duvidas"
                    stroke={CHART_ACCENT}
                    fill="url(#colorDuvidas)"
                    strokeWidth={2}
                    name="Duvidas Resolvidas"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Satisfaction Pie Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base font-semibold">
            Satisfacao dos Pacientes
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-col items-center gap-6 sm:flex-row sm:justify-center">
            <div className="h-[220px] w-[220px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={satisfactionData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={100}
                    paddingAngle={3}
                    dataKey="value"
                  >
                    {satisfactionData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "hsl(var(--card))",
                      border: "1px solid hsl(var(--border))",
                      borderRadius: "8px",
                      fontSize: "12px",
                    }}
                    formatter={(value: number) => [`${value}%`, ""]}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="flex flex-col gap-3">
              {satisfactionData.map((item) => (
                <div key={item.name} className="flex items-center gap-3">
                  <div
                    className="h-3 w-3 rounded-full shrink-0"
                    style={{ backgroundColor: item.color }}
                  />
                  <span className="text-sm">{item.name}</span>
                  <span className="text-sm font-semibold ml-auto">{item.value}%</span>
                </div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
