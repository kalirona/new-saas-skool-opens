'use client'
import { Users, CheckCircle, MessageSquare, Download, TrendingUp, TrendingDown } from 'lucide-react'
import React from 'react'
import { useDashboardOverview } from './useDashboardOverview'

import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  Tooltip,
} from 'recharts'
import { useTranslation } from 'react-i18next'

function StatCard({
  icon,
  label,
  total,
  thisMonth,
  growth,
  color,
}: {
  icon: React.ReactNode
  label: string
  total: number
  thisMonth: number
  growth: number
  color: string
}) {
  const isUp = growth >= 0
  return (
    <div className="bg-white nice-shadow rounded-xl p-5 flex flex-col gap-3 min-w-0">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <div
            className="w-9 h-9 rounded-lg flex items-center justify-center"
            style={{ backgroundColor: color + '15' }}
          >
            {icon}
          </div>
          <span className="text-sm font-medium text-gray-500">{label}</span>
        </div>
        <span
          className={`flex items-center gap-0.5 text-xs font-semibold px-2 py-1 rounded-full ${
            isUp ? 'text-green-700 bg-green-50' : 'text-red-700 bg-red-50'
          }`}
        >
          {isUp ? <TrendingUp size={12} /> : <TrendingDown size={12} />}
          {Math.abs(growth).toFixed(1)}%
        </span>
      </div>
      <div className="flex items-baseline gap-3">
        <span className="text-3xl font-bold text-gray-900 tracking-tight">
          {total.toLocaleString()}
        </span>
        <span className="text-sm text-gray-400">
          +{thisMonth} this month
        </span>
      </div>
    </div>
  )
}

function SparklineChart({
  data,
  color,
}: {
  data: { month: string; count: number }[]
  color: string
}) {
  return (
    <div style={{ height: 60 }}>
      <ResponsiveContainer width="100%" height={60}>
        <AreaChart data={data} margin={{ top: 0, right: 0, bottom: 0, left: 0 }}>
          <defs>
            <linearGradient id={`grad-${color.replace('#', '')}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={color} stopOpacity={0.2} />
              <stop offset="100%" stopColor={color} stopOpacity={0} />
            </linearGradient>
          </defs>
          <XAxis dataKey="month" hide />
          <Tooltip
            contentStyle={{
              borderRadius: 8,
              border: '1px solid #f3f4f6',
              boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
              fontSize: 11,
            }}
            formatter={(value: any) => [typeof value === 'number' ? value.toLocaleString() : String(value), '']}
            labelFormatter={(label) => label}
          />
          <Area
            type="monotone"
            dataKey="count"
            stroke={color}
            strokeWidth={2}
            fill={`url(#grad-${color.replace('#', '')})`}
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  )
}

export default function DashboardOverview() {
  const { t } = useTranslation()
  const { data, isLoading, error } = useDashboardOverview()

  if (isLoading) {
    return (
      <div className="bg-white nice-shadow rounded-xl p-10 text-center text-gray-300">
        {t('analytics.common.loading')}
      </div>
    )
  }

  if (error || !data) {
    return null
  }

  const cards = [
    {
      icon: <Users size={18} className="text-blue-500" />,
      label: t('analytics.overview.active_members'),
      total: data.active_members.total,
      thisMonth: data.active_members.this_month,
      growth: data.active_members.growth_percent,
      color: '#3b82f6',
      chart: data.growth_charts.members,
    },
    {
      icon: <CheckCircle size={18} className="text-emerald-500" />,
      label: t('analytics.overview.course_completions'),
      total: data.course_completions.total,
      thisMonth: data.course_completions.this_month,
      growth: data.course_completions.growth_percent,
      color: '#10b981',
      chart: data.growth_charts.completions,
    },
    {
      icon: <MessageSquare size={18} className="text-violet-500" />,
      label: t('analytics.overview.discussion_activity'),
      total: data.discussion_activity.total_discussions,
      thisMonth: data.discussion_activity.this_month_discussions,
      growth: data.discussion_activity.growth_percent_discussions,
      color: '#8b5cf6',
      chart: data.growth_charts.discussions,
    },
    {
      icon: <Download size={18} className="text-amber-500" />,
      label: t('analytics.overview.resources'),
      total: data.resources.total,
      thisMonth: data.resources.this_month,
      growth: data.resources.growth_percent,
      color: '#f59e0b',
      chart: data.growth_charts.resources,
    },
  ]

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map((card) => (
          <StatCard key={card.label} {...card} />
        ))}
      </div>

      {/* Growth charts row */}
      <div className="bg-white nice-shadow rounded-xl p-5">
        <h3 className="text-sm font-semibold text-gray-700 mb-4">
          {t('analytics.overview.growth_trends')}
        </h3>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
          {cards.map((card) => (
            <div key={card.label} className="min-w-0">
              <div className="flex items-center gap-1.5 mb-1">
                <span
                  className="w-2 h-2 rounded-full"
                  style={{ backgroundColor: card.color }}
                />
                <span className="text-[11px] text-gray-400 font-medium truncate">
                  {card.label}
                </span>
              </div>
              <SparklineChart data={card.chart} color={card.color} />
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
