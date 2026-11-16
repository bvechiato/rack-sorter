import { useState } from 'react';
import { fetchInitial, rerankBatch } from '../api';
import type { components } from '../types/api';
import type { Trait } from '../static/constants';
import { useTraitProfile } from './useTraitProfile';

export type TraitPicks = Partial<Record<Trait, 'MORE' | 'LESS'>>;
type Item = components['schemas']['ItemResponse'];

export function useProductSearch() {
  const [currentPool, setCurrentPool] = useState<Item[]>([]);
  const [products, setProducts] = useState<Item[]>([]);
  const [loading, setLoading] = useState(false);
  const [traitPicks, setTraitPicks] = useState<Record<string, TraitPicks>>({});
  const [newItems, setNewItems] = useState(0);

  const traitProfile = useTraitProfile();

  const loadTraitProfile = traitProfile.actions.loadTraitProfile;
  const clearTraitProfile = traitProfile.actions.clearTraitProfile;

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

      const poolData = await fetchInitial(requestData);
      console.log(`[INFO] Sending scrape request with filters: ${JSON.stringify(requestData)}`);

      setCurrentPool(poolData.pool || []);
      setProducts(poolData.pool || []);
      setTraitPicks({});
      setNewItems(0);
      clearTraitProfile();
    } catch {
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
      const rankedData = await rerankBatch({
        upload_id: uploadId,
        feedback: [{ item_url: itemUrl, feedback_type: feedbackType, concept: concept ?? null }],
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

      await loadTraitProfile(uploadId, itemUrl);
    } catch (err) {
      throw err instanceof Error ? err : new Error('Vector calculation error');
    } finally {
      setLoading(false);
    }
  };

  const applyTraitPicks = async (uploadId: any, itemUrl: string, picks: TraitPicks) => {
    if (!uploadId) {
      throw new Error('Missing upload id');
    }

    const feedback = (Object.entries(picks) as [Trait, 'MORE' | 'LESS'][]).map(
      ([concept, feedback_type]) => ({ item_url: itemUrl, feedback_type, concept }),
    );
    if (!feedback.length) return;

    setLoading(true);
    try {
      const rankedData = await rerankBatch({
        upload_id: uploadId,
        feedback,
        fetch_more: true,
      });

      setProducts(rankedData.pool || []);
      setCurrentPool(rankedData.pool || []);
      setNewItems(rankedData.new_items ?? 0);
      setTraitPicks(prev => ({ ...prev, [itemUrl]: picks }));

      await loadTraitProfile(uploadId, itemUrl);
    } catch (err) {
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
      traitProfile: traitProfile.state.traitProfile,
      profileError: traitProfile.state.profileError,
    },
    actions: {
      scrapeProducts,
      rerankProducts,
      applyTraitPicks,
      loadTraitProfile,
    },
  };
}
