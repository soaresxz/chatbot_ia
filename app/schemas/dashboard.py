from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class DashboardMetrics(BaseModel):
    agendamentos_hoje: int
    confirmados: int
    taxa_confirmacao: float
    faltas: int
    faturamento_projetado: float
    proximos_agendamentos: int
    mensagens_hoje: int

class DashboardResponse(BaseModel):
    metrics: DashboardMetrics
    proximos: List[dict] = []

class SuperAdminDashboard(BaseModel):
    total_clinicas: int
    clinicas_ativas: int
    agendamentos_mes: int
    receita_total: float