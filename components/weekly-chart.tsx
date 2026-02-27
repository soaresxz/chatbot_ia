"use client"

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

export function WeeklyChart() {
  return (
    <div className="rounded-xl border border-border bg-card">
      <div className="px-6 py-4 border-b border-border">
        <h3 className="text-base font-semibold text-card-foreground">Mensagens por Dia</h3>
      </div>
      <div className="p-6">
        <div className="h-[280px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart data={weekData} barCategoryGap="20%">
              <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
              <XAxis
                dataKey="day"
                tickLine={false}
                axisLine={false}
                fontSize={12}
                stroke="#64748b"
              />
              <YAxis
                tickLine={false}
                axisLine={false}
                fontSize={12}
                stroke="#64748b"
              />
              <Tooltip
                cursor={{ fill: "#f1f5f9", opacity: 0.5 }}
                contentStyle={{
                  backgroundColor: "#ffffff",
                  border: "1px solid #e2e8f0",
                  borderRadius: "8px",
                  fontSize: "12px",
                }}
                labelStyle={{ color: "#0f172a", fontWeight: 600 }}
              />
              <Bar
                dataKey="mensagens"
                fill="#0ea5e9"
                radius={[6, 6, 0, 0]}
                name="Mensagens"
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  )
}
