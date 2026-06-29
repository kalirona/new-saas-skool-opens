'use client'
import React, { useState, useEffect, useCallback } from 'react'
import { useOrg } from '@components/Contexts/OrgContext'
import { useLHSession } from '@components/Contexts/LHSessionContext'
import { useRouter } from 'next/navigation'
import { getUriWithOrg } from '@services/config/config'
import { createCommunity } from '@services/communities/communities'
import { createMembershipPlan } from '@services/communities/membership'
import { getStripeExpressOnboardingLink } from '@services/payments/providers/stripe'
import {
  ArrowRight, ArrowLeft, Check, Building2, Users, Palette, CreditCard,
  Rocket, Package, Crown, Star, Sparkles
} from 'lucide-react'

type StepState = 'current' | 'upcoming' | 'completed'

interface Step {
  id: number
  title: string
  description: string
  icon: React.ReactNode
  state: StepState
}

const STEPS: Omit<Step, 'state'>[] = [
  { id: 1, title: 'Workspace', description: 'Name your workspace', icon: <Building2 size={20} /> },
  { id: 2, title: 'Community', description: 'Set up your community', icon: <Users size={20} /> },
  { id: 3, title: 'Branding', description: 'Customize your look', icon: <Palette size={20} /> },
  { id: 4, title: 'Plans', description: 'Create membership plans', icon: <Package size={20} /> },
  { id: 5, title: 'Payments', description: 'Connect Stripe', icon: <CreditCard size={20} /> },
  { id: 6, title: 'Publish', description: 'Launch your workspace', icon: <Rocket size={20} /> },
]

