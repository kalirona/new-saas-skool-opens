'use client';
import CreatorLeftMenu from '@components/Dashboard/Menus/CreatorLeftMenu';
import CreatorMobileMenu from '@components/Dashboard/Menus/CreatorMobileMenu';
import OnboardingBar from '@components/Dashboard/Onboarding/OnboardingBar';
import WelcomeModal from '@components/Dashboard/Onboarding/WelcomeModal';
import FreePlanUpgradeBanner from '@components/Dashboard/Shared/PlanRestricted/FreePlanUpgradeBanner';
import AdminAuthorization from '@components/Security/AdminAuthorization'
import { SessionGate } from '@components/Contexts/LHSessionContext'
import { CommandPaletteProvider } from '@components/Dashboard/CommandPalette/CommandPaletteContext'
import CommandPalette from '@components/Dashboard/CommandPalette/CommandPalette'
import React from 'react'
import { useMediaQuery } from 'usehooks-ts';

function ClientAdminLayout({
    children,
    params,
}: {
    children: React.ReactNode
    params: any
}) {
    const isMobile = useMediaQuery('(max-width: 1024px)')

    return (
        <SessionGate>
            <AdminAuthorization authorizationMode="page">
                <CommandPaletteProvider>
                    {isMobile && <CreatorMobileMenu />}
                    <div className="flex flex-col lg:flex-row">
                        {!isMobile && <CreatorLeftMenu />}
                        <div className="flex flex-col w-full relative isolate pb-24 lg:pb-0">
                            <FreePlanUpgradeBanner />
                            {children}
                            <OnboardingBar />
                        </div>
                        <WelcomeModal />
                        <CommandPalette />
                    </div>
                </CommandPaletteProvider>
            </AdminAuthorization>
        </SessionGate>
    )
}

export default ClientAdminLayout
