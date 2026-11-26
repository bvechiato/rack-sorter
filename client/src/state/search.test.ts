import { describe, expect, it } from 'vitest';
import {
  initialSearchState,
  searchReducer,
  selectUndoing,
  selectFetchingMore,
  selectLoading,
  selectSearching,
  selectUndoPreview,
} from './search';
import type { SearchAction, SearchState } from './search';
import type { Item, LastFeedback, TraitProfile } from './types';

const pool = (url: string): Item[] => [
  {
    url,
    image_url: `${url}.jpg`,
    title: 'Blue linen shirt, Brand: X, Size: S, 12.00 £',
    similarity_score: 0.8,
  } as Item,
];

const event = (overrides: Partial<LastFeedback> = {}): LastFeedback => ({
  item_url: 'u1',
  feedback_type: 'MORE',
  concept: null,
  aesthetic: null,
  ...overrides,
});

function run(state: SearchState, ...actions: SearchAction[]): SearchState {
  return actions.reduce(searchReducer, state);
}

describe('search status union', () => {
  it('derives every render flag from one status value', () => {
    const scraping = searchReducer(initialSearchState, { type: 'SCRAPE_START' });
    expect(selectLoading(scraping)).toBe(true);
    expect(selectSearching(scraping)).toBe(true);
    expect(selectFetchingMore(scraping)).toBe(false);
    expect(selectUndoing(scraping)).toBe(false);

    const reranking = searchReducer(initialSearchState, {
      type: 'RERANK_START',
      fetchMore: true,
    });
    expect(selectLoading(reranking)).toBe(true);
    expect(selectSearching(reranking)).toBe(false);
    expect(selectFetchingMore(reranking)).toBe(true);
    expect(selectUndoing(reranking)).toBe(false);

    const undoing = searchReducer(initialSearchState, { type: 'UNDO_START' });
    expect(selectLoading(undoing)).toBe(false);
    expect(selectUndoing(undoing)).toBe(true);
    expect(selectFetchingMore(undoing)).toBe(false);
  });

  it('returns to idle when a request fails', () => {
    const failed = run(
      initialSearchState,
      { type: 'SCRAPE_START' },
      { type: 'REQUEST_FAILED' },
    );
    expect(failed.status).toEqual({ kind: 'idle' });
    expect(selectLoading(failed)).toBe(false);
  });
});

