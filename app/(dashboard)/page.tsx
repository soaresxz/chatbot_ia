"use client"

import useSWR from "swr"
import { fetchStats, fetchConversations } from "@/lib/api"
import { StatsCards } from "@/components/stats-cards"
import { RecentConversations } from "@/components/recent-conversations"
import { WeeklyChart } from "@/components/weekly-chart"

function StatsLoading() {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {Array.from({ length: 4 }).map((_, i) => (
        <div key={i} className="rounded-xl border border-border bg-card p-6 animate-pulse">
          <div className="h-4 w-32 rounded bg-muted mb-4" />
          <div className="h-8 w-20 rounded bg-muted mb-2" />
          <div className="h-3 w-24 rounded bg-muted" />
        </div>
      ))}
    </div>
  )
}

function ConversationsLoading() {
  return (
    <div className="rounded-xl border border-border bg-card">
      <div className="p-6 pb-4">
        <div className="h-5 w-40 rounded bg-muted animate-pulse" />
      </div>
      <div className="divide-y divide-border">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="flex items-center gap-4 px-6 py-4 animate-pulse">
            <div className="h-10 w-10 rounded-full bg-muted" />
            <div className="flex-1">
              <div className="h-4 w-28 rounded bg-muted mb-2" />
              <div className="h-3 w-48 rounded bg-muted" />
            </div>
            <div className="h-8 w-28 rounded bg-muted" />
          </div>
        ))}
      </div>
    </div>
  )
}

export default function OverviewPage() {
  const { data: stats, isLoading: statsLoading } = useSWR("stats", fetchStats, {
    refreshInterval: 30000,
  })
  const { data: conversations, isLoading: convsLoading } = useSWR(
    "conversations",
    fetchConversations,
    { refreshInterval: 10000 }
  )

  return (
    <div className="flex flex-col gap-6">
      {statsLoading || !stats ? <StatsLoading /> : <StatsCards stats={stats} />}

      <div className="grid gap-6 xl:grid-cols-5">
        <div className="xl:col-span-3">
          {convsLoading || !conversations ? (
            <ConversationsLoading />
          ) : (
            <RecentConversations conversations={conversations} />
          )}
        </div>
        <div className="xl:col-span-2">
          <WeeklyChart />
        </div>
      </div>
    </div>
  )
}
