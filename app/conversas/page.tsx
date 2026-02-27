"use client"

import { useState, useCallback } from "react"
import useSWR from "swr"
import {
  Search,
  Filter,
  MessageSquare,
  RefreshCw,
  AlertCircle,
} from "lucide-react"
import { ConversationCard } from "@/components/conversation-card"
import { fetcher, API_BASE } from "@/lib/fetcher"
import type { Conversation } from "@/lib/types"
import { cn } from "@/lib/utils"

type FilterType = "todas" | "bot" | "humano"

export default function ConversasPage() {
  const [filter, setFilter] = useState<FilterType>("todas")
  const [search, setSearch] = useState("")

  const {
    data: conversations,
    error,
    isLoading,
    mutate,
  } = useSWR<Conversation[]>("/dashboard/conversations", fetcher, {
    refreshInterval: 10_000,
    revalidateOnFocus: true,
  })

  const handleTakeOver = useCallback(
    async (phone: string) => {
      const res = await fetch(`${API_BASE}/dashboard/take-over`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone }),
      })
      if (!res.ok) {
        throw new Error("Falha ao assumir conversa")
      }
      await mutate()
    },
    [mutate]
  )

  const filtered = (conversations ?? []).filter((c) => {
    const matchFilter = filter === "todas" || c.status === filter
    const matchSearch =
      search === "" ||
      c.name.toLowerCase().includes(search.toLowerCase()) ||
      c.lastMessage.toLowerCase().includes(search.toLowerCase()) ||
      c.phone.includes(search)
    return matchFilter && matchSearch
  })

  const totalConversations = conversations?.length ?? 0
  const botCount = conversations?.filter((c) => c.status === "bot").length ?? 0
  const humanCount =
    conversations?.filter((c) => c.status === "humano").length ?? 0

  return (
    <div className="flex flex-col gap-6">
      {/* Header com estatisticas rapidas */}
      <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-4">
          <p className="text-sm text-muted-foreground">
            <span className="font-semibold text-foreground">
              {totalConversations}
            </span>{" "}
            conversas ativas
          </p>
          <div className="hidden items-center gap-3 sm:flex">
            <span className="flex items-center gap-1.5 text-xs text-primary">
              <span className="h-2 w-2 rounded-full bg-primary" />
              {botCount} Bot
            </span>
            <span className="flex items-center gap-1.5 text-xs text-chart-5">
              <span className="h-2 w-2 rounded-full bg-chart-5" />
              {humanCount} Humano
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Busca */}
          <div className="relative">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              placeholder="Buscar por nome, telefone..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="h-9 w-72 rounded-lg border border-border bg-secondary pl-9 pr-4 text-sm text-foreground placeholder:text-muted-foreground focus:border-primary focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </div>

          {/* Filtro */}
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

          {/* Atualizar */}
          <button
            type="button"
            onClick={() => mutate()}
            className="flex h-9 w-9 items-center justify-center rounded-lg border border-border bg-secondary text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            aria-label="Atualizar conversas"
          >
            <RefreshCw className={cn("h-4 w-4", isLoading && "animate-spin")} />
          </button>
        </div>
      </div>

      {/* Estado de carregamento */}
      {isLoading && (
        <div className="flex flex-col gap-3">
          {Array.from({ length: 5 }).map((_, i) => (
            <div
              key={i}
              className="flex items-center gap-4 rounded-xl border border-border bg-card p-4"
            >
              <div className="h-12 w-12 animate-pulse rounded-full bg-secondary" />
              <div className="flex flex-1 flex-col gap-2">
                <div className="h-4 w-40 animate-pulse rounded bg-secondary" />
                <div className="h-3 w-28 animate-pulse rounded bg-secondary" />
                <div className="h-3 w-64 animate-pulse rounded bg-secondary" />
              </div>
              <div className="h-8 w-20 animate-pulse rounded-full bg-secondary" />
              <div className="h-10 w-36 animate-pulse rounded-lg bg-secondary" />
            </div>
          ))}
        </div>
      )}

      {/* Estado de erro */}
      {error && !isLoading && (
        <div className="flex flex-col items-center justify-center gap-4 rounded-xl border border-destructive/30 bg-destructive/5 py-16">
          <AlertCircle className="h-10 w-10 text-destructive" />
          <div className="text-center">
            <p className="text-sm font-medium text-destructive">
              Erro ao carregar conversas
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              Verifique se a API esta acessivel e tente novamente.
            </p>
          </div>
          <button
            type="button"
            onClick={() => mutate()}
            className="rounded-lg bg-destructive/10 px-4 py-2 text-sm font-medium text-destructive transition-colors hover:bg-destructive/20"
          >
            Tentar novamente
          </button>
        </div>
      )}

      {/* Lista de conversas */}
      {!isLoading && !error && (
        <div className="flex flex-col gap-3">
          {filtered.length > 0 ? (
            filtered.map((conversation) => (
              <ConversationCard
                key={conversation.id}
                {...conversation}
                onTakeOver={handleTakeOver}
              />
            ))
          ) : (
            <div className="flex flex-col items-center justify-center gap-3 rounded-xl border border-border bg-card py-16">
              <MessageSquare className="h-10 w-10 text-muted-foreground" />
              <p className="text-sm text-muted-foreground">
                {search || filter !== "todas"
                  ? "Nenhuma conversa encontrada com os filtros atuais"
                  : "Nenhuma conversa ativa no momento"}
              </p>
              {(search || filter !== "todas") && (
                <button
                  type="button"
                  onClick={() => {
                    setSearch("")
                    setFilter("todas")
                  }}
                  className="text-xs font-medium text-primary hover:underline"
                >
                  Limpar filtros
                </button>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