describe('search pool transitions', () => {
  it('resets steering, cadence, undo and profile on a new search', () => {
    const steered = run(
      initialSearchState,
      { type: 'VISUAL_FEEDBACK_SUCCESS', pool: pool('u1'), eventsCount: 1, fetchMore: false },
      {
        type: 'TRAIT_PICKS_SUCCESS',
        pool: pool('u1'),
        eventsCount: 1,
        fetchMore: false,
        itemUrl: 'u1',
        picks: { fit: 'MORE' },
      },
      { type: 'LAST_FEEDBACK_RECEIVED', event: event() },
      { type: 'UNDO_REQUEST' },
      { type: 'PROFILE_LOAD_SUCCESS', profile: { axes: [] } as unknown as TraitProfile },
    );

    const reset = searchReducer(steered, {
      type: 'SCRAPE_SUCCESS',
      pool: pool('u2'),
      uploadId: 2,
    });

    expect(reset.products).toEqual(pool('u2'));
    expect(reset.traitPicks).toEqual({});
    expect(reset.feedbacksSinceFetch).toBe(0);
    expect(reset.lastFeedback).toBeNull();
    expect(reset.undoStage).toBe('hidden');
    expect(reset.traitProfile).toBeNull();
    expect(reset.profileError).toBeNull();
    expect(reset.status).toEqual({ kind: 'idle' });
  });

  it('keeps global aesthetics across a re-scrape but clears them for a new upload', () => {
    const aesthetic: SearchAction = {
      type: 'AESTHETIC_SUCCESS',
      pool: [],
      eventsCount: 1,
      fetchMore: false,
      phrase: 'formal',
      active: false,
    };
    // A toggle is only available after a pool exists, so the first scrape claims the
    // upload id before the aesthetic is added.
    const scraped = searchReducer(initialSearchState, {
      type: 'SCRAPE_SUCCESS',
      pool: [],
      uploadId: 7,
    });
    const steered = searchReducer(scraped, aesthetic);

    const sameUpload = searchReducer(steered, {
      type: 'SCRAPE_SUCCESS',
      pool: [],
      uploadId: 7,
    });
    expect(sameUpload.aesthetics).toEqual(['formal']);

    const newUpload = searchReducer(sameUpload, {
      type: 'SCRAPE_SUCCESS',
      pool: [],
      uploadId: 8,
    });
    expect(newUpload.aesthetics).toEqual([]);
  });

  it('toggles aesthetic phrases case-insensitively', () => {
    let state = searchReducer(initialSearchState, {
      type: 'AESTHETIC_SUCCESS',
      pool: [],
      eventsCount: 1,
      fetchMore: false,
      phrase: ' Formal ',
      active: false,
    });
    expect(state.aesthetics).toEqual(['Formal']);

    state = searchReducer(state, {
      type: 'AESTHETIC_SUCCESS',
      pool: [],
      eventsCount: 1,
      fetchMore: false,
      phrase: 'formal',
      active: true,
    });
    expect(state.aesthetics).toEqual([]);
  });

  it('accumulates the cadence counter and zeroes it on a page fetch', () => {
    let state = initialSearchState;
    for (let i = 0; i < 2; i += 1) {
      state = searchReducer(state, {
        type: 'VISUAL_FEEDBACK_SUCCESS',
        pool: [],
        eventsCount: 1,
        fetchMore: false,
      });
    }
    expect(state.feedbacksSinceFetch).toBe(2);

    state = searchReducer(state, {
      type: 'VISUAL_FEEDBACK_SUCCESS',
      pool: [],
      eventsCount: 1,
      fetchMore: true,
    });
    expect(state.feedbacksSinceFetch).toBe(0);
  });

  it('records a single trait pick and replaces the set applied by the Tune sheet', () => {
    let state = searchReducer(initialSearchState, {
      type: 'TRAIT_FEEDBACK_SUCCESS',
      pool: pool('u1'),
      eventsCount: 1,
      fetchMore: false,
      itemUrl: 'u1',
      concept: 'fit',
      feedbackType: 'MORE',
    });
    expect(state.traitPicks.u1).toEqual({ fit: 'MORE' });

    state = searchReducer(state, {
      type: 'TRAIT_PICKS_SUCCESS',
      pool: pool('u1'),
      eventsCount: 1,
      fetchMore: false,
      itemUrl: 'u1',
      picks: { sleeves: 'LESS' },
    });
    expect(state.traitPicks.u1).toEqual({ sleeves: 'LESS' });
  });
});

