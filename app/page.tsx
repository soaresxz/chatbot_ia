import { MessageSquare, Users, TrendingUp, Timer } from "lucide-react"
import { StatCard } from "@/components/stat-card"
import { MessagesChart } from "@/components/messages-chart"
import { MetricCards } from "@/components/metric-cards"
import { RecentActivity } from "@/components/recent-activity"

const stats = [
  {
    title: "Mensagens Enviadas",
    value: "1.284",
    change: "+12.5%",
    changeType: "positive" as const,
    icon: MessageSquare,
  },
  {
    title: "Pacientes Atendidos",
    value: "348",
    change: "+8.2%",
    changeType: "positive" as const,
    icon: Users,
  },
  {
    title: "Taxa de Conversao",
    value: "68.4%",
    change: "+3.1%",
    changeType: "positive" as const,
    icon: TrendingUp,
  },
  {
    title: "Tempo Medio de Resposta",
    value: "1.2s",
    change: "-0.3s",
    changeType: "positive" as const,
    icon: Timer,
  },
]

export default function HomePage() {
  return (
    <div className="flex flex-col gap-6">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        {stats.map((stat) => (
          <StatCard key={stat.title} {...stat} />
        ))}
      </div>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        <div className="xl:col-span-2">
          <MessagesChart />
        </div>
        <div>
          <MetricCards />
        </div>
      </div>

      <RecentActivity />
    </div>
  )
}
