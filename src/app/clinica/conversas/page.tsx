"use client"

import { useState } from "react"
import type { Conversation } from "@/lib/types"
import { ConversationList } from "@/components/clinic/conversation-list"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { MessageSquare, Search } from "lucide-react"

// Mock data for demonstration
const MOCK_CONVERSATIONS: Conversation[] = [
  {
    id: "1",
    patient_name: "Maria Silva",
    patient_phone: "+5511988887777",
    last_message: "Gostaria de agendar uma limpeza para a proxima semana",
    status: "ai_mode",
    updated_at: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
    unread_count: 2,
  },
  {
    id: "2",
    patient_name: "Joao Santos",
    patient_phone: "+5511977776666",
    last_message: "Estou com dor de dente forte, preciso de atendimento urgente",
    status: "ai_mode",
    updated_at: new Date(Date.now() - 1000 * 60 * 15).toISOString(),
    unread_count: 1,
  },
  {
    id: "3",
    patient_name: "Ana Oliveira",
    patient_phone: "+5511966665555",
    last_message: "Qual o valor da consulta de avaliacao?",
    status: "human_mode",
    updated_at: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
    unread_count: 0,
  },
  {
    id: "4",
    patient_name: "Carlos Lima",
    patient_phone: "+5511955554444",
    last_message: "Obrigado, vou confirmar o horario!",
    status: "ai_mode",
    updated_at: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
    unread_count: 0,
  },
  {
    id: "5",
    patient_name: "Fernanda Costa",
    patient_phone: "+5511944443333",
    last_message: "Preciso remarcar minha consulta de sexta",
    status: "ai_mode",
    updated_at: new Date(Date.now() - 1000 * 60 * 120).toISOString(),
    unread_count: 3,
  },
]

export default function ConversasPage() {
  const [conversations, setConversations] = useState(MOCK_CONVERSATIONS)
  const [search, setSearch] = useState("")

  const filtered = conversations.filter(
    (c) =>
      c.patient_name.toLowerCase().includes(search.toLowerCase()) ||
      c.patient_phone.includes(search) ||
      c.last_message.toLowerCase().includes(search.toLowerCase())
  )

  const aiCount = conversations.filter((c) => c.status === "ai_mode").length
  const humanCount = conversations.filter((c) => c.status === "human_mode").length

  function handleTakeOver(id: string) {
    setConversations((prev) =>
      prev.map((c) => (c.id === id ? { ...c, status: "human_mode" as const } : c))
    )
  }

  function handleReleaseToAi(id: string) {
    setConversations((prev) =>
      prev.map((c) => (c.id === id ? { ...c, status: "ai_mode" as const } : c))
    )
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight text-balance">Conversas</h1>
          <p className="text-muted-foreground">
            Gerencie as conversas do WhatsApp da sua clinica
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Badge variant="secondary" className="gap-1.5 px-3 py-1">
            <span className="h-2 w-2 rounded-full bg-primary" />
            IA: {aiCount}
          </Badge>
          <Badge variant="outline" className="gap-1.5 border-orange-500/30 px-3 py-1 text-orange-500">
            <span className="h-2 w-2 rounded-full bg-orange-500" />
            Humano: {humanCount}
          </Badge>
        </div>
      </div>

      <div className="relative">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <Input
          placeholder="Buscar conversa por nome, telefone ou mensagem..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="pl-10"
        />
      </div>

      {filtered.length === 0 ? (
        <div className="flex flex-col items-center justify-center gap-4 rounded-lg border border-dashed bg-card py-16">
          <div className="flex h-14 w-14 items-center justify-center rounded-full bg-muted">
            <MessageSquare className="h-6 w-6 text-muted-foreground" />
          </div>
          <div className="text-center">
            <h3 className="text-lg font-semibold">Nenhuma conversa encontrada</h3>
            <p className="text-sm text-muted-foreground">
              {search ? "Tente alterar os termos de busca" : "Quando pacientes entrarem em contato, as conversas aparecerão aqui"}
            </p>
          </div>
        </div>
      ) : (
        <ConversationList
          conversations={filtered}
          onTakeOver={handleTakeOver}
          onReleaseToAi={handleReleaseToAi}
        />
      )}
    </div>
  )
}
