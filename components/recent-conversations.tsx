"use client"

import { useState } from "react"
import { cn } from "@/lib/utils"
import { Bot, User, ArrowRight } from "lucide-react"
import { takeOverConversation } from "@/lib/api"
import type { Conversation } from "@/lib/api"

interface RecentConversationsProps {
  conversations: Conversation[]
}

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

function formatTime(timestamp: string) {
  const date = new Date(timestamp)
  const now = new Date()
  const diffMin = Math.floor((now.getTime() - date.getTime()) / 60000)

  if (diffMin < 1) return "Agora"
  if (diffMin < 60) return `${diffMin}min`
  const diffHours = Math.floor(diffMin / 60)
  if (diffHours < 24) return `${diffHours}h`
  return date.toLocaleDateString("pt-BR", { day: "2-digit", month: "short" })
}

const avatarBgs = [
  { bg: "bg-primary/15", text: "text-primary" },
  { bg: "bg-accent/15", text: "text-accent" },
  { bg: "bg-secondary", text: "text-secondary-foreground" },
  { bg: "bg-muted", text: "text-muted-foreground" },
]

export function RecentConversations({ conversations }: RecentConversationsProps) {
  const [loadingPhone, setLoadingPhone] = useState<string | null>(null)

  async function handleTakeOver(phone: string) {
    setLoadingPhone(phone)
    try {
      await takeOverConversation(phone)
    } finally {
      setLoadingPhone(null)
    }
  }

  return (
    <div className="rounded-xl border border-border bg-card">
      <div className="flex items-center justify-between px-6 py-4 border-b border-border">
        <h3 className="text-base font-semibold text-card-foreground">Conversas Recentes</h3>
        <a
          href="/conversations"
          className="flex items-center gap-1 text-sm font-medium text-primary hover:text-primary/80 transition-colors"
        >
          Ver todas
          <ArrowRight className="h-3.5 w-3.5" />
        </a>
      </div>
      <div className="divide-y divide-border">
        {conversations.slice(0, 5).map((conv, i) => {
          const name = patientNames[conv.phone] || conv.phone
          const initials = patientNames[conv.phone]
            ? getInitials(patientNames[conv.phone])
            : "#"
          const isLoading = loadingPhone === conv.phone
          const color = avatarBgs[i % avatarBgs.length]

          return (
            <div
              key={conv.phone}
              className="flex items-center gap-4 px-6 py-4 transition-colors hover:bg-muted/50"
            >
              <div className={cn("flex h-10 w-10 shrink-0 items-center justify-center rounded-full text-xs font-semibold", color.bg, color.text)}>
                {initials}
              </div>

              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-card-foreground truncate">{name}</span>
                  <span
                    className={cn(
                      "inline-flex items-center gap-0.5 rounded-full px-2 py-0.5 text-[10px] font-medium",
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
                    <span className="flex h-5 w-5 items-center justify-center rounded-full bg-primary text-[10px] font-bold text-primary-foreground shrink-0">
                      {conv.unread}
                    </span>
                  )}
                </div>
                <p className="mt-0.5 text-xs text-muted-foreground truncate">
                  {conv.last_message}
                </p>
              </div>

              <div className="flex items-center gap-3 shrink-0">
                <span className="text-xs text-muted-foreground">{formatTime(conv.timestamp)}</span>
                {conv.status === "Bot" && (
                  <button
                    className="rounded-md border border-border px-3 py-1.5 text-xs font-medium text-card-foreground hover:bg-muted transition-colors disabled:opacity-50"
                    onClick={() => handleTakeOver(conv.phone)}
                    disabled={isLoading}
                  >
                    {isLoading ? "Assumindo..." : "Assumir"}
                  </button>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}
