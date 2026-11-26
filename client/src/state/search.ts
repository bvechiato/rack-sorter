import type { Trait } from '../static/constants';
import { FETCH_EVERY } from './types';
import type {
  Direction,
  Item,
  LastFeedback,
  SearchStatus,
  TraitPicks,
  TraitProfile,
  UndoStage,
} from './types';

export interface SearchState {
  products: Item[];
  status: SearchStatus;
  traitPicks: Record<string, TraitPicks>;
  aesthetics: string[];
  /** Upload the aesthetic list belongs to; a different upload starts a clean list. */
  aestheticsUploadId: number | null;
  feedbacksSinceFetch: number;
  lastFeedback: LastFeedback | null;
  undoStage: UndoStage;
  traitProfile: TraitProfile | null;
  profileError: string | null;
}

export const initialSearchState: SearchState = {
  products: [],
  status: { kind: 'idle' },
  traitPicks: {},
  aesthetics: [],
  aestheticsUploadId: null,
  feedbacksSinceFetch: 0,
  lastFeedback: null,
  undoStage: 'hidden',
  traitProfile: null,
  profileError: null,
};

export type SearchAction =
  | { type: 'SCRAPE_START' }
  | { type: 'SCRAPE_SUCCESS'; pool: Item[]; uploadId: number }
  | { type: 'RERANK_START'; fetchMore: boolean }
  | { type: 'VISUAL_FEEDBACK_SUCCESS'; pool: Item[]; eventsCount: number; fetchMore: boolean }
  | {
      type: 'TRAIT_FEEDBACK_SUCCESS';
      pool: Item[];
      eventsCount: number;
      fetchMore: boolean;
      itemUrl: string;
      concept: Trait;
      feedbackType: Direction;
    }
  | {
      type: 'TRAIT_PICKS_SUCCESS';
      pool: Item[];
      eventsCount: number;
      fetchMore: boolean;
      itemUrl: string;
      picks: TraitPicks;
    }
  | {
      type: 'AESTHETIC_SUCCESS';
      pool: Item[];
      eventsCount: number;
      fetchMore: boolean;
      phrase: string;
      active: boolean;
    }
  | { type: 'REQUEST_FAILED' }
  | { type: 'LAST_FEEDBACK_RECEIVED'; event: LastFeedback | null }
  | { type: 'UNDO_REQUEST' }
  | { type: 'UNDO_CANCEL' }
  | { type: 'UNDO_START' }
  | { type: 'UNDO_SUCCESS'; pool: Item[] }
  | { type: 'UNDO_ERROR' }
  | { type: 'PROFILE_LOAD_START' }
  | { type: 'PROFILE_LOAD_SUCCESS'; profile: TraitProfile }
  | { type: 'PROFILE_LOAD_ERROR'; message: string };

/** Aesthetic phrases are removed by their StyleStrip chip, never by the undo bar. */
function isUndoable(event: LastFeedback | null): boolean {
  return Boolean(event && !event.aesthetic);
}

/** Shared by the commands that decide whether a tap pulls another catalogue page. */
export const shouldFetchMore = (feedbacksSinceFetch: number, eventsCount: number): boolean =>
  feedbacksSinceFetch + eventsCount >= FETCH_EVERY;

const nextCadence = (count: number, eventsCount: number, fetchMore: boolean): number =>
  fetchMore ? 0 : count + eventsCount;

function applyRerank(
  state: SearchState,
  pool: Item[],
  eventsCount: number,
  fetchMore: boolean,
): SearchState {
  return {
    ...state,
    products: pool || [],
    feedbacksSinceFetch: nextCadence(state.feedbacksSinceFetch, eventsCount, fetchMore),
    status: { kind: 'idle' },
  };
}

