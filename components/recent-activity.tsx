import { MessageSquare, CalendarCheck, UserPlus, AlertCircle } from "lucide-react"
import { cn } from "@/lib/utils"

const activities = [
  {
    icon: MessageSquare,
    color: "text-primary",
    bg: "bg-primary/10",
    title: "Nova conversa iniciada",
    description: "Maria Silva enviou uma mensagem sobre clareamento dental",
    time: "2 min atras",
  },
  {
    icon: CalendarCheck,
    color: "text-accent",
    bg: "bg-accent/10",
    title: "Consulta agendada",
    description: "Joao Pedro agendou uma limpeza para 15/03/2026",
    time: "15 min atras",
  },
  {
    icon: UserPlus,
    color: "text-chart-3",
    bg: "bg-chart-3/10",
    title: "Novo paciente cadastrado",
    description: "Ana Costa foi registrada via chatbot do WhatsApp",
    time: "32 min atras",
  },
  {
    icon: AlertCircle,
    color: "text-chart-5",
    bg: "bg-chart-5/10",
    title: "Conversa transferida",
    description: "Bot transferiu conversa de Carlos Lima para atendente",
    time: "1h atras",
  },
  {
    icon: MessageSquare,
    color: "text-primary",
    bg: "bg-primary/10",
    title: "Duvida resolvida",
    description: "Fernanda Oliveira tirou duvida sobre valores de ortodontia",
    time: "1h 20min atras",
  },
]

export function RecentActivity() {
  return (
    <div className="rounded-xl border border-border bg-card p-5">
      <h3 className="mb-4 text-base font-semibold text-card-foreground">
        Atividade Recente
      </h3>
      <div className="flex flex-col gap-3">
        {activities.map((activity, index) => (
          <div
            key={index}
            className="flex items-start gap-3 rounded-lg p-3 transition-colors hover:bg-secondary/50"
          >
            <div
              className={cn(
                "mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg",
                activity.bg
              )}
            >
              <activity.icon className={cn("h-4 w-4", activity.color)} />
            </div>
            <div className="flex-1 overflow-hidden">
              <p className="text-sm font-medium text-card-foreground">
                {activity.title}
              </p>
              <p className="truncate text-xs text-muted-foreground">
                {activity.description}
              </p>
            </div>
            <span className="shrink-0 text-xs text-muted-foreground">
              {activity.time}
            </span>
          </div>
        ))}
      </div>
    </div>
  )
}
