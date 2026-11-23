import { useState } from 'react';
import { fetchTraitProfile } from '../api';
import type { components } from '../types/api';

type TraitProfile = components['schemas']['TraitProfileResponse'];

export function useTraitProfile() {
  const [traitProfile, setTraitProfile] = useState<TraitProfile | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);

  const loadTraitProfile = async (uploadId: any, itemUrl?: string) => {
    if (!uploadId) return;
    setProfileError(null);
    try {
      setTraitProfile(await fetchTraitProfile(Number(uploadId), itemUrl));
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Trait profile unavailable';
      console.warn('[WARN] Trait profile failed:', message);
      setProfileError(message);
    }
  };

  const clearTraitProfile = () => {
    setTraitProfile(null);
    setProfileError(null);
  };

  return {
    state: { traitProfile, profileError },
    actions: { loadTraitProfile, clearTraitProfile },
  };
}
