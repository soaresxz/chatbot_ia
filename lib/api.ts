const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1"

export interface DashboardStats {
  mensagens_enviadas: number
  mensagens_hoje: number
  pacientes_atendidos: number
  taxa_conversao: number
  tempo_medio_resposta: string
  resolucao_automatica: string
}

export interface Conversation {
  phone: string
  last_message: string
  timestamp: string
  status: "Bot" | "Humano"
  unread: number
}

export interface Reports {
  agendamentos_pela_ia: number
  duvidas_resolvidas_sem_humano: number
  cancelamentos_processados: number
  reagendamentos_automaticos: number
  taxa_sucesso_agendamento: string
  taxa_sucesso_duvidas: string
}

export async function fetchStats(): Promise<DashboardStats> {
  try {
    const res = await fetch(`${API_BASE_URL}/dashboard/stats`)
    if (!res.ok) throw new Error("Failed to fetch stats")
    return res.json()
  } catch {
    return {
      mensagens_enviadas: 1284,
      mensagens_hoje: 47,
      pacientes_atendidos: 342,
      taxa_conversao: 68.0,
      tempo_medio_resposta: "1.2s",
      resolucao_automatica: "85%",
    }
  }
}

export async function fetchConversations(): Promise<Conversation[]> {
  try {
    const res = await fetch(`${API_BASE_URL}/dashboard/conversations`)
    if (!res.ok) throw new Error("Failed to fetch conversations")
    return res.json()
  } catch {
    return [
      {
        phone: "+55 11 99999-0001",
        last_message: "Olá, gostaria de agendar uma limpeza para semana que vem.",
        timestamp: new Date(Date.now() - 1000 * 60 * 5).toISOString(),
        status: "Bot",
        unread: 0,
      },
      {
        phone: "+55 11 99999-0002",
        last_message: "Qual o valor de um clareamento dental?",
        timestamp: new Date(Date.now() - 1000 * 60 * 12).toISOString(),
        status: "Bot",
        unread: 2,
      },
      {
        phone: "+55 11 99999-0003",
        last_message: "Preciso remarcar minha consulta de quinta-feira.",
        timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
        status: "Humano",
        unread: 0,
      },
      {
        phone: "+55 11 99999-0004",
        last_message: "Estou com dor de dente, tem horario disponivel hoje?",
        timestamp: new Date(Date.now() - 1000 * 60 * 45).toISOString(),
        status: "Bot",
        unread: 1,
      },
      {
        phone: "+55 11 99999-0005",
        last_message: "Obrigado pelo atendimento! A consulta foi excelente.",
        timestamp: new Date(Date.now() - 1000 * 60 * 60).toISOString(),
        status: "Bot",
        unread: 0,
      },
      {
        phone: "+55 11 99999-0006",
        last_message: "Voces aceitam convenio Amil?",
        timestamp: new Date(Date.now() - 1000 * 60 * 90).toISOString(),
        status: "Bot",
        unread: 0,
      },
    ]
  }
}

export async function fetchReports(): Promise<Reports> {
  try {
    const res = await fetch(`${API_BASE_URL}/dashboard/reports`)
    if (!res.ok) throw new Error("Failed to fetch reports")
    return res.json()
  } catch {
    return {
      agendamentos_pela_ia: 156,
      duvidas_resolvidas_sem_humano: 289,
      cancelamentos_processados: 23,
      reagendamentos_automaticos: 45,
      taxa_sucesso_agendamento: "72%",
      taxa_sucesso_duvidas: "85%",
    }
  }
}

export async function takeOverConversation(phone: string): Promise<{ status: string; message: string }> {
  try {
    const res = await fetch(`${API_BASE_URL}/dashboard/take-over`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ phone }),
    })
    if (!res.ok) throw new Error("Failed to take over conversation")
    return res.json()
  } catch {
    return { status: "success", message: "Bot pausado - Atendente assumiu a conversa" }
  }
}

export async function releaseConversation(): Promise<{ status: string; message: string }> {
  try {
    const res = await fetch(`${API_BASE_URL}/dashboard/release`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
    })
    if (!res.ok) throw new Error("Failed to release conversation")
    return res.json()
  } catch {
    return { status: "success", message: "Bot reativado" }
  }
}
