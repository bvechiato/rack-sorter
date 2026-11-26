import {
  analyzeFile,
  fetchInitial,
  fetchLastFeedback as apiFetchLastFeedback,
  fetchTraitProfile,
  rerankBatch,
  undoFeedback,
} from '../api';
import type { Trait } from '../static/constants';
import { shouldFetchMore } from './search';
import type { AppAction, AppState } from './store';
import { GLOBAL_FEEDBACK_ITEM_URL } from './types';
import type { Direction, TraitPicks } from './types';

export interface CommandContext {
  state: AppState;
  dispatch: (action: AppAction) => void;
}

/** A state-layer effect: observes the current state, performs I/O, emits events. */
export type Command = (context: CommandContext) => Promise<void>;

const MAX_UPLOAD_BYTES = 10 * 1024 * 1024;

export function analyzeImage(file: File | null): Command {
  return async ({ dispatch }) => {
    if (!file) return;
    if (!file.type.startsWith('image/')) throw new Error('Please choose an image file.');
    if (file.size === 0) throw new Error('The selected image is empty.');
    if (file.size > MAX_UPLOAD_BYTES) throw new Error('Image is too large (max 10 MB).');

    dispatch({ type: 'UPLOAD_START' });
    try {
      const data = await analyzeFile(file);
      dispatch({ type: 'UPLOAD_SUCCESS', uploadId: data.upload_id, analysis: data.analysis });
      // The undo preview is server-truthful, so a new session fetches its last event
      // right here instead of making the view watch `uploadId` for changes.
      await fetchLastFeedback(data.upload_id)({ dispatch });
    } catch (err) {
      dispatch({ type: 'UPLOAD_FAILURE' });
      throw err instanceof Error ? err : new Error('Image analysis failed');
    }
  };
}

/** This effect only emits events; it never needs to read state. */
export function fetchLastFeedback(uploadId: number): (context: Pick<CommandContext, 'dispatch'>) => Promise<void> {
  return async ({ dispatch }) => {
    try {
      const event = await apiFetchLastFeedback(uploadId);
      dispatch({ type: 'LAST_FEEDBACK_RECEIVED', event: event ?? null });
    } catch {
      // No feedback to undo: hide the undo button.
      dispatch({ type: 'LAST_FEEDBACK_RECEIVED', event: null });
    }
  };
}

export function search(): Command {
  return async ({ state, dispatch }) => {
    const keyword = state.analysis.confirmedKeyword;
    const uploadId = state.analysis.uploadId;
    const filters = state.filters;

    if (!keyword.trim()) throw new Error('Please provide or parse a lookup keyword first.');
    if (!uploadId) throw new Error('Upload an image before searching.');
    const price = Number(filters.maxPrice);
    if (filters.maxPrice !== '' && (!Number.isFinite(price) || price < 0)) {
      throw new Error('Enter a valid non-negative price cap.');
    }

    dispatch({ type: 'SCRAPE_START' });
    try {
      const requestData = {
        uploadId: Number(uploadId),
        keyword,
        selectedSizes: filters.selectedSizes.join(','),
        selectedCategory: filters.selectedCategory,
        selectedColors: filters.selectedColors.join(','),
        maxPrice: String(filters.maxPrice),
        selectedConditions: filters.selectedConditions.join(','),
      };
      const poolData = await fetchInitial(requestData);
      console.log(`[INFO] Sending scrape request with filters: ${JSON.stringify(requestData)}`);
      dispatch({ type: 'SCRAPE_SUCCESS', pool: poolData.pool || [], uploadId });
    } catch (err) {
      dispatch({ type: 'REQUEST_FAILED' });
      throw err instanceof Error ? err : new Error('Failed fetching items with the chosen keyword.');
    }
  };
}

/** MORE/LESS on a card, optionally naming a physical trait. */
export function rerank(itemUrl: string, feedbackType: Direction, concept?: Trait): Command {
  return async ({ state, dispatch }) => {
    const uploadId = state.analysis.uploadId;
    if (!uploadId) throw new Error('Missing upload id');

    const eventsCount = 1;
    const willFetch = shouldFetchMore(state.search.feedbacksSinceFetch, eventsCount);
    dispatch({ type: 'RERANK_START', fetchMore: willFetch });

    try {
      const rankedData = await rerankBatch({
        upload_id: uploadId,
        feedback: [{ item_url: itemUrl, feedback_type: feedbackType, concept: concept ?? null }],
        fetch_more: willFetch,
      });
      const common = { pool: rankedData.pool || [], eventsCount, fetchMore: willFetch };
      if (concept) {
        dispatch({ type: 'TRAIT_FEEDBACK_SUCCESS', ...common, itemUrl, concept, feedbackType });
      } else {
        dispatch({ type: 'VISUAL_FEEDBACK_SUCCESS', ...common });
      }
      await fetchLastFeedback(uploadId)({ dispatch });
    } catch (err) {
      dispatch({ type: 'REQUEST_FAILED' });
      throw err instanceof Error ? err : new Error('Vector calculation error');
    }
  };
}

