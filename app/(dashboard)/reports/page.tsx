"use client"

import useSWR from "swr"
import { fetchReports } from "@/lib/api"
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

const satisfactionData = [
  { name: "Muito Satisfeito", value: 52, color: "#10b981" },
  { name: "Satisfeito", value: 30, color: "#0ea5e9" },
  { name: "Neutro", value: 12, color: "#f59e0b" },
  { name: "Insatisfeito", value: 6, color: "#ef4444" },
]

function ReportCardLoading() {
  return (
    <div className="rounded-xl border border-border bg-card p-6 animate-pulse">
      <div className="h-4 w-32 rounded bg-muted mb-4" />
      <div className="h-8 w-20 rounded bg-muted mb-2" />
      <div className="h-3 w-24 rounded bg-muted" />
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
          iconColor: "#0ea5e9",
          iconBg: "rgba(14,165,233,0.1)",
          badge: reports.taxa_sucesso_agendamento,
          badgeLabel: "taxa de sucesso",
        },
        {
          title: "Duvidas Resolvidas sem Humano",
          value: reports.duvidas_resolvidas_sem_humano,
          icon: HelpCircle,
          iconColor: "#10b981",
          iconBg: "rgba(16,185,129,0.1)",
          badge: reports.taxa_sucesso_duvidas,
          badgeLabel: "resolvidas automaticamente",
        },
        {
          title: "Cancelamentos Processados",
          value: reports.cancelamentos_processados,
          icon: XCircle,
          iconColor: "#ef4444",
          iconBg: "rgba(239,68,68,0.1)",
          badge: null,
          badgeLabel: "este mes",
        },
        {
          title: "Reagendamentos Automaticos",
          value: reports.reagendamentos_automaticos,
          icon: RefreshCw,
          iconColor: "#0ea5e9",
          iconBg: "rgba(14,165,233,0.1)",
          badge: null,
          badgeLabel: "este mes",
        },
        {
          title: "Taxa de Sucesso",
          value: reports.taxa_sucesso_agendamento,
          icon: Target,
          iconColor: "#10b981",
          iconBg: "rgba(16,185,129,0.1)",
          badge: null,
          badgeLabel: "agendamentos confirmados",
        },
        {
          title: "Satisfacao dos Pacientes",
          value: "82%",
          icon: Smile,
          iconColor: "#10b981",
          iconBg: "rgba(16,185,129,0.1)",
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

      <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
        {isLoading
          ? Array.from({ length: 6 }).map((_, i) => <ReportCardLoading key={i} />)
          : reportCards.map((card) => (
              <div key={card.title} className="rounded-xl border border-border bg-card p-6">
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
                <div className="flex items-center gap-2">
                  <span className="text-2xl font-bold text-card-foreground">
                    {typeof card.value === "number" ? card.value.toLocaleString("pt-BR") : card.value}
                  </span>
                  {card.badge && (
                    <span className="inline-flex items-center gap-0.5 rounded-full bg-secondary px-2 py-0.5 text-xs font-medium text-secondary-foreground">
                      <TrendingUp className="h-3 w-3" />
                      {card.badge}
                    </span>
                  )}
                </div>
                <p className="mt-1 text-xs text-muted-foreground">{card.badgeLabel}</p>
              </div>
            ))}
      </div>

      <div className="grid gap-6 xl:grid-cols-2">
        <div className="rounded-xl border border-border bg-card">
          <div className="px-6 py-4 border-b border-border">
            <h3 className="text-base font-semibold text-card-foreground">
              Mensagens vs Resolvidas por Dia
            </h3>
          </div>
          <div className="p-6">
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={weekData} barCategoryGap="20%">
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                  <XAxis dataKey="day" tickLine={false} axisLine={false} fontSize={12} stroke="#64748b" />
                  <YAxis tickLine={false} axisLine={false} fontSize={12} stroke="#64748b" />
                  <Tooltip
                    cursor={{ fill: "#f1f5f9", opacity: 0.5 }}
                    contentStyle={{ backgroundColor: "#fff", border: "1px solid #e2e8f0", borderRadius: "8px", fontSize: "12px" }}
                    labelStyle={{ color: "#0f172a", fontWeight: 600 }}
                  />
                  <Bar dataKey="mensagens" fill="#0ea5e9" radius={[6, 6, 0, 0]} name="Mensagens" />
                  <Bar dataKey="resolvidas" fill="#10b981" radius={[6, 6, 0, 0]} name="Resolvidas" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-border bg-card">
          <div className="px-6 py-4 border-b border-border">
            <h3 className="text-base font-semibold text-card-foreground">
              Tendencia Mensal
            </h3>
          </div>
          <div className="p-6">
            <div className="h-[300px] w-full">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={monthTrend}>
                  <defs>
                    <linearGradient id="colorAgendamentos" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} />
                    </linearGradient>
                    <linearGradient id="colorDuvidas" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10b981" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                  <XAxis dataKey="week" tickLine={false} axisLine={false} fontSize={12} stroke="#64748b" />
                  <YAxis tickLine={false} axisLine={false} fontSize={12} stroke="#64748b" />
                  <Tooltip
                    contentStyle={{ backgroundColor: "#fff", border: "1px solid #e2e8f0", borderRadius: "8px", fontSize: "12px" }}
                    labelStyle={{ color: "#0f172a", fontWeight: 600 }}
                  />
                  <Area type="monotone" dataKey="agendamentos" stroke="#0ea5e9" fill="url(#colorAgendamentos)" strokeWidth={2} name="Agendamentos" />
                  <Area type="monotone" dataKey="duvidas" stroke="#10b981" fill="url(#colorDuvidas)" strokeWidth={2} name="Duvidas Resolvidas" />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-border bg-card">
        <div className="px-6 py-4 border-b border-border">
          <h3 className="text-base font-semibold text-card-foreground">
            Satisfacao dos Pacientes
          </h3>
        </div>
        <div className="p-6">
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
                    contentStyle={{ backgroundColor: "#fff", border: "1px solid #e2e8f0", borderRadius: "8px", fontSize: "12px" }}
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
                  <span className="text-sm text-card-foreground">{item.name}</span>
                  <span className="text-sm font-semibold text-card-foreground ml-auto">{item.value}%</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
