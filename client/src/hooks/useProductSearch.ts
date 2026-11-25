import { useRef, useState } from 'react';
import { fetchInitial, fetchLastFeedback as apiFetchLastFeedback, rerankBatch, undoFeedback } from '../api';
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
  const [products, setProducts] = useState<Item[]>([]);
  const [loading, setLoading] = useState(false);
  // Only /fetch_initial sets this: it drives the scrape overlay, including re-submits
  // where the previous grid is still on screen. `loading` also covers rerank/feedback.
  const [searching, setSearching] = useState(false);
  const [traitPicks, setTraitPicks] = useState<Record<string, TraitPicks>>({});
  // Aesthetics are global: one list per upload, not per item. Kept in step with the
  // server's append-only history, which is also keyed by upload.
  const [aesthetics, setAesthetics] = useState<string[]>([]);
  const aestheticsUploadId = useRef<any>(null);
  // Feedbacks accumulated since the last catalogue-page fetch. A new page is
  // pulled only every FETCH_EVERY feedbacks, so most taps stay cheap.
  const [feedbacksSinceFetch, setFeedbacksSinceFetch] = useState(0);
  // The most recent feedback event for the current upload, used to preview an undo.
  // Fetched from the server so it stays in step with the append-only history.
  const [lastFeedback, setLastFeedback] = useState<{ item_url: string; feedback_type: string; concept?: string | null; aesthetic?: string | null } | null>(null);
  const [confirmingUndo, setConfirmingUndo] = useState(false);
  const [fetchingMore, setFetchingMore] = useState(false);
  const FETCH_EVERY = 3;

  const traitProfile = useTraitProfile();

  const loadTraitProfile = traitProfile.actions.loadTraitProfile;
  const clearTraitProfile = traitProfile.actions.clearTraitProfile;

  const scrapeProducts = async (uploadId: any, keyword: string, filters: any) => {
    if (!keyword.trim()) {
      throw new Error('Please provide or parse a lookup keyword first.');
    }
    if (!uploadId) {
      throw new Error('Upload an image before searching.');
    }
    const price = Number(filters.maxPrice);
    if (filters.maxPrice !== '' && (!Number.isFinite(price) || price < 0)) {
      throw new Error('Enter a valid non-negative price cap.');
    }

    setLoading(true);
    setSearching(true);
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

      setProducts(poolData.pool || []);
      setTraitPicks({});
      // Feedback history is stored per upload, so a re-scrape of the same upload keeps
      // steering; only a new upload starts from a clean style list.
      if (aestheticsUploadId.current !== uploadId) {
        aestheticsUploadId.current = uploadId;
        setAesthetics([]);
      }
      setFeedbacksSinceFetch(0);
      setLastFeedback(null);
      clearTraitProfile();
    } catch (err) {
      throw err instanceof Error ? err : new Error('Failed fetching items with the chosen keyword.');
    } finally {
      setLoading(false);
      setSearching(false);
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

      if (concept) {
        setTraitPicks(prev => ({
          ...prev,
          [itemUrl]: { ...prev[itemUrl], [concept]: feedbackType },
        }));
      }

      setFeedbacksSinceFetch(willFetch ? 0 : feedbacksSinceFetch + eventsCount);

      // Refresh the last-feedback preview so the undo button stays in step.
      await fetchLastFeedback(uploadId);

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
      setTraitPicks(prev => ({ ...prev, [itemUrl]: picks }));

      setFeedbacksSinceFetch(willFetch ? 0 : feedbacksSinceFetch + eventsCount);

      // Refresh the last-feedback preview so the undo button stays in step.
      await fetchLastFeedback(uploadId);

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
      setAesthetics(prev => (
        active
          ? prev.filter(value => value.toLowerCase() !== normalized.toLowerCase())
          : [...prev, normalized]
      ));

      setFeedbacksSinceFetch(willFetch ? 0 : feedbacksSinceFetch + eventsCount);

      // Refresh the last-feedback preview so the undo button stays in step.
      await fetchLastFeedback(uploadId);
    } catch (err) {
      throw err instanceof Error ? err : new Error('Vector calculation error');
    } finally {
      setFetchingMore(false);
      setLoading(false);
    }
  };

  const fetchLastFeedback = async (uploadId: any) => {
    try {
      const fb = await apiFetchLastFeedback(uploadId);
      setLastFeedback(fb ?? null);
    } catch {
      // No feedback to undo: hide the undo button.
      setLastFeedback(null);
    }
  };

  const confirmUndo = async (uploadId: any) => {
    setConfirmingUndo(true);
    try {
      const rankedData = await undoFeedback({ upload_id: uploadId, fetch_more: false });
      setProducts(rankedData.pool || []);
      // Undo still never fetches a page, but it gives back the cadence slot the removed
      // event consumed: "rate another 2" → add feedback → "1" → undo → back to "2".
      // Clamp at zero — an event undone just after a page fetch already had its slot reset.
      setFeedbacksSinceFetch(prev => Math.max(0, prev - 1));
      await fetchLastFeedback(uploadId);
    } catch (err: any) {
      throw new Error(err?.message || 'Undo failed');
    } finally {
      setConfirmingUndo(false);
    }
  };

  // The undo bar covers physical trait picks and visual MORE/LESS card taps. Aesthetic
  // phrases are excluded: they are undone by untoggling their StyleStrip chip.
  const undoPreview = (() => {
    if (!lastFeedback || lastFeedback.aesthetic) return null;
    if (lastFeedback.concept) return `${lastFeedback.feedback_type} ${lastFeedback.concept}`;
    const item = products.find(p => p.url === lastFeedback.item_url);
    // Card titles pack brand/condition/size/price after the first comma; the undo preview
    // only needs the product name, quoted for clarity.
    const name = item ? item.title.split(',')[0].trim() : 'a card';
    return `${lastFeedback.feedback_type} like \`${name}\``;
  })();

  return {
    state: {
      products,
      loading,
      searching,
      traitPicks,
      aesthetics,
      feedbacksSinceFetch,
      fetchingMore,
      lastFeedback,
      undoPreview,
      confirmingUndo,
      traitProfile: traitProfile.state.traitProfile,
      profileError: traitProfile.state.profileError,
    },
    actions: {
      scrapeProducts,
      rerankProducts,
      applyTraitPicks,
      toggleAesthetic,
      loadTraitProfile,
      fetchLastFeedback,
      confirmUndo,
    },
  };
}
