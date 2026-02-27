"use client"

import { useState } from "react"
import useSWR from "swr"
import { cn } from "@/lib/utils"
import { fetchConversations, takeOverConversation, releaseConversation } from "@/lib/api"
import type { Conversation } from "@/lib/api"
import { Bot, User, Search, PhoneForwarded, PhoneOff } from "lucide-react"
import { toast } from "sonner"

const patientNames: Record<string, string> = {
  "+55 11 99999-0001": "Ana Silva",
  "+55 11 99999-0002": "Carlos Oliveira",
  "+55 11 99999-0003": "Maria Santos",
  "+55 11 99999-0004": "Pedro Costa",
  "+55 11 99999-0005": "Julia Ferreira",
  "+55 11 99999-0006": "Lucas Mendes",
}

function getInitials(name: string) {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2)
}

function formatTimestamp(timestamp: string) {
  const date = new Date(timestamp)
  return date.toLocaleString("pt-BR", {
    day: "2-digit",
    month: "short",
    hour: "2-digit",
    minute: "2-digit",
  })
}

const avatarBgs = [
  { bg: "bg-primary/15", text: "text-primary" },
  { bg: "bg-accent/15", text: "text-accent" },
  { bg: "bg-secondary", text: "text-secondary-foreground" },
  { bg: "bg-muted", text: "text-muted-foreground" },
]

export default function ConversationsPage() {
  const { data: conversations, isLoading, mutate } = useSWR("conversations", fetchConversations, {
    refreshInterval: 10000,
  })
  const [searchQuery, setSearchQuery] = useState("")
  const [loadingPhone, setLoadingPhone] = useState<string | null>(null)

  async function handleTakeOver(phone: string) {
    setLoadingPhone(phone)
    try {
      const result = await takeOverConversation(phone)
      toast.success("Conversa assumida", { description: result.message })
      mutate()
    } finally {
      setLoadingPhone(null)
    }
  }

  async function handleRelease() {
    try {
      const result = await releaseConversation()
      toast.success("Bot reativado", { description: result.message })
      mutate()
    } catch {
      toast.error("Erro", { description: "Nao foi possivel reativar o bot" })
    }
  }

  const filtered = (conversations || []).filter((conv: Conversation) => {
    const name = patientNames[conv.phone] || conv.phone
    const q = searchQuery.toLowerCase()
    return (
      name.toLowerCase().includes(q) ||
      conv.phone.includes(q) ||
      conv.last_message.toLowerCase().includes(q)
    )
  })

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h2 className="text-xl font-semibold">Conversas</h2>
          <p className="text-sm text-muted-foreground">
            Gerencie as conversas com seus pacientes
          </p>
        </div>
        <button
          onClick={handleRelease}
          className="inline-flex items-center gap-1.5 rounded-md border border-border px-3 py-2 text-sm font-medium hover:bg-muted transition-colors"
        >
          <PhoneOff className="h-3.5 w-3.5" />
          Reativar Bot
        </button>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <input
          type="text"
          placeholder="Buscar por nome, telefone ou mensagem..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full rounded-md border border-input bg-background px-3 py-2 pl-9 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2"
        />
      </div>

      <div className="rounded-xl border border-border bg-card">
        <div className="px-6 py-4 border-b border-border">
          <h3 className="text-base font-semibold text-card-foreground">
            {filtered.length} conversa{filtered.length !== 1 ? "s" : ""}
          </h3>
        </div>
        <div>
          {isLoading ? (
            <div className="flex items-center justify-center py-12">
              <p className="text-sm text-muted-foreground">Carregando conversas...</p>
            </div>
          ) : filtered.length === 0 ? (
            <div className="flex items-center justify-center py-12">
              <p className="text-sm text-muted-foreground">Nenhuma conversa encontrada</p>
            </div>
          ) : (
            <div className="divide-y divide-border">
              {filtered.map((conv: Conversation, i: number) => {
                const name = patientNames[conv.phone] || conv.phone
                const initials = patientNames[conv.phone]
                  ? getInitials(patientNames[conv.phone])
                  : "#"
                const isProcessing = loadingPhone === conv.phone
                const color = avatarBgs[i % avatarBgs.length]

                return (
                  <div
                    key={conv.phone}
                    className="flex items-center gap-4 px-6 py-4 transition-colors hover:bg-muted/50"
                  >
                    <div className={cn("flex h-11 w-11 shrink-0 items-center justify-center rounded-full text-xs font-semibold", color.bg, color.text)}>
                      {initials}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className="text-sm font-medium text-card-foreground">{name}</span>
                        <span
                          className={cn(
                            "inline-flex items-center gap-0.5 rounded-full px-2 py-0.5 text-[10px] font-medium shrink-0",
                            conv.status === "Bot"
                              ? "bg-secondary text-secondary-foreground"
                              : "border border-border text-muted-foreground"
                          )}
                        >
                          {conv.status === "Bot" ? (
                            <Bot className="h-3 w-3" />
                          ) : (
                            <User className="h-3 w-3" />
                          )}
                          {conv.status}
                        </span>
                        {conv.unread > 0 && (
                          <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-primary px-1 text-[10px] font-bold text-primary-foreground">
                            {conv.unread}
                          </span>
                        )}
                      </div>
                      <p className="text-xs text-muted-foreground truncate">{conv.last_message}</p>
                      <p className="mt-0.5 text-[11px] text-muted-foreground/60">
                        {conv.phone} - {formatTimestamp(conv.timestamp)}
                      </p>
                    </div>

                    <div className="shrink-0">
                      {conv.status === "Bot" ? (
                        <button
                          className="inline-flex items-center gap-1 rounded-md border border-border px-3 py-1.5 text-xs font-medium hover:bg-muted transition-colors disabled:opacity-50"
                          onClick={() => handleTakeOver(conv.phone)}
                          disabled={isProcessing}
                        >
                          <PhoneForwarded className="h-3.5 w-3.5" />
                          {isProcessing ? "Assumindo..." : "Assumir"}
                        </button>
                      ) : (
                        <span className="inline-flex items-center rounded-full border border-accent/30 px-2 py-0.5 text-xs text-accent font-medium">
                          Atendimento humano
                        </span>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
