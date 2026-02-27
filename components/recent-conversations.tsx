"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
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

const avatarColors = [
  "bg-primary/15 text-primary",
  "bg-accent/15 text-accent",
  "bg-chart-3/15 text-chart-3",
  "bg-chart-4/15 text-chart-4",
  "bg-chart-5/15 text-chart-5",
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
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-base font-semibold">Conversas Recentes</CardTitle>
        <Button variant="ghost" size="sm" className="text-primary" asChild>
          <a href="/conversations">
            Ver todas
            <ArrowRight className="ml-1 h-3.5 w-3.5" />
          </a>
        </Button>
      </CardHeader>
      <CardContent className="p-0">
        <div className="divide-y divide-border">
          {conversations.slice(0, 5).map((conv, i) => {
            const name = patientNames[conv.phone] || conv.phone
            const initials = patientNames[conv.phone]
              ? getInitials(patientNames[conv.phone])
              : "#"
            const isLoading = loadingPhone === conv.phone

            return (
              <div
                key={conv.phone}
                className="flex items-center gap-4 px-6 py-4 transition-colors hover:bg-muted/50"
              >
                <Avatar className="h-10 w-10 shrink-0">
                  <AvatarFallback className={avatarColors[i % avatarColors.length] + " text-xs font-semibold"}>
                    {initials}
                  </AvatarFallback>
                </Avatar>

                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium truncate">{name}</span>
                    <Badge
                      variant={conv.status === "Bot" ? "secondary" : "outline"}
                      className="text-[10px] px-1.5 py-0 h-5 shrink-0"
                    >
                      {conv.status === "Bot" ? (
                        <Bot className="mr-0.5 h-3 w-3" />
                      ) : (
                        <User className="mr-0.5 h-3 w-3" />
                      )}
                      {conv.status}
                    </Badge>
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
                    <Button
                      variant="outline"
                      size="sm"
                      className="h-8 text-xs"
                      onClick={() => handleTakeOver(conv.phone)}
                      disabled={isLoading}
                    >
                      {isLoading ? "Assumindo..." : "Assumir Conversa"}
                    </Button>
                  )}
                </div>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
