"use client"

import { useState } from "react"
import { Search, Filter, MessageSquare } from "lucide-react"
import { ConversationCard } from "@/components/conversation-card"
import { cn } from "@/lib/utils"

const conversations = [
  {
    name: "Maria Silva",
    initials: "MS",
    lastMessage: "Gostaria de saber sobre clareamento dental. Qual o valor?",
    time: "2 min",
    status: "bot" as const,
    unread: 3,
    phone: "+55 11 98765-4321",
  },
  {
    name: "Joao Pedro Santos",
    initials: "JP",
    lastMessage: "Ok, vou comparecer na data agendada. Obrigado!",
    time: "15 min",
    status: "bot" as const,
    unread: 0,
    phone: "+55 21 99876-5432",
  },
  {
    name: "Ana Costa",
    initials: "AC",
    lastMessage: "Preciso remarcar minha consulta de amanha",
    time: "32 min",
    status: "humano" as const,
    unread: 1,
    phone: "+55 31 97654-3210",
  },
  {
    name: "Carlos Lima",
    initials: "CL",
    lastMessage: "Estou com muita dor de dente, tem horario hoje?",
    time: "1h",
    status: "humano" as const,
    unread: 5,
    phone: "+55 11 96543-2109",
  },
  {
    name: "Fernanda Oliveira",
    initials: "FO",
    lastMessage: "Vou verificar se meu plano cobre esse procedimento",
    time: "1h 20min",
    status: "bot" as const,
    unread: 0,
    phone: "+55 41 95432-1098",
  },
  {
    name: "Lucas Mendes",
    initials: "LM",
    lastMessage: "Qual a forma de pagamento? Aceitam parcelamento?",
    time: "2h",
    status: "bot" as const,
    unread: 2,
    phone: "+55 51 94321-0987",
  },
  {
    name: "Patricia Souza",
    initials: "PS",
    lastMessage: "Meu filho de 5 anos precisa de uma avaliacao",
    time: "3h",
    status: "bot" as const,
    unread: 0,
    phone: "+55 71 93210-9876",
  },
  {
    name: "Ricardo Ferreira",
    initials: "RF",
    lastMessage: "Obrigado pelo atendimento! Muito satisfeito.",
    time: "4h",
    status: "humano" as const,
    unread: 0,
    phone: "+55 61 92109-8765",
  },
]

type FilterType = "todas" | "bot" | "humano"

export default function ConversasPage() {
  const [filter, setFilter] = useState<FilterType>("todas")
  const [search, setSearch] = useState("")

  const filtered = conversations.filter((c) => {
    const matchFilter =
      filter === "todas" || c.status === filter
    const matchSearch =
      search === "" ||
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      c.lastMessage.toLowerCase().includes(search.toLowerCase())
    return matchFilter && matchSearch
  })

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm text-muted-foreground">
            {conversations.length} conversas ativas
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              placeholder="Buscar conversa..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="h-9 w-64 rounded-lg border border-border bg-secondary pl-9 pr-4 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>

          <div className="flex items-center rounded-lg border border-border bg-secondary p-0.5">
            {(
              [
                { value: "todas", label: "Todas" },
                { value: "bot", label: "Bot" },
                { value: "humano", label: "Humano" },
              ] as { value: FilterType; label: string }[]
            ).map((f) => (
              <button
                key={f.value}
                type="button"
                onClick={() => setFilter(f.value)}
                className={cn(
                  "flex items-center gap-1.5 rounded-md px-3 py-1.5 text-xs font-medium transition-colors",
                  filter === f.value
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:text-foreground"
                )}
              >
                {f.value === "todas" && <Filter className="h-3 w-3" />}
                {f.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      <div className="flex flex-col gap-3">
        {filtered.length > 0 ? (
          filtered.map((conversation, index) => (
            <ConversationCard key={index} {...conversation} />
          ))
        ) : (
          <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-border bg-card py-16">
            <MessageSquare className="h-10 w-10 text-muted-foreground" />
            <p className="text-sm text-muted-foreground">
              Nenhuma conversa encontrada
            </p>
          </div>
        )}
      </div>
    </div>
  )
}
