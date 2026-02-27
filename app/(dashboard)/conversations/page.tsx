"use client"

import { useState } from "react"
import useSWR from "swr"
import { fetchConversations, takeOverConversation, releaseConversation } from "@/lib/api"
import type { Conversation } from "@/lib/api"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Input } from "@/components/ui/input"
import { Bot, User, Search, PhoneForwarded, PhoneOff } from "lucide-react"
import { useToast } from "@/hooks/use-toast"

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

const avatarColors = [
  "bg-primary/15 text-primary",
  "bg-accent/15 text-accent",
  "bg-chart-3/15 text-chart-3",
  "bg-chart-4/15 text-chart-4",
  "bg-chart-5/15 text-chart-5",
]

export default function ConversationsPage() {
  const { data: conversations, isLoading, mutate } = useSWR("conversations", fetchConversations, {
    refreshInterval: 10000,
  })
  const [searchQuery, setSearchQuery] = useState("")
  const [loadingPhone, setLoadingPhone] = useState<string | null>(null)
  const { toast } = useToast()

  async function handleTakeOver(phone: string) {
    setLoadingPhone(phone)
    try {
      const result = await takeOverConversation(phone)
      toast({ title: "Conversa assumida", description: result.message })
      mutate()
    } finally {
      setLoadingPhone(null)
    }
  }

  async function handleRelease() {
    try {
      const result = await releaseConversation()
      toast({ title: "Bot reativado", description: result.message })
      mutate()
    } catch {
      toast({ title: "Erro", description: "Nao foi possivel reativar o bot", variant: "destructive" })
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
        <Button variant="outline" size="sm" onClick={handleRelease}>
          <PhoneOff className="mr-1.5 h-3.5 w-3.5" />
          Reativar Bot
        </Button>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Buscar por nome, telefone ou mensagem..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="pl-9"
        />
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base font-semibold">
            {filtered.length} conversa{filtered.length !== 1 ? "s" : ""}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
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

                return (
                  <div
                    key={conv.phone}
                    className="flex items-center gap-4 px-6 py-4 transition-colors hover:bg-muted/50"
                  >
                    <Avatar className="h-11 w-11 shrink-0">
                      <AvatarFallback
                        className={avatarColors[i % avatarColors.length] + " text-xs font-semibold"}
                      >
                        {initials}
                      </AvatarFallback>
                    </Avatar>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-0.5">
                        <span className="text-sm font-medium">{name}</span>
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
                        <Button
                          variant="outline"
                          size="sm"
                          className="h-8 text-xs"
                          onClick={() => handleTakeOver(conv.phone)}
                          disabled={isProcessing}
                        >
                          <PhoneForwarded className="mr-1 h-3.5 w-3.5" />
                          {isProcessing ? "Assumindo..." : "Assumir"}
                        </Button>
                      ) : (
                        <Badge variant="outline" className="text-xs text-accent border-accent/30">
                          Atendimento humano
                        </Badge>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
