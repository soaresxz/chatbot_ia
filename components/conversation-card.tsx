"use client"

import { useState } from "react"
import { Bot, UserRound, Loader2, Phone } from "lucide-react"
import { cn } from "@/lib/utils"
import type { Conversation } from "@/lib/types"

interface ConversationCardProps extends Conversation {
  onTakeOver: (phone: string) => Promise<void>
}

export function ConversationCard({
  name,
  initials,
  lastMessage,
  time,
  status,
  unread,
  phone,
  onTakeOver,
}: ConversationCardProps) {
  const [loading, setLoading] = useState(false)
  const [taken, setTaken] = useState(false)

  async function handleTakeOver() {
    setLoading(true)
    try {
      await onTakeOver(phone)
      setTaken(true)
    } catch {
      // erro tratado no pai
    } finally {
      setLoading(false)
    }
  }

  const isBot = status === "bot"

  return (
    <div
      className={cn(
        "group flex items-center gap-4 rounded-xl border bg-card p-4 transition-all",
        taken
          ? "border-accent/40 bg-accent/5"
          : "border-border hover:border-primary/30"
      )}
    >
      {/* Avatar */}
      <div className="relative shrink-0">
        <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary/15 text-sm font-bold text-primary">
          {initials}
        </div>
        <span
          className={cn(
            "absolute -bottom-0.5 -right-0.5 h-3.5 w-3.5 rounded-full border-2 border-card",
            isBot ? "bg-primary" : "bg-chart-5"
          )}
          aria-label={isBot ? "Atendido pelo Bot" : "Atendido por Humano"}
        />
      </div>

      {/* Info */}
      <div className="flex min-w-0 flex-1 flex-col gap-0.5">
        <div className="flex items-center justify-between gap-2">
          <h4 className="truncate text-sm font-semibold text-card-foreground">
            {name}
          </h4>
          <span className="shrink-0 text-xs text-muted-foreground">{time}</span>
        </div>
        <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
          <Phone className="h-3 w-3 shrink-0" />
          <span>{phone}</span>
        </div>
        <p className="mt-0.5 truncate text-sm text-muted-foreground/80">
          {lastMessage}
        </p>
      </div>

      {/* Status badge + unread */}
      <div className="flex shrink-0 flex-col items-end gap-2">
        <span
          className={cn(
            "flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-medium",
            isBot
              ? "bg-primary/10 text-primary"
              : "bg-chart-5/10 text-chart-5"
          )}
        >
          {isBot ? (
            <Bot className="h-3 w-3" />
          ) : (
            <UserRound className="h-3 w-3" />
          )}
          {isBot ? "Bot" : "Humano"}
        </span>

        {unread > 0 && (
          <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-primary px-1.5 text-[10px] font-bold text-primary-foreground">
            {unread}
          </span>
        )}
      </div>

      {/* Take over button */}
      {isBot && !taken && (
        <button
          type="button"
          disabled={loading}
          onClick={handleTakeOver}
          className="shrink-0 cursor-pointer rounded-lg bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? (
            <span className="flex items-center gap-2">
              <Loader2 className="h-4 w-4 animate-spin" />
              Assumindo...
            </span>
          ) : (
            "Assumir Conversa"
          )}
        </button>
      )}

      {isBot && taken && (
        <span className="shrink-0 rounded-lg border border-accent/30 bg-accent/10 px-4 py-2.5 text-sm font-semibold text-accent">
          Conversa Assumida
        </span>
      )}

      {!isBot && (
        <button
          type="button"
          className="shrink-0 cursor-pointer rounded-lg border border-border bg-secondary px-4 py-2.5 text-sm font-medium text-foreground transition-colors hover:bg-muted"
        >
          Ver Conversa
        </button>
      )}
    </div>
  )
}
