"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
} from "recharts"

const weekData = [
  { day: "Seg", mensagens: 42 },
  { day: "Ter", mensagens: 56 },
  { day: "Qua", mensagens: 38 },
  { day: "Qui", mensagens: 65 },
  { day: "Sex", mensagens: 48 },
  { day: "Sab", mensagens: 22 },
  { day: "Dom", mensagens: 12 },
]

const CHART_COLOR = "#0ea5e9"

export function WeeklyChart() {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base font-semibold">Mensagens por Dia da Semana</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[280px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={weekData} barCategoryGap="20%">
              <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" vertical={false} />
              <XAxis
                dataKey="day"
                tickLine={false}
                axisLine={false}
                fontSize={12}
                stroke="hsl(var(--muted-foreground))"
              />
              <YAxis
                tickLine={false}
                axisLine={false}
                fontSize={12}
                stroke="hsl(var(--muted-foreground))"
              />
              <Tooltip
                cursor={{ fill: "hsl(var(--muted))", opacity: 0.5 }}
                contentStyle={{
                  backgroundColor: "hsl(var(--card))",
                  border: "1px solid hsl(var(--border))",
                  borderRadius: "8px",
                  fontSize: "12px",
                }}
                labelStyle={{ color: "hsl(var(--foreground))", fontWeight: 600 }}
              />
              <Bar
                dataKey="mensagens"
                fill={CHART_COLOR}
                radius={[6, 6, 0, 0]}
                name="Mensagens"
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </CardContent>
    </Card>
  )
}
