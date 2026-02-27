"use client"

import { Bot, UserRound } from "lucide-react"
import { cn } from "@/lib/utils"

interface ConversationCardProps {
  name: string
  initials: string
  lastMessage: string
  time: string
  status: "bot" | "humano"
  unread?: number
  phone: string
}

export function ConversationCard({
  name,
  initials,
  lastMessage,
  time,
  status,
  unread,
  phone,
}: ConversationCardProps) {
  return (
    <div className="flex items-center gap-4 rounded-xl border border-border bg-card p-4 transition-colors hover:border-primary/30">
      <div className="relative">
        <div className="flex h-11 w-11 items-center justify-center rounded-full bg-primary/20 text-sm font-semibold text-primary">
          {initials}
        </div>
        <span
          className={cn(
            "absolute -bottom-0.5 -right-0.5 h-3.5 w-3.5 rounded-full border-2 border-card",
            status === "bot" ? "bg-primary" : "bg-chart-5"
          )}
        />
      </div>

      <div className="flex flex-1 flex-col overflow-hidden">
        <div className="flex items-center justify-between">
          <h4 className="text-sm font-semibold text-card-foreground">
            {name}
          </h4>
          <span className="text-xs text-muted-foreground">{time}</span>
        </div>
        <p className="text-xs text-muted-foreground">{phone}</p>
        <p className="mt-1 truncate text-sm text-muted-foreground">
          {lastMessage}
        </p>
      </div>

      <div className="flex flex-col items-end gap-2">
        <span
          className={cn(
            "flex items-center gap-1 rounded-full px-2.5 py-1 text-[11px] font-medium",
            status === "bot"
              ? "bg-primary/10 text-primary"
              : "bg-chart-5/10 text-chart-5"
          )}
        >
          {status === "bot" ? (
            <Bot className="h-3 w-3" />
          ) : (
            <UserRound className="h-3 w-3" />
          )}
          {status === "bot" ? "Bot" : "Humano"}
        </span>
        {unread && unread > 0 ? (
          <span className="flex h-5 min-w-5 items-center justify-center rounded-full bg-primary px-1 text-[10px] font-bold text-primary-foreground">
            {unread}
          </span>
        ) : null}
      </div>

      <button
        type="button"
        className={cn(
          "shrink-0 rounded-lg px-3 py-2 text-xs font-medium transition-colors",
          status === "bot"
            ? "border border-primary/30 bg-primary/10 text-primary hover:bg-primary/20"
            : "border border-chart-5/30 bg-chart-5/10 text-chart-5 hover:bg-chart-5/20"
        )}
      >
        {status === "bot" ? "Assumir Conversa" : "Ver Conversa"}
      </button>
    </div>
  )
}