/** The Tune sheet sends all queued physical picks together on Done. */
export function applyTraitPicks(itemUrl: string, picks: TraitPicks): Command {
  return async ({ state, dispatch }) => {
    const uploadId = state.analysis.uploadId;
    if (!uploadId) throw new Error('Missing upload id');

    const feedback = (Object.entries(picks) as [Trait, Direction][]).map(
      ([concept, feedback_type]) => ({ item_url: itemUrl, feedback_type, concept }),
    );
    if (!feedback.length) return;

    const eventsCount = feedback.length;
    const willFetch = shouldFetchMore(state.search.feedbacksSinceFetch, eventsCount);
    dispatch({ type: 'RERANK_START', fetchMore: willFetch });
    try {
      const rankedData = await rerankBatch({
        upload_id: uploadId,
        feedback,
        fetch_more: willFetch,
      });
      dispatch({
        type: 'TRAIT_PICKS_SUCCESS',
        pool: rankedData.pool || [],
        eventsCount,
        fetchMore: willFetch,
        itemUrl,
        picks,
      });
      await fetchLastFeedback(uploadId)({ dispatch });
      await loadTraitProfile(itemUrl)({ state, dispatch });
    } catch (err) {
      dispatch({ type: 'REQUEST_FAILED' });
      throw err instanceof Error ? err : new Error('Vector calculation error');
    }
  };
}

/**
 * Toggles one global style phrase. The phrase carries the intent, so `feedback_type`
 * is only the switch (MORE = steer toward it, LESS = remove it). `item_url` is a
 * required carrier field the aesthetic lane ignores — there is no "clicked item".
 */
export function toggleAesthetic(phrase: string): Command {
  return async ({ state, dispatch }) => {
    const uploadId = state.analysis.uploadId;
    if (!uploadId) throw new Error('Missing upload id');

    const normalized = phrase.trim();
    if (!normalized) return;
    const active = state.search.aesthetics.some(
      value => value.toLowerCase() === normalized.toLowerCase(),
    );
    const eventsCount = 1;
    const willFetch = shouldFetchMore(state.search.feedbacksSinceFetch, eventsCount);
    dispatch({ type: 'RERANK_START', fetchMore: willFetch });

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
      dispatch({
        type: 'AESTHETIC_SUCCESS',
        pool: rankedData.pool || [],
        eventsCount,
        fetchMore: willFetch,
        phrase: normalized,
        active,
      });
      await fetchLastFeedback(uploadId)({ dispatch });
    } catch (err) {
      dispatch({ type: 'REQUEST_FAILED' });
      throw err instanceof Error ? err : new Error('Vector calculation error');
    }
  };
}

export function confirmUndo(): Command {
  return async ({ state, dispatch }) => {
    const uploadId = state.analysis.uploadId;
    dispatch({ type: 'UNDO_START' });
    try {
      const rankedData = await undoFeedback({ upload_id: uploadId, fetch_more: false });
      dispatch({ type: 'UNDO_SUCCESS', pool: rankedData.pool || [] });
      await fetchLastFeedback(uploadId)({ dispatch });
    } catch (err: any) {
      // Reopen the confirmation so the user can retry or cancel.
      dispatch({ type: 'UNDO_ERROR' });
      throw new Error(err?.message || 'Undo failed');
    }
  };
}

/** Opening the sheet also loads its debug radar; the view only sends the intent. */
export function openTraitSheet(itemUrl: string): Command {
  return async (context) => {
    context.dispatch({ type: 'OPEN_TRAIT_SHEET', itemUrl });
    await loadTraitProfile(itemUrl)(context);
  };
}

export function loadTraitProfile(itemUrl?: string): Command {
  return async ({ state, dispatch }) => {
    const uploadId = state.analysis.uploadId;
    if (!uploadId) return;
    dispatch({ type: 'PROFILE_LOAD_START' });
    try {
      const profile = await fetchTraitProfile(Number(uploadId), itemUrl);
      dispatch({ type: 'PROFILE_LOAD_SUCCESS', profile });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Trait profile unavailable';
      console.warn('[WARN] Trait profile failed:', message);
      dispatch({ type: 'PROFILE_LOAD_ERROR', message });
    }
  };
}
