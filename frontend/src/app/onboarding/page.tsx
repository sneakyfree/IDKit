import { IntakeWizard } from '@/components/intake';

export default function OnboardingPage() {
    return <IntakeWizard flowId="creator_onboarding_v1" />;
}

export const metadata = {
    title: 'Get Started | IDKit',
    description: 'Set up your creator profile in just a few minutes',
};
