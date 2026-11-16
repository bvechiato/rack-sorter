import { useState } from 'react';
import { fetchTraitProfile } from '../api';
import type { components } from '../types/api';

type TraitProfile = components['schemas']['TraitProfileResponse'];

export function useTraitProfile() {
  const [traitProfile, setTraitProfile] = useState<TraitProfile | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [profileLoading, setProfileLoading] = useState(false);

  const loadTraitProfile = async (uploadId: any, itemUrl?: string) => {
    if (!uploadId) return;
    setProfileError(null);
    setProfileLoading(true);
    try {
      setTraitProfile(await fetchTraitProfile(Number(uploadId), itemUrl));
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Trait profile unavailable';
      console.warn('[WARN] Trait profile failed:', message);
      setProfileError(message);
    } finally {
      setProfileLoading(false);
    }
  };

  const clearTraitProfile = () => {
    setTraitProfile(null);
    setProfileError(null);
  };

  return {
    state: { traitProfile, profileError, profileLoading },
    actions: { loadTraitProfile, clearTraitProfile },
  };
}
