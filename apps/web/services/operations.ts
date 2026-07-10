export interface OpsDashboardResponse {
  timestamp: string
  health: {
    status: string
    timestamp?: string
    dependencies: { name: string; status: string; latency_ms?: number; error?: string }[]
  } | { error: string }
  ai_usage: {
    enabled: boolean
    provider: string
    recent_requests: number
  } | { error: string }
  billing_failures: {
    total: number
    recent: { key: string; data: string }[]
  } | { error: string }
  failed_webhooks: {
    total_failed: number
    recent: { id: string; endpoint_id: string; status_code?: number; error?: string; created_at?: string }[]
  } | { error: string }
  storage_usage: {
    type: string
    healthy: boolean
  } | { error: string }
  queue_status: {
    connected: boolean
    used_memory_human?: string
    connected_clients?: number
    uptime_in_seconds?: number
    keyspace_hits?: number
    keyspace_misses?: number
  } | { error: string }
  background_jobs: {
    workers: number
    queued: number
    recent_failures: number
  } | { error: string }
}

export async function fetchOperationsDashboard(): Promise<OpsDashboardResponse> {
  const res = await fetch('/api/v1/operations/dashboard')
  if (!res.ok) {
    throw new Error(`Failed to fetch operations dashboard: ${res.statusText}`)
  }
  return res.json()
}
