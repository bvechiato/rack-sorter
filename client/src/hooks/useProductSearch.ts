import { useState } from 'react';
import { fetchInitial, fetchTraitProfile, rerank } from '../api';
import type { components } from '../types/api';
import type { Trait } from '../static/constants';

export type TraitPicks = Partial<Record<Trait, 'MORE' | 'LESS'>>;
type TraitProfile = components['schemas']['TraitProfileResponse'];

export function useProductSearch() {
  const [currentPool, setCurrentPool] = useState<any[]>([]);
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  // Trait choices keyed by item URL. Kept outside the sheet so reopening it shows
  // what is already applied, and the card's Tune trigger can show an active state.
  const [traitPicks, setTraitPicks] = useState<Record<string, TraitPicks>>({});
  // Items appended by the last rerank's extra catalogue page.
  const [newItems, setNewItems] = useState(0);
  // Debug view of the scorer: raw axis projections + the pool spread it standardises
  // against. Refreshed after every feedback so the diagram moves with the ranking.
  const [traitProfile, setTraitProfile] = useState<TraitProfile | null>(null);
  const [profileError, setProfileError] = useState<string | null>(null);

  const loadTraitProfile = async (uploadId: any, itemUrl?: string) => {
    if (!uploadId) return;
    setProfileError(null);
    try {
      setTraitProfile(await fetchTraitProfile(Number(uploadId), itemUrl));
    } catch (err) {
      // The radar is a debugging aid: never fail the search or swallow the reason.
      const message = err instanceof Error ? err.message : 'Trait profile unavailable';
      console.warn('[WARN] Trait profile failed:', message);
      setProfileError(message);
    }
  };

  const scrapeProducts = async (uploadId: any, keyword: string, filters: any) => {
    if (!keyword.trim()) {
      throw new Error('Please provide or parse a lookup keyword first.');
    }

    setLoading(true);
    try {
      const requestData = {
        uploadId: Number(uploadId),
        keyword: keyword,
        selectedSizes: filters.selectedSizes.join(','),
        selectedCategory: filters.selectedCategory,
        selectedColors: filters.selectedColors.join(','),
        maxPrice: String(filters.maxPrice),
        selectedConditions: filters.selectedConditions.join(',')
      };

      // Now this passes type checking!
      const poolData = await fetchInitial(requestData);
      console.log(`[INFO] Sending scrape request with filters: ${JSON.stringify(requestData)}`);

      setCurrentPool(poolData.pool || []);
      setProducts(poolData.pool || []);
      // A fresh pool has no trait history yet.
      setTraitPicks({});
      setNewItems(0);
      setTraitProfile(null);
      setProfileError(null);
    } catch (err) {
      throw new Error('Failed fetching items with the chosen keyword.');
    } finally {
      setLoading(false);
    }
  };

  const rerankProducts = async (uploadId: any, itemUrl: string, feedbackType: 'MORE' | 'LESS', concept?: Trait) => {
    if (!uploadId) {
      throw new Error('Missing upload id');
    }

    setLoading(true);

    try {
      const rankedData = await rerank({
        upload_id: uploadId,
        item_url: itemUrl,
        feedback_type: feedbackType,
        concept: concept ?? null,
        fetch_more: true,
      });

      setProducts(rankedData.pool || []);
      setCurrentPool(rankedData.pool || []);
      setNewItems(rankedData.new_items ?? 0);

      if (concept) {
        setTraitPicks(prev => ({
          ...prev,
          [itemUrl]: { ...prev[itemUrl], [concept]: feedbackType },
        }));
      }

      // Recompute the debug diagram from the *new* pool/ranking. Awaited so the
      // sheet's "updating" state covers it, but errors stay attached to the panel.
      await loadTraitProfile(uploadId, itemUrl);
    } catch (err) {
      // Surface the backend reason; a generic message hides axis/deadband faults.
      throw err instanceof Error ? err : new Error('Vector calculation error');
    } finally {
      setLoading(false);
    }
  };

  return {
    state: {
      currentPool,
      products,
      loading,
      traitPicks,
      newItems,
      traitProfile,
      profileError,
    },
    actions: {
      scrapeProducts,
      rerankProducts,
      loadTraitProfile,
    },
  };
}
