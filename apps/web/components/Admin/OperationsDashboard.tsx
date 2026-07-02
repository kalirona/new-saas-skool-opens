'use client'
import React from 'react'
import { useQuery } from '@tanstack/react-query'
import {
  Activity,
  AlertTriangle,
  CheckCircle2,
  Cpu,
  Database,
  Globe,
  Webhook,
  HardDrive,
  Loader2,
  RefreshCw,
} from 'lucide-react'
import { fetchOperationsDashboard, type OpsDashboardResponse } from '@services/operations'
import PageLoading from '@components/Objects/Loaders/PageLoading'

function StatCard({
  icon,
  label,
  value,
  sub,
  accent,
}: {
  icon: React.ReactNode
  label: string
  value: string | number
  sub?: string
  accent?: 'green' | 'red' | 'yellow' | 'blue'
}) {
  const accentMap: Record<string, string> = {
    green: 'text-emerald-400',
    red: 'text-red-400',
    yellow: 'text-yellow-400',
    blue: 'text-blue-400',
  }
  return (
    <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-5 flex items-start gap-4">
      <div className={`mt-0.5 ${accentMap[accent ?? 'blue'] || 'text-blue-400'}`}>
        {icon}
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-xs font-medium text-white/40 uppercase tracking-wider">{label}</p>
        <p className="text-2xl font-bold text-white mt-1">{value}</p>
        {sub && <p className="text-xs text-white/30 mt-0.5 truncate">{sub}</p>}
      </div>
    </div>
  )
}

