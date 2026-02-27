"use client"

import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Legend,
} from "recharts"
import {
  Download,
  TrendingUp,
  TrendingDown,
  Calendar,
} from "lucide-react"

const monthlyData = [
  { mes: "Jan", atendimentos: 220, agendamentos: 145, conversoes: 98 },
  { mes: "Fev", atendimentos: 280, agendamentos: 178, conversoes: 125 },
  { mes: "Mar", atendimentos: 310, agendamentos: 195, conversoes: 140 },
  { mes: "Abr", atendimentos: 350, agendamentos: 210, conversoes: 162 },
  { mes: "Mai", atendimentos: 290, agendamentos: 185, conversoes: 130 },
  { mes: "Jun", atendimentos: 380, agendamentos: 240, conversoes: 185 },
]

const categoryData = [
  { name: "Agendamento", value: 35, color: "#14b8a6" },
  { name: "Duvidas", value: 28, color: "#10b981" },
  { name: "Precos", value: 20, color: "#06b6d4" },
  { name: "Emergencia", value: 10, color: "#f59e0b" },
  { name: "Outros", value: 7, color: "#8b5cf6" },
]

const weeklyTrend = [
  { semana: "Sem 1", resolucao: 82, satisfacao: 4.5 },
  { semana: "Sem 2", resolucao: 85, satisfacao: 4.6 },
  { semana: "Sem 3", resolucao: 88, satisfacao: 4.7 },
  { semana: "Sem 4", resolucao: 91, satisfacao: 4.8 },
]

const reportCards = [
  {
    title: "Total de Atendimentos",
    value: "1.830",
    change: "+18%",
    trend: "up" as const,
  },
  {
    title: "Agendamentos via IA",
    value: "1.153",
    change: "+24%",
    trend: "up" as const,
  },
  {
    title: "Taxa de Resolucao",
    value: "89%",
    change: "+5%",
    trend: "up" as const,
  },
  {
    title: "Transferencias p/ Humano",
    value: "11%",
    change: "-3%",
    trend: "down" as const,
  },
]

function ChartTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean
  payload?: Array<{ value: number; dataKey: string; color: string }>
  label?: string
}) {
  if (active && payload && payload.length) {
    return (
      <div className="rounded-lg border border-border bg-card p-3 shadow-lg">
        <p className="mb-1.5 text-sm font-medium text-foreground">{label}</p>
        {payload.map((entry) => (
          <p key={entry.dataKey} className="text-xs text-muted-foreground">
            <span
              className="mr-2 inline-block h-2 w-2 rounded-full"
              style={{ backgroundColor: entry.color }}
            />
            {entry.dataKey}: <span className="font-medium text-foreground">{entry.value}</span>
          </p>
        ))}
      </div>
    )
  }
  return null
}

