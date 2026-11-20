import { useRef, useState } from 'react';
import { fetchInitial, rerankBatch } from '../api';
import type { components } from '../types/api';
import type { Trait } from '../static/constants';
import { useTraitProfile } from './useTraitProfile';

export type TraitPicks = Partial<Record<Trait, 'MORE' | 'LESS'>>;
type Item = components['schemas']['ItemResponse'];

// Aesthetic events are global, so there is no clicked item to name. The field is required
// by the API shape and ignored by the aesthetic lane; a stable sentinel keeps the stored
// history honest instead of borrowing some card's URL.
const GLOBAL_FEEDBACK_ITEM_URL = 'global';

export function useProductSearch() {
  const [currentPool, setCurrentPool] = useState<Item[]>([]);
  const [products, setProducts] = useState<Item[]>([]);
  const [loading, setLoading] = useState(false);
  const [traitPicks, setTraitPicks] = useState<Record<string, TraitPicks>>({});
  // Aesthetics are global: one list per upload, not per item. Kept in step with the
  // server's append-only history, which is also keyed by upload.
  const [aesthetics, setAesthetics] = useState<string[]>([]);
  const aestheticsUploadId = useRef<any>(null);
  // Feedbacks accumulated since the last catalogue-page fetch. A new page is
  // pulled only every FETCH_EVERY feedbacks, so most taps stay cheap.
  const [feedbacksSinceFetch, setFeedbacksSinceFetch] = useState(0);
  const [fetchingMore, setFetchingMore] = useState(false);
  const FETCH_EVERY = 3;

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
      // Feedback history is stored per upload, so a re-scrape of the same upload keeps
      // steering; only a new upload starts from a clean style list.
      if (aestheticsUploadId.current !== uploadId) {
        aestheticsUploadId.current = uploadId;
        setAesthetics([]);
      }
      setFeedbacksSinceFetch(0);
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

    const eventsCount = 1;
    const willFetch = feedbacksSinceFetch + eventsCount >= FETCH_EVERY;

    setLoading(true);
    setFetchingMore(willFetch);

    try {
      const rankedData = await rerankBatch({
        upload_id: uploadId,
        feedback: [{ item_url: itemUrl, feedback_type: feedbackType, concept: concept ?? null }],
        fetch_more: willFetch,
      });

      setProducts(rankedData.pool || []);
      setCurrentPool(rankedData.pool || []);

      if (concept) {
        setTraitPicks(prev => ({
          ...prev,
          [itemUrl]: { ...prev[itemUrl], [concept]: feedbackType },
        }));
      }

      setFeedbacksSinceFetch(willFetch ? 0 : feedbacksSinceFetch + eventsCount);

      // Profile is only needed for the Tune sheet's debug radar; it refreshes on
      // open and after Done, so skip the extra /trait-profile call here.
    } catch (err) {
      throw err instanceof Error ? err : new Error('Vector calculation error');
    } finally {
      setFetchingMore(false);
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
      const eventsCount = feedback.length;
      const willFetch = feedbacksSinceFetch + eventsCount >= FETCH_EVERY;

      setFetchingMore(willFetch);

      const rankedData = await rerankBatch({
        upload_id: uploadId,
        feedback,
        fetch_more: willFetch,
      });

      setProducts(rankedData.pool || []);
      setCurrentPool(rankedData.pool || []);
      setTraitPicks(prev => ({ ...prev, [itemUrl]: picks }));

      setFeedbacksSinceFetch(willFetch ? 0 : feedbacksSinceFetch + eventsCount);

      await loadTraitProfile(uploadId, itemUrl);
    } catch (err) {
      throw err instanceof Error ? err : new Error('Vector calculation error');
    } finally {
      setFetchingMore(false);
      setLoading(false);
    }
  };

  /**
   * Switch one global style phrase on or off and rerank the pool.
   *
   * Aesthetic events are absolute: the phrase carries the intent, so ``feedback_type`` is
   * just the switch (MORE = steer toward it, LESS = remove it). ``item_url`` is a required
   * carrier field that the aesthetic lane ignores — there is no "clicked item" here.
   */
  const toggleAesthetic = async (uploadId: any, phrase: string, active: boolean) => {
    if (!uploadId) {
      throw new Error('Missing upload id');
    }

    const normalized = phrase.trim();
    if (!normalized) return;

    const eventsCount = 1;
    const willFetch = feedbacksSinceFetch + eventsCount >= FETCH_EVERY;

    setLoading(true);
    setFetchingMore(willFetch);

    try {
      const rankedData = await rerankBatch({
        upload_id: uploadId,
        feedback: [
          {
            item_url: GLOBAL_FEEDBACK_ITEM_URL,
            feedback_type: active ? 'LESS' : 'MORE',
            aesthetic: normalized,
          },
        ],
        fetch_more: willFetch,
      });

      setProducts(rankedData.pool || []);
      setCurrentPool(rankedData.pool || []);
      setAesthetics(prev => (
        active
          ? prev.filter(value => value.toLowerCase() !== normalized.toLowerCase())
          : [...prev, normalized]
      ));

      setFeedbacksSinceFetch(willFetch ? 0 : feedbacksSinceFetch + eventsCount);
    } catch (err) {
      throw err instanceof Error ? err : new Error('Vector calculation error');
    } finally {
      setFetchingMore(false);
      setLoading(false);
    }
  };

  return {
    state: {
      currentPool,
      products,
      loading,
      traitPicks,
      aesthetics,
      feedbacksSinceFetch,
      fetchingMore,
      traitProfile: traitProfile.state.traitProfile,
      profileError: traitProfile.state.profileError,
    },
    actions: {
      scrapeProducts,
      rerankProducts,
      applyTraitPicks,
      toggleAesthetic,
      loadTraitProfile,
    },
  };
}
