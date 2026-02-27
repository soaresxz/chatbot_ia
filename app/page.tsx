'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

export default function Dashboard() {
  const [stats, setStats] = useState({
    mensagens_enviadas: 0,
    pacientes_atendidos: 0,
    taxa_conversao: 0,
    tempo_medio: "0s"
  });

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch('http://localhost:8000/dashboard/stats')
      .then(res => res.json())
      .then(data => {
        setStats(data);
        setLoading(false);
      })
      .catch(err => {
        console.error("Erro ao carregar stats", err);
        setLoading(false);
      });
  }, []);

  if (loading) return <div className="p-8">Carregando dados...</div>;

  return (
    <div className="p-8">
      <h1 className="text-4xl font-bold mb-8">Visão Geral</h1>

      <div className="grid grid-cols-4 gap-6">
        <Card>
          <CardHeader><CardTitle>Mensagens Enviadas</CardTitle></CardHeader>
          <CardContent>
            <p className="text-5xl font-bold">{stats.mensagens_enviadas}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Pacientes Atendidos</CardTitle></CardHeader>
          <CardContent>
            <p className="text-5xl font-bold">{stats.pacientes_atendidos}</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Taxa de Conversão</CardTitle></CardHeader>
          <CardContent>
            <p className="text-5xl font-bold">{stats.taxa_conversao}%</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Tempo Médio de Resposta</CardTitle></CardHeader>
          <CardContent>
            <p className="text-5xl font-bold">{stats.tempo_medio}</p>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