export default function OnboardingWizard() {
  const org = useOrg() as any
  const session = useLHSession() as any
  const access_token = session?.data?.tokens?.access_token
  const router = useRouter()

  const [currentStep, setCurrentStep] = useState(1)
  const [saved, setSaved] = useState<Record<number, boolean>>({})

  const [workspace, setWorkspace] = useState({ name: '', slug: '', description: '' })
  const [community, setCommunity] = useState({ name: '', description: '', type: 'open' as 'open' | 'paid' | 'invite_only' | 'hidden' })
  const [branding, setBranding] = useState({ logo: '', colors: { primary: '#3B82F6', secondary: '#10B981' } })
  const [plans, setPlans] = useState<{ name: string; price: number; interval: string; description: string }[]>([
    { name: 'Free', price: 0, interval: 'monthly', description: 'Basic access' },
    { name: 'Pro', price: 29, interval: 'monthly', description: 'Full access' },
    { name: 'VIP', price: 99, interval: 'monthly', description: 'Everything included' },
  ])
  const [stripeStatus, setStripeStatus] = useState<{ connected: boolean; url?: string }>({ connected: false })
  const [publishing, setPublishing] = useState(false)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (org) {
      setWorkspace(prev => ({
        ...prev,
        name: org.name || '',
        slug: org.slug || '',
        description: org.description || '',
      }))
    }
  }, [org])

  const getToken = () => access_token || ''

  const saveStep = useCallback(async (step: number) => {
    setSaving(true)
    try {
      setSaved(prev => ({ ...prev, [step]: true }))
    } catch (e) {
      console.error('Save failed:', e)
    }
    setSaving(false)
  }, [])

  const nextStep = async () => {
    await saveStep(currentStep)
    if (currentStep < 6) setCurrentStep(currentStep + 1)
  }

  const prevStep = () => {
    if (currentStep > 1) setCurrentStep(currentStep - 1)
  }

  const handleCreateCommunity = async () => {
    const newCommunity = await createCommunity(
      org.id,
      { name: community.name, description: community.description, community_type: community.type },
      getToken()
    )
    return newCommunity
  }

  const handleCreatePlans = async (communityUuid: string) => {
    for (const [idx, plan] of plans.filter(p => p.name).entries()) {
      try {
        await createMembershipPlan(
          communityUuid,
          {
            name: plan.name,
            description: plan.description || '',
            price: plan.price,
            currency: 'usd',
            interval: plan.interval as 'monthly' | 'yearly' | 'one_time',
            is_free: plan.price === 0,
            is_public: true,
            display_order: idx,
            status: 'active',
          },
          getToken()
        )
      } catch (e) {
        console.error('Failed to create plan:', plan.name, e)
      }
    }
  }

  const handleStripeConnect = async () => {
    try {
      const redirectUri = `${window.location.origin}${getUriWithOrg(org.slug, '/dash/onboarding')}`
      const result = await getStripeExpressOnboardingLink(org.id, getToken(), redirectUri)
      if (result?.url) {
        setStripeStatus({ connected: false, url: result.url })
        window.open(result.url, '_blank')
      }
    } catch (e) {
      console.error('Stripe connect failed:', e)
    }
  }

  const handlePublish = async () => {
    setPublishing(true)
    try {
      await saveStep(currentStep)
      const newCommunity = await handleCreateCommunity()
      if (newCommunity?.community_uuid) {
        await handleCreatePlans(newCommunity.community_uuid)
      }
      router.push(getUriWithOrg(org.slug, '/dash'))
    } catch (e) {
      console.error('Publish failed:', e)
    }
    setPublishing(false)
  }

  const steps: Step[] = STEPS.map(s => ({
    ...s,
    state: s.id === currentStep ? 'current' : saved[s.id] ? 'completed' : 'upcoming',
  }))

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="mb-8">
          <h1 className="text-2xl font-bold text-gray-900">Set up your workspace</h1>
          <p className="text-gray-500 mt-1">Complete the steps below to launch your community</p>
        </div>

        <div className="flex items-center gap-2 mb-8 overflow-x-auto pb-2">
          {steps.map((step, idx) => (
            <React.Fragment key={step.id}>
              <div className={`flex items-center gap-2 px-3 py-2 rounded-lg whitespace-nowrap transition-colors ${
                step.state === 'current' ? 'bg-blue-100 text-blue-700' :
                step.state === 'completed' ? 'bg-green-50 text-green-600' :
                'bg-gray-100 text-gray-400'
              }`}>
                <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                  step.state === 'completed' ? 'bg-green-500 text-white' :
                  step.state === 'current' ? 'bg-blue-600 text-white' :
                  'bg-gray-300 text-gray-500'
                }`}>
                  {step.state === 'completed' ? <Check size={12} /> : step.id}
                </div>
                <span className="text-sm font-medium hidden sm:inline">{step.title}</span>
              </div>
              {idx < steps.length - 1 && <div className="w-4 h-px bg-gray-300 hidden sm:block" />}
            </React.Fragment>
          ))}
        </div>

        <div className="bg-white rounded-xl shadow-sm ring-1 ring-gray-200 p-6 md:p-8">
          {currentStep === 1 && (
            <div className="space-y-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-blue-50 rounded-lg"><Building2 size={24} className="text-blue-600" /></div>
                <div><h2 className="text-xl font-bold">Workspace Name</h2><p className="text-gray-500 text-sm">What is your workspace called?</p></div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Workspace Name</label>
                <input type="text" value={workspace.name} onChange={e => setWorkspace(p => ({ ...p, name: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="My Learning Community" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea value={workspace.description} onChange={e => setWorkspace(p => ({ ...p, description: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  rows={3} placeholder="What is your workspace about?" />
              </div>
            </div>
          )}

          {currentStep === 2 && (
            <div className="space-y-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-purple-50 rounded-lg"><Users size={24} className="text-purple-600" /></div>
                <div><h2 className="text-xl font-bold">Community Details</h2><p className="text-gray-500 text-sm">Set up your first community</p></div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Community Name</label>
                <input type="text" value={community.name} onChange={e => setCommunity(p => ({ ...p, name: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  placeholder="Marketing Community" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea value={community.description} onChange={e => setCommunity(p => ({ ...p, description: e.target.value }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                  rows={3} placeholder="Describe your community..." />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Community Type</label>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {[
                    { value: 'open', label: 'Open', desc: 'Anyone can join' },
                    { value: 'paid', label: 'Paid', desc: 'Requires payment' },
                    { value: 'invite_only', label: 'Invite Only', desc: 'By invitation' },
                    { value: 'hidden', label: 'Hidden', desc: 'Not listed' },
                  ].map(t => (
                    <button key={t.value} onClick={() => setCommunity(p => ({ ...p, type: t.value as any }))}
                      className={`p-3 rounded-lg border text-left transition-all ${
                        community.type === t.value ? 'border-blue-500 bg-blue-50 ring-1 ring-blue-500' : 'border-gray-200 hover:border-gray-300'
                      }`}>
                      <div className="font-medium text-sm">{t.label}</div>
                      <div className="text-xs text-gray-500 mt-0.5">{t.desc}</div>
                    </button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {currentStep === 3 && (
            <div className="space-y-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-pink-50 rounded-lg"><Palette size={24} className="text-pink-600" /></div>
                <div><h2 className="text-xl font-bold">Branding</h2><p className="text-gray-500 text-sm">Customize your workspace appearance</p></div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Primary Color</label>
                <div className="flex items-center gap-3">
                  <input type="color" value={branding.colors.primary}
                    onChange={e => setBranding(p => ({ ...p, colors: { ...p.colors, primary: e.target.value } }))}
                    className="w-12 h-12 rounded-lg border border-gray-300 cursor-pointer" />
                  <span className="text-sm text-gray-500 font-mono">{branding.colors.primary}</span>
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Secondary Color</label>
                <div className="flex items-center gap-3">
                  <input type="color" value={branding.colors.secondary}
                    onChange={e => setBranding(p => ({ ...p, colors: { ...p.colors, secondary: e.target.value } }))}
                    className="w-12 h-12 rounded-lg border border-gray-300 cursor-pointer" />
                  <span className="text-sm text-gray-500 font-mono">{branding.colors.secondary}</span>
                </div>
              </div>
              <div className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm text-gray-500">Branding can always be updated later from the dashboard settings.</p>
              </div>
            </div>
          )}

          {currentStep === 4 && (
            <div className="space-y-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-amber-50 rounded-lg"><Package size={24} className="text-amber-600" /></div>
                <div><h2 className="text-xl font-bold">Membership Plans</h2><p className="text-gray-500 text-sm">Define your Free, Pro, and VIP tiers</p></div>
              </div>
              <div className="space-y-4">
                {plans.map((plan, idx) => (
                  <div key={idx} className="p-4 border border-gray-200 rounded-lg space-y-3">
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        {idx === 0 && <Sparkles size={18} className="text-green-500" />}
                        {idx === 1 && <Star size={18} className="text-blue-500" />}
                        {idx === 2 && <Crown size={18} className="text-amber-500" />}
                        <input type="text" value={plan.name}
                          onChange={e => { const p = [...plans]; p[idx].name = e.target.value; setPlans(p) }}
                          className="font-medium border-b border-transparent focus:border-blue-500 focus:outline-none px-1"
                          placeholder="Plan name" />
                      </div>
                    </div>
                    <div className="flex gap-3">
                      <div className="flex-1">
                        <label className="text-xs text-gray-500">Price ($)</label>
                        <input type="number" value={plan.price}
                          onChange={e => { const p = [...plans]; p[idx].price = Number(e.target.value); setPlans(p) }}
                          className="w-full px-2 py-1 border border-gray-200 rounded text-sm" min={0} step={0.99} />
                      </div>
                      <div className="flex-1">
                        <label className="text-xs text-gray-500">Interval</label>
                        <select value={plan.interval}
                          onChange={e => { const p = [...plans]; p[idx].interval = e.target.value; setPlans(p) }}
                          className="w-full px-2 py-1 border border-gray-200 rounded text-sm">
                          <option value="monthly">Monthly</option>
                          <option value="yearly">Yearly</option>
                          <option value="one_time">One-time</option>
                        </select>
                      </div>
                    </div>
                    <input type="text" value={plan.description}
                      onChange={e => { const p = [...plans]; p[idx].description = e.target.value; setPlans(p) }}
                      className="w-full px-2 py-1 border border-gray-200 rounded text-sm"
                      placeholder="Brief description of this plan" />
                  </div>
                ))}
              </div>
            </div>
          )}

          {currentStep === 5 && (
            <div className="space-y-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-indigo-50 rounded-lg"><CreditCard size={24} className="text-indigo-600" /></div>
                <div><h2 className="text-xl font-bold">Payment Provider</h2><p className="text-gray-500 text-sm">Connect Stripe to accept payments</p></div>
              </div>
              <div className="p-6 border border-gray-200 rounded-lg">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 bg-indigo-50 rounded-lg flex items-center justify-center">
                      <svg className="w-7 h-7" viewBox="0 0 24 24" fill="#635BFF"><path d="M13.3 2.1A10 10 0 0 0 2.1 13.3a10 10 0 0 0 11.2 11.2A10 10 0 0 0 24.5 13.3 10 10 0 0 0 13.3 2.1zm3.6 6.7h-2.7v5.6c0 1.4-.5 2.1-1.7 2.1-.5 0-1.2-.2-1.5-.4l-.4 2.1c.4.2 1.3.5 2.3.5 2.5 0 4-1.5 4-4.5V8.8zm-6.4 0H7.8v7.8h2.7V8.8z"/></svg>
                    </div>
                    <div>
                      <h3 className="font-semibold">Stripe</h3>
                      <p className="text-sm text-gray-500">Accept credit cards and more</p>
                    </div>
                  </div>
                  {stripeStatus.connected ? (
                    <span className="flex items-center gap-1 text-green-600 bg-green-50 px-3 py-1 rounded-full text-sm font-medium">
                      <Check size={16} /> Connected
                    </span>
                  ) : (
                    <button onClick={handleStripeConnect}
                      className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors text-sm font-medium">
                      Connect Stripe
                    </button>
                  )}
                </div>
                {stripeStatus.url && (
                  <p className="mt-3 text-sm text-gray-500">
                    A new tab opened for Stripe onboarding. Complete the setup there, then return here.
                  </p>
                )}
              </div>
            </div>
          )}

          {currentStep === 6 && (
            <div className="space-y-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="p-2 bg-green-50 rounded-lg"><Rocket size={24} className="text-green-600" /></div>
                <div><h2 className="text-xl font-bold">Publish</h2><p className="text-gray-500 text-sm">Review and launch your workspace</p></div>
              </div>
              <div className="space-y-4">
                {[
                  { label: 'Workspace', value: workspace.name, icon: <Building2 size={16} /> },
                  { label: 'Community', value: community.name, icon: <Users size={16} /> },
                  { label: 'Plans', value: `${plans.filter(p => p.name).length} plans configured`, icon: <Package size={16} /> },
                  { label: 'Payments', value: stripeStatus.connected ? 'Stripe connected' : 'Not connected (skip)', icon: <CreditCard size={16} /> },
                ].map((item, idx) => (
                  <div key={idx} className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                    <div className="text-gray-400">{item.icon}</div>
                    <div>
                      <div className="text-xs text-gray-500">{item.label}</div>
                      <div className="font-medium text-gray-900">{item.value || 'Not set'}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          <div className="flex items-center justify-between mt-8 pt-6 border-t border-gray-200">
            <button onClick={prevStep} disabled={currentStep === 1}
              className="flex items-center gap-2 px-4 py-2 text-gray-600 hover:text-gray-900 disabled:opacity-50 disabled:cursor-not-allowed transition-colors">
              <ArrowLeft size={16} /> Back
            </button>
            <div className="flex items-center gap-3">
              {saved[currentStep] && (
                <span className="flex items-center gap-1 text-xs text-green-600"><Check size={12} /> Saved</span>
              )}
              {currentStep < 6 ? (
                <button onClick={nextStep} disabled={saving}
                  className="flex items-center gap-2 px-5 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors font-medium">
                  {saving ? 'Saving...' : 'Continue'} <ArrowRight size={16} />
                </button>
              ) : (
                <button onClick={handlePublish} disabled={publishing}
                  className="flex items-center gap-2 px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors font-medium">
                  {publishing ? 'Publishing...' : 'Publish Workspace'} <Rocket size={16} />
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
