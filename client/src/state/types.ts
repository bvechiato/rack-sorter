import type { components } from '../types/api';
import type { Trait } from '../static/constants';

export type Item = components['schemas']['ItemResponse'];
export type TraitProfile = components['schemas']['TraitProfileResponse'];

export type Direction = 'MORE' | 'LESS';
export type TraitPicks = Partial<Record<Trait, Direction>>;

/** Shape returned by GET /feedback/last, kept as-is so the preview stays server-truthful. */
export interface LastFeedback {
  item_url: string;
  feedback_type: string;
  concept?: string | null;
  aesthetic?: string | null;
}

/**
 * One value for "what the client is doing". Replaces independent busy flags so states
 * that cannot coexist (scraping vs reranking vs undoing) are unrepresentable.
 */
export type SearchStatus =
  | { kind: 'idle' }
  | { kind: 'scraping' }
  | { kind: 'reranking'; fetchMore: boolean };

/** Explicit undo flow: no bar → preview → confirm → in-flight. */
export type UndoStage = 'hidden' | 'preview' | 'confirming' | 'undoing';

/** A catalogue page is pulled after this many feedback events. */
export const FETCH_EVERY = 3;

/** Aesthetic events are global, so they carry a required but ignored item field. */
export const GLOBAL_FEEDBACK_ITEM_URL = 'global';