export default function RelatoriosPage() {
  return (
    <div className="flex flex-col gap-6">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-muted-foreground">
            Dados dos ultimos 6 meses
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button
            type="button"
            className="flex items-center gap-2 rounded-lg border border-border bg-secondary px-4 py-2 text-sm font-medium text-foreground transition-colors hover:bg-muted"
          >
            <Calendar className="h-4 w-4" />
            Ultimo Semestre
          </button>
          <button
            type="button"
            className="flex items-center gap-2 rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-colors hover:bg-primary/90"
          >
            <Download className="h-4 w-4" />
            Exportar PDF
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {reportCards.map((card) => (
          <div
            key={card.title}
            className="rounded-xl border border-border bg-card p-5"
          >
            <p className="text-sm font-medium text-muted-foreground">
              {card.title}
            </p>
            <div className="mt-2 flex items-baseline gap-2">
              <p className="text-2xl font-bold text-card-foreground tracking-tight">
                {card.value}
              </p>
              <span className={`flex items-center gap-0.5 text-xs font-medium ${card.trend === "up" ? "text-accent" : "text-destructive"}`}>
                {card.trend === "up" ? (
                  <TrendingUp className="h-3 w-3" />
                ) : (
                  <TrendingDown className="h-3 w-3" />
                )}
                {card.change}
              </span>
            </div>
          </div>
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <div className="rounded-xl border border-border bg-card p-5 xl:col-span-2">
          <h3 className="mb-1 text-base font-semibold text-card-foreground">
            Atendimentos Mensais
          </h3>
          <p className="mb-6 text-sm text-muted-foreground">
            Comparativo de atendimentos, agendamentos e conversoes
          </p>
          <div className="h-72">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={monthlyData} barGap={4}>
                <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
                <XAxis dataKey="mes" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                <Tooltip content={<ChartTooltip />} />
                <Bar dataKey="atendimentos" fill="#14b8a6" radius={[4, 4, 0, 0]} />
                <Bar dataKey="agendamentos" fill="#10b981" radius={[4, 4, 0, 0]} />
                <Bar dataKey="conversoes" fill="#06b6d4" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 flex items-center justify-center gap-6">
            <div className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full bg-primary" />
              <span className="text-xs text-muted-foreground">Atendimentos</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full bg-accent" />
              <span className="text-xs text-muted-foreground">Agendamentos</span>
            </div>
            <div className="flex items-center gap-1.5">
              <span className="h-2.5 w-2.5 rounded-full bg-chart-3" />
              <span className="text-xs text-muted-foreground">Conversoes</span>
            </div>
          </div>
        </div>

        <div className="rounded-xl border border-border bg-card p-5">
          <h3 className="mb-1 text-base font-semibold text-card-foreground">
            Categorias de Atendimento
          </h3>
          <p className="mb-6 text-sm text-muted-foreground">
            Distribuicao por tipo de solicitacao
          </p>
          <div className="h-56">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={categoryData}
                  cx="50%"
                  cy="50%"
                  innerRadius={55}
                  outerRadius={85}
                  paddingAngle={4}
                  dataKey="value"
                >
                  {categoryData.map((entry) => (
                    <Cell key={entry.name} fill={entry.color} />
                  ))}
                </Pie>
                <Tooltip
                  content={({ active, payload }) => {
                    if (active && payload && payload.length) {
                      const data = payload[0]
                      return (
                        <div className="rounded-lg border border-border bg-card p-3 shadow-lg">
                          <p className="text-sm font-medium text-foreground">
                            {data.name}
                          </p>
                          <p className="text-xs text-muted-foreground">
                            {data.value}% das conversas
                          </p>
                        </div>
                      )
                    }
                    return null
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-2 flex flex-col gap-2">
            {categoryData.map((cat) => (
              <div key={cat.name} className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span
                    className="h-2.5 w-2.5 rounded-full"
                    style={{ backgroundColor: cat.color }}
                  />
                  <span className="text-xs text-muted-foreground">{cat.name}</span>
                </div>
                <span className="text-xs font-medium text-card-foreground">
                  {cat.value}%
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="rounded-xl border border-border bg-card p-5">
        <h3 className="mb-1 text-base font-semibold text-card-foreground">
          Tendencia Semanal
        </h3>
        <p className="mb-6 text-sm text-muted-foreground">
          Evolucao da taxa de resolucao e satisfacao
        </p>
        <div className="h-64">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={weeklyTrend}>
              <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" vertical={false} />
              <XAxis dataKey="semana" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
              <YAxis yAxisId="left" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} domain={[75, 100]} />
              <YAxis yAxisId="right" orientation="right" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} domain={[4, 5]} />
              <Tooltip content={<ChartTooltip />} />
              <Legend
                formatter={(value: string) =>
                  value === "resolucao" ? "Taxa de Resolucao (%)" : "Satisfacao"
                }
                wrapperStyle={{ fontSize: "12px", color: "#94a3b8" }}
              />
              <Line yAxisId="left" type="monotone" dataKey="resolucao" stroke="#14b8a6" strokeWidth={2} dot={{ r: 4, fill: "#14b8a6" }} />
              <Line yAxisId="right" type="monotone" dataKey="satisfacao" stroke="#10b981" strokeWidth={2} dot={{ r: 4, fill: "#10b981" }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