describe('undo flow', () => {
  it('moves hidden → preview → confirming → undoing → hidden and gives back a slot', () => {
    let state = run(
      initialSearchState,
      { type: 'VISUAL_FEEDBACK_SUCCESS', pool: [], eventsCount: 1, fetchMore: false },
      { type: 'VISUAL_FEEDBACK_SUCCESS', pool: [], eventsCount: 1, fetchMore: false },
    );
    expect(state.feedbacksSinceFetch).toBe(2);

    state = searchReducer(state, { type: 'LAST_FEEDBACK_RECEIVED', event: event() });
    expect(state.undoStage).toBe('preview');
    state = searchReducer(state, { type: 'UNDO_REQUEST' });
    expect(state.undoStage).toBe('confirming');
    state = searchReducer(state, { type: 'UNDO_CANCEL' });
    expect(state.undoStage).toBe('preview');

    state = run(state, { type: 'UNDO_REQUEST' }, { type: 'UNDO_START' });
    expect(state.undoStage).toBe('undoing');
    expect(selectUndoing(state)).toBe(true);

    state = searchReducer(state, { type: 'UNDO_SUCCESS', pool: [] });
    expect(state.undoStage).toBe('hidden');
    expect(state.feedbacksSinceFetch).toBe(1);
    expect(selectUndoing(state)).toBe(false);
  });

  it('clamps the cadence slot at zero and promotes the next event to preview', () => {
    let state = run(
      initialSearchState,
      { type: 'LAST_FEEDBACK_RECEIVED', event: event() },
      { type: 'UNDO_REQUEST' },
      { type: 'UNDO_START' },
      { type: 'UNDO_SUCCESS', pool: [] },
    );
    expect(state.feedbacksSinceFetch).toBe(0);

    state = searchReducer(state, {
      type: 'LAST_FEEDBACK_RECEIVED',
      event: event({ feedback_type: 'LESS', concept: 'sleeves' }),
    });
    expect(state.undoStage).toBe('preview');
    expect(selectUndoPreview(state)).toBe('LESS sleeves');
  });

  it('hides the bar for aesthetic events and never drops a confirmation mid-flight', () => {
    const aestheticOnly = searchReducer(initialSearchState, {
      type: 'LAST_FEEDBACK_RECEIVED',
      event: event({ aesthetic: 'formal' }),
    });
    expect(aestheticOnly.undoStage).toBe('hidden');
    expect(selectUndoPreview(aestheticOnly)).toBeNull();

    const confirming = run(
      initialSearchState,
      { type: 'LAST_FEEDBACK_RECEIVED', event: event() },
      { type: 'UNDO_REQUEST' },
      { type: 'LAST_FEEDBACK_RECEIVED', event: null },
    );
    expect(confirming.undoStage).toBe('confirming');
  });

  it('reopens the confirmation when undo fails', () => {
    const failed = run(
      initialSearchState,
      { type: 'LAST_FEEDBACK_RECEIVED', event: event() },
      { type: 'UNDO_REQUEST' },
      { type: 'UNDO_START' },
      { type: 'UNDO_ERROR' },
    );
    expect(failed.undoStage).toBe('confirming');
    expect(failed.status).toEqual({ kind: 'idle' });
  });

  it('ignores a cancel during undo and never reopens a settled confirmation', () => {
    const undoing = run(
      initialSearchState,
      { type: 'LAST_FEEDBACK_RECEIVED', event: event() },
      { type: 'UNDO_REQUEST' },
      { type: 'UNDO_START' },
    );
    expect(searchReducer(undoing, { type: 'UNDO_CANCEL' }).undoStage).toBe('undoing');

    const settled = searchReducer(undoing, { type: 'UNDO_SUCCESS', pool: [] });
    expect(searchReducer(settled, { type: 'UNDO_ERROR' }).undoStage).toBe('hidden');
  });

  it('previews a visual tap with just the product name', () => {
    const state = run(
      initialSearchState,
      { type: 'VISUAL_FEEDBACK_SUCCESS', pool: pool('u2'), eventsCount: 1, fetchMore: false },
      { type: 'LAST_FEEDBACK_RECEIVED', event: event({ item_url: 'u2' }) },
    );
    expect(selectUndoPreview(state)).toBe('MORE like `Blue linen shirt`');
  });
});

describe('trait profile state', () => {
  it('records a load, keeps stale axes on failure, and clears on request', () => {
    const profile = { axes: [] } as unknown as TraitProfile;
    let state = run(
      initialSearchState,
      { type: 'PROFILE_LOAD_START' },
      { type: 'PROFILE_LOAD_SUCCESS', profile },
    );
    expect(state.traitProfile).toBe(profile);
    expect(state.profileError).toBeNull();

    state = searchReducer(state, { type: 'PROFILE_LOAD_ERROR', message: 'no vectors' });
    expect(state.profileError).toBe('no vectors');
    expect(state.traitProfile).toBe(profile);

    state = searchReducer(state, { type: 'SCRAPE_SUCCESS', pool: [], uploadId: 9 });
    expect(state.traitProfile).toBeNull();
    expect(state.profileError).toBeNull();
  });
});