export function searchReducer(state: SearchState, action: SearchAction): SearchState {
  switch (action.type) {
    case 'SCRAPE_START':
      return { ...state, status: { kind: 'scraping' } };

    case 'SCRAPE_SUCCESS':
      return {
        ...state,
        products: action.pool || [],
        status: { kind: 'idle' },
        traitPicks: {},
        aesthetics:
          state.aestheticsUploadId !== action.uploadId ? [] : state.aesthetics,
        aestheticsUploadId: action.uploadId,
        feedbacksSinceFetch: 0,
        lastFeedback: null,
        undoStage: 'hidden',
        traitProfile: null,
        profileError: null,
      };

    case 'RERANK_START':
      return { ...state, status: { kind: 'reranking', fetchMore: action.fetchMore } };

    case 'VISUAL_FEEDBACK_SUCCESS':
      return applyRerank(state, action.pool, action.eventsCount, action.fetchMore);

    case 'TRAIT_FEEDBACK_SUCCESS':
      return {
        ...applyRerank(state, action.pool, action.eventsCount, action.fetchMore),
        traitPicks: {
          ...state.traitPicks,
          [action.itemUrl]: { ...state.traitPicks[action.itemUrl], [action.concept]: action.feedbackType },
        },
      };

    case 'TRAIT_PICKS_SUCCESS':
      return {
        ...applyRerank(state, action.pool, action.eventsCount, action.fetchMore),
        traitPicks: { ...state.traitPicks, [action.itemUrl]: action.picks },
      };

    case 'AESTHETIC_SUCCESS': {
      const phrase = action.phrase.trim();
      return {
        ...applyRerank(state, action.pool, action.eventsCount, action.fetchMore),
        aesthetics: action.active
          ? state.aesthetics.filter(value => value.toLowerCase() !== phrase.toLowerCase())
          : [...state.aesthetics, phrase],
      };
    }

    case 'REQUEST_FAILED':
      return { ...state, status: { kind: 'idle' } };

    case 'LAST_FEEDBACK_RECEIVED':
      return {
        ...state,
        lastFeedback: action.event,
        // Never yank a confirmation dialog away from the user mid-confirm; otherwise
        // a newly fetched event promotes an idle bar into the preview stage.
        undoStage:
          state.undoStage === 'confirming' || state.undoStage === 'undoing'
            ? state.undoStage
            : isUndoable(action.event)
              ? 'preview'
              : 'hidden',
      };

    case 'UNDO_REQUEST':
      return state.undoStage === 'preview'
        ? { ...state, undoStage: 'confirming' }
        : state;

    case 'UNDO_CANCEL':
      return state.undoStage === 'confirming'
        ? {
            ...state,
            undoStage: isUndoable(state.lastFeedback) ? 'preview' : 'hidden',
          }
        : state;

    // Only the undo stage tracks the in-flight operation; `status` stays idle so cards
    // remain interactive, matching the pre-refactor behaviour.
    case 'UNDO_START':
      return { ...state, undoStage: 'undoing' };

    case 'UNDO_SUCCESS':
      // The just-undone event is still in state; hide now, then LAST_FEEDBACK_RECEIVED
      // promotes the bar to the next-most-recent event, or leaves it hidden.
      return {
        ...state,
        products: action.pool || [],
        feedbacksSinceFetch: Math.max(0, state.feedbacksSinceFetch - 1),
        undoStage: 'hidden',
      };

    // Never resurrect a confirmation the user cancelled while undo was in flight.
    case 'UNDO_ERROR':
      return state.undoStage === 'undoing'
        ? { ...state, undoStage: 'confirming' }
        : state;

    case 'PROFILE_LOAD_START':
      return { ...state, profileError: null };

    case 'PROFILE_LOAD_SUCCESS':
      return { ...state, traitProfile: action.profile };

    case 'PROFILE_LOAD_ERROR':
      return { ...state, profileError: action.message };

    default:
      return state;
  }
}

export const selectLoading = (state: SearchState): boolean =>
  state.status.kind === 'scraping' || state.status.kind === 'reranking';

export const selectSearching = (state: SearchState): boolean =>
  state.status.kind === 'scraping';

export const selectFetchingMore = (state: SearchState): boolean =>
  state.status.kind === 'reranking' && state.status.fetchMore;

export const selectUndoing = (state: SearchState): boolean =>
  state.undoStage === 'undoing';

/** Human-readable label for the undo bar, derived from server feedback + current pool. */
export function selectUndoPreview(state: SearchState): string | null {
  const { lastFeedback } = state;
  if (!lastFeedback || lastFeedback.aesthetic) return null;
  if (lastFeedback.concept) return `${lastFeedback.feedback_type} ${lastFeedback.concept}`;

  const item = state.products.find(product => product.url === lastFeedback.item_url);
  // Card titles pack brand/condition/size/price after the first comma; only the name is
  // needed here, quoted for clarity.
  const name = item ? item.title.split(',')[0].trim() : 'a card';
  return `${lastFeedback.feedback_type} like \`${name}\``;
}
