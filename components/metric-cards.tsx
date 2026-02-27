import { CalendarCheck, HelpCircle, Star, Clock } from "lucide-react"

const metrics = [
  {
    title: "Agendamentos pela IA",
    value: "142",
    description: "Consultas agendadas automaticamente",
    icon: CalendarCheck,
    color: "text-primary" as const,
    bgColor: "bg-primary/10" as const,
  },
  {
    title: "Duvidas Resolvidas",
    value: "89%",
    description: "Sem intervencao humana",
    icon: HelpCircle,
    color: "text-accent" as const,
    bgColor: "bg-accent/10" as const,
  },
  {
    title: "Satisfacao do Paciente",
    value: "4.8",
    description: "Nota media de avaliacao",
    icon: Star,
    color: "text-chart-5" as const,
    bgColor: "bg-chart-5/10" as const,
  },
  {
    title: "Tempo de Espera",
    value: "< 5s",
    description: "Primeira resposta do bot",
    icon: Clock,
    color: "text-chart-3" as const,
    bgColor: "bg-chart-3/10" as const,
  },
]

export function MetricCards() {
  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <h3 className="mb-4 text-base font-semibold text-card-foreground">
        Metricas de Performance
      </h3>
      <div className="flex flex-col gap-4">
        {metrics.map((metric) => (
          <div
            key={metric.title}
            className="flex items-center gap-4 rounded-lg bg-secondary/50 p-4"
          >
            <div
              className={`flex h-11 w-11 items-center justify-center rounded-lg ${metric.bgColor}`}
            >
              <metric.icon className={`h-5 w-5 ${metric.color}`} />
            </div>
            <div className="flex-1">
              <div className="flex items-baseline justify-between">
                <p className="text-sm font-medium text-card-foreground">
                  {metric.title}
                </p>
                <p className={`text-lg font-bold ${metric.color}`}>
                  {metric.value}
                </p>
              </div>
              <p className="text-xs text-muted-foreground">
                {metric.description}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
