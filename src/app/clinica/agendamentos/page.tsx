"use client"

import { Calendar } from "lucide-react"

export default function AgendamentosPage() {
  return (
    <div className="flex flex-col gap-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight text-balance">Agendamentos</h1>
        <p className="text-muted-foreground">
          Gerencie os agendamentos da sua clinica
        </p>
      </div>
      <div className="flex flex-col items-center justify-center gap-4 rounded-lg border border-dashed bg-card py-16">
        <div className="flex h-14 w-14 items-center justify-center rounded-full bg-muted">
          <Calendar className="h-6 w-6 text-muted-foreground" />
        </div>
        <div className="text-center">
          <h3 className="text-lg font-semibold">Em breve</h3>
          <p className="text-sm text-muted-foreground">
            Visualizacao de agendamentos sera implementada em breve.
          </p>
        </div>
      </div>
    </div>
  )
}