function DependenciesCard({ deps }: { deps: { name: string; status: string; latency_ms?: number; error?: string }[] }) {
  return (
    <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-5 col-span-full lg:col-span-2">
      <h3 className="text-xs font-medium text-white/40 uppercase tracking-wider mb-3 flex items-center gap-2">
        <Activity size={14} /> Service Dependencies
      </h3>
      <div className="space-y-2">
        {deps.map((d) => (
          <div key={d.name} className="flex items-center justify-between px-3 py-2 rounded-lg bg-white/[0.02]">
            <div className="flex items-center gap-2 min-w-0">
              {d.status === 'healthy' ? (
                <CheckCircle2 size={14} className="text-emerald-400 shrink-0" />
              ) : (
                <AlertTriangle size={14} className="text-red-400 shrink-0" />
              )}
              <span className="text-sm text-white/70 truncate">{d.name}</span>
            </div>
            <div className="flex items-center gap-3 shrink-0">
              {d.latency_ms != null && (
                <span className="text-xs text-white/30">{d.latency_ms}ms</span>
              )}
              <span
                className={`text-xs font-medium ${
                  d.status === 'healthy' ? 'text-emerald-400' : 'text-red-400'
                }`}
              >
                {d.status}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}

function WebhookFailuresCard({ data }: { data: NonNullable<OpsDashboardResponse['failed_webhooks']> }) {
  if ('error' in data) {
    return <ErrorMini label="Webhook Failures" message={data.error} />
  }
  const recent = data.recent || []
  return (
    <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-5">
      <h3 className="text-xs font-medium text-white/40 uppercase tracking-wider mb-3 flex items-center gap-2">
        <Webhook size={14} /> Failed Webhooks <span className="text-red-400">({data.total_failed})</span>
      </h3>
      {recent.length === 0 ? (
        <p className="text-sm text-white/25">No recent failures</p>
      ) : (
        <div className="space-y-1.5 max-h-48 overflow-y-auto">
          {recent.map((w) => (
            <div key={w.id} className="text-xs text-white/50 truncate">
              <span className="text-white/70">{w.endpoint_id?.slice(0, 24)}</span>
              {w.status_code && <span className="text-red-400 ml-2">{w.status_code}</span>}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function BillingFailuresCard({ data }: { data: NonNullable<OpsDashboardResponse['billing_failures']> }) {
  if ('error' in data) {
    return <ErrorMini label="Billing Failures" message={data.error} />
  }
  return (
    <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-5">
      <h3 className="text-xs font-medium text-white/40 uppercase tracking-wider mb-3 flex items-center gap-2">
        <AlertTriangle size={14} /> Billing Failures{' '}
        <span className={data.total > 0 ? 'text-red-400' : 'text-emerald-400'}>({data.total})</span>
      </h3>
      {data.recent.length === 0 ? (
        <p className="text-sm text-white/25">No recent failures</p>
      ) : (
        <div className="space-y-1.5 max-h-48 overflow-y-auto">
          {data.recent.map((f) => (
            <div key={f.key} className="text-xs text-white/50 truncate">
              {f.data}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function ErrorMini({ label, message }: { label: string; message: string }) {
  return (
    <div className="bg-white/[0.03] border border-white/[0.08] rounded-xl p-5">
      <h3 className="text-xs font-medium text-white/40 uppercase tracking-wider mb-2">{label}</h3>
      <p className="text-xs text-red-400">{message}</p>
    </div>
  )
}

export default function OperationsDashboard() {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['operations-dashboard'],
    queryFn: fetchOperationsDashboard,
    refetchInterval: 30_000,
    staleTime: 15_000,
  })

  if (isLoading) return <PageLoading />

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-20 text-white/40">
        <AlertTriangle size={48} />
        <p className="mt-4 text-lg">Failed to load operations dashboard</p>
        <p className="text-sm text-white/25 mt-1">{(error as Error).message}</p>
      </div>
    )
  }

  if (!data) return null

  const health = 'status' in data.health ? data.health : null
  const healthStatusRaw = health?.status ?? 'unknown'
  const healthStatus = healthStatusRaw === 'ok' ? 'healthy' : healthStatusRaw === 'down' ? 'unhealthy' : healthStatusRaw
  const deps = health?.dependencies ?? []

  const ai = 'enabled' in data.ai_usage ? data.ai_usage : null
  const billing = 'total' in data.billing_failures ? data.billing_failures : null
  const webhooks = 'total_failed' in data.failed_webhooks ? data.failed_webhooks : null
  const storage = 'type' in data.storage_usage ? data.storage_usage : null
  const queue = 'connected' in data.queue_status ? data.queue_status : null
  const jobs = 'workers' in data.background_jobs ? data.background_jobs : null

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">Operations Dashboard</h1>
          <p className="text-white/40 mt-1 text-sm">
            System health, usage, and background status overview
          </p>
        </div>
        <button
          onClick={() => refetch()}
          className="flex items-center gap-2 px-3 py-2 text-sm text-white/50 hover:text-white border border-white/[0.08] rounded-lg hover:bg-white/[0.04] transition-colors"
        >
          <RefreshCw size={14} /> Refresh
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={<CheckCircle2 size={20} />}
          label="System Health"
          value={healthStatus.charAt(0).toUpperCase() + healthStatus.slice(1)}
          sub={`${deps.length} dependencies`}
          accent={healthStatus === 'healthy' ? 'green' : healthStatus === 'degraded' ? 'yellow' : 'red'}
        />
        <StatCard
          icon={<Cpu size={20} />}
          label="AI Provider"
          value={ai?.enabled ? ai.provider : 'Disabled'}
          sub={ai?.recent_requests != null ? `${ai.recent_requests} recent requests` : undefined}
          accent={ai?.enabled ? 'blue' : 'yellow'}
        />
        <StatCard
          icon={<Database size={20} />}
          label="Redis Queue"
          value={queue?.connected ? 'Connected' : 'Disconnected'}
          sub={
            queue?.connected_clients != null
              ? `${queue.connected_clients} clients · ${queue.used_memory_human}`
              : undefined
          }
          accent={queue?.connected ? 'green' : 'red'}
        />
        <StatCard
          icon={<HardDrive size={20} />}
          label="Storage"
          value={storage?.type ?? 'Unknown'}
          sub={storage?.healthy ? 'Healthy' : 'Unhealthy'}
          accent={storage?.healthy ? 'green' : 'red'}
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
        <DependenciesCard deps={deps} />
        <WebhookFailuresCard data={data.failed_webhooks} />
        <BillingFailuresCard data={data.billing_failures} />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <StatCard
          icon={<Globe size={20} />}
          label="Background Jobs"
          value={jobs?.queued ?? 0}
          sub={`${jobs?.workers ?? 0} workers · ${jobs?.recent_failures ?? 0} failures`}
          accent={jobs && jobs.recent_failures > 0 ? 'red' : 'green'}
        />
        <StatCard
          icon={<Activity size={20} />}
          label="Keyspace Hits"
          value={queue?.keyspace_hits?.toLocaleString() ?? '-'}
          sub={`Misses: ${queue?.keyspace_misses?.toLocaleString() ?? '-'}`}
          accent="blue"
        />
        <StatCard
          icon={<RefreshCw size={20} />}
          label="Uptime"
          value={
            queue?.uptime_in_seconds != null
              ? `${Math.floor(queue.uptime_in_seconds / 86400)}d`
              : '-'
          }
          accent="blue"
        />
      </div>
    </div>
  )
}
