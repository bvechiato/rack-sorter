import { beforeEach, describe, expect, it, vi } from 'vitest';
import {
  analyzeFile,
  fetchInitial,
  fetchLastFeedback,
  fetchTraitProfile,
  rerankBatch,
  undoFeedback,
} from '../api';
import * as commands from './commands';
import { selectSearching, selectUndoPreview } from './search';
import { appReducer, createInitialState } from './store';
import type { AppAction, AppState } from './store';

vi.mock('../api', () => ({
  analyzeFile: vi.fn(),
  fetchInitial: vi.fn(),
  fetchTraitProfile: vi.fn(),
  fetchLastFeedback: vi.fn(),
  rerankBatch: vi.fn(),
  undoFeedback: vi.fn(),
}));

/** Commands are tested against the real root reducer, but without mounting React. */
function harness(initial: AppState = createInitialState()) {
  let state = initial;
  const emitted: AppAction[] = [];
  const dispatch = (action: AppAction) => {
    emitted.push(action);
    state = appReducer(state, action);
  };
  return {
    emitted,
    get state() {
      return state;
    },
    ctx: () => ({ state, dispatch }),
  };
}

function withUpload(uploadId = 1): AppState {
  return appReducer(createInitialState(), {
    type: 'UPLOAD_SUCCESS',
    uploadId,
    analysis: {
      archetype: 'striped',
      classified_tags: ['striped', 'striped'],
      colour_archetype: 'Blue',
      colour_classified_tags: ['Blue', 'Red'],
      category_archetype: 'Tops',
    },
  });
}

beforeEach(() => {
  localStorage.clear();
  vi.clearAllMocks();
  vi.mocked(fetchLastFeedback).mockResolvedValue(null);
  vi.mocked(rerankBatch).mockResolvedValue({ pool: [] } as any);
});

describe('analyzeImage command', () => {
  const image = () => new File(['x'], 'shirt.jpg', { type: 'image/jpeg' });

  it('rejects invalid files before emitting any state change', async () => {
    const h = harness();
    await expect(
      commands.analyzeImage(new File(['x'], 'notes.txt', { type: 'text/plain' }))(h.ctx()),
    ).rejects.toThrow('Please choose an image file.');
    await expect(
      commands.analyzeImage(new File([new Uint8Array(10 * 1024 * 1024 + 1)], 'big.jpg', { type: 'image/jpeg' }))(h.ctx()),
    ).rejects.toThrow('Image is too large (max 10 MB).');

    expect(analyzeFile).not.toHaveBeenCalled();
    expect(h.emitted).toEqual([]);
  });

  it('starts before the request and fans the result out across the root state', async () => {
    vi.mocked(analyzeFile).mockResolvedValueOnce({
      upload_id: 7,
      analysis: {
        archetype: 'long sleeve',
        classified_tags: ['long sleeve', 'striped', 'long sleeve'],
        colour_archetype: 'Blue',
        colour_classified_tags: ['Blue', 'Red'],
        category_archetype: 'Tops',
      },
    } as any);
    const h = harness();

    const pending = commands.analyzeImage(image())(h.ctx());
    expect(h.emitted[0]).toEqual({ type: 'UPLOAD_START' });
    expect(h.state.analysis.loading).toBe(true);
    await pending;

    expect(h.state.analysis.uploadId).toBe(7);
    expect(h.state.analysis.suggestedKeywords).toEqual(['long sleeve', 'striped']);
    expect(h.state.filters.selectedCategory).toBe('Tops');
    expect(h.state.filters.selectedColors).toEqual(['Blue', 'Red']);
    expect(h.state.ui.preferencesOpen).toBe(true);
    expect(h.emitted.some(action => action.type === 'LAST_FEEDBACK_RECEIVED')).toBe(true);
  });

  it('clears loading and surfaces the real error on failure', async () => {
    vi.mocked(analyzeFile).mockRejectedValueOnce(new Error('Analysis crashed'));
    const h = harness();

    await expect(commands.analyzeImage(image())(h.ctx())).rejects.toThrow('Analysis crashed');
    expect(h.state.analysis.loading).toBe(false);
    expect(h.state.analysis.uploadId).toBeNull();
  });
});

describe('search command', () => {
  it('rejects missing keyword, missing upload and invalid price before the API call', async () => {
    await expect(commands.search()(harness().ctx())).rejects.toThrow(
      'Please provide or parse a lookup keyword first.',
    );
    const keywordOnly = appReducer(createInitialState(), {
      type: 'KEYWORD_CHANGED',
      value: 'striped',
    });
    await expect(commands.search()(harness(keywordOnly).ctx())).rejects.toThrow(
      'Upload an image before searching.',
    );

    const badPrice = appReducer(withUpload(), { type: 'SET_MAX_PRICE', value: '-5' });
    await expect(commands.search()(harness(badPrice).ctx())).rejects.toThrow(
      'Enter a valid non-negative price cap.',
    );
    expect(fetchInitial).not.toHaveBeenCalled();
  });

  it('keeps the scraping status until the request settles, including a re-submit', async () => {
    let resolveFetch: ((value: any) => void) | undefined;
    vi.mocked(fetchInitial).mockReturnValueOnce(
      new Promise<any>(resolve => {
        resolveFetch = resolve;
      }),
    );
    const h = harness(withUpload());

    const pending = commands.search()(h.ctx());
    expect(selectSearching(h.state.search)).toBe(true);
    await Promise.resolve();

    resolveFetch?.({ pool: [] });
    await pending;
    expect(selectSearching(h.state.search)).toBe(false);
  });

  it('passes the real fetch error through and returns to idle', async () => {
    vi.mocked(fetchInitial).mockRejectedValueOnce(new Error('Upstream 502'));
    const h = harness(withUpload());

    await expect(commands.search()(h.ctx())).rejects.toThrow('Upstream 502');
    expect(h.state.search.status).toEqual({ kind: 'idle' });
  });
});

describe('feedback commands', () => {
  it('asks for a page on the third feedback event', async () => {
    const h = harness(withUpload());
    for (let i = 0; i < 3; i += 1) {
      await commands.rerank(`u${i}`, 'MORE')(h.ctx());
    }

    expect(rerankBatch).toHaveBeenCalledTimes(3);
    expect(vi.mocked(rerankBatch).mock.calls[2][0]).toMatchObject({ fetch_more: true });
    expect(h.state.search.feedbacksSinceFetch).toBe(0);
  });

  it('derives the aesthetic switch from current state, so tapping an active chip removes it', async () => {
    const h = harness(withUpload());
    await commands.toggleAesthetic(' Formal ')(h.ctx());
    expect(h.state.search.aesthetics).toEqual(['Formal']);
    expect(vi.mocked(rerankBatch).mock.calls[0][0]).toMatchObject({
      feedback: [{ aesthetic: 'Formal', feedback_type: 'MORE' }],
    });

    await commands.toggleAesthetic('formal')(h.ctx());
    expect(h.state.search.aesthetics).toEqual([]);
    expect(vi.mocked(rerankBatch).mock.calls[1][0]).toMatchObject({
      feedback: [{ aesthetic: 'formal', feedback_type: 'LESS' }],
    });
  });

  it('keeps a server-provided undo preview and excludes aesthetic events', async () => {
    const h = harness(withUpload());
    vi.mocked(fetchLastFeedback).mockResolvedValueOnce({
      item_url: 'u1',
      feedback_type: 'LESS',
      concept: 'sleeves',
    } as any);
    await commands.fetchLastFeedback(1)(h.ctx());
    expect(selectUndoPreview(h.state.search)).toBe('LESS sleeves');

    const aesthetic = harness(withUpload());
    vi.mocked(fetchLastFeedback).mockResolvedValueOnce({
      item_url: 'global',
      feedback_type: 'MORE',
      aesthetic: 'formal',
    } as any);
    await commands.fetchLastFeedback(1)(aesthetic.ctx());
    expect(aesthetic.state.search.undoStage).toBe('hidden');
    expect(selectUndoPreview(aesthetic.state.search)).toBeNull();
  });
});

describe('undo command', () => {
  it('never fetches a page and gives back the cadence slot', async () => {
    const h = harness(withUpload());
    await commands.rerank('u1', 'MORE')(h.ctx());
    await commands.rerank('u2', 'MORE')(h.ctx());
    expect(h.state.search.feedbacksSinceFetch).toBe(2);

    vi.mocked(undoFeedback).mockResolvedValueOnce({ pool: [] } as any);
    await commands.confirmUndo()(h.ctx());

    expect(undoFeedback).toHaveBeenCalledWith({ upload_id: 1, fetch_more: false });
    expect(h.state.search.feedbacksSinceFetch).toBe(1);
    expect(h.state.search.undoStage).toBe('hidden');
  });

  it('clamps the cadence counter at zero and reopens confirmation on failure', async () => {
    const h = harness(withUpload());
    vi.mocked(undoFeedback).mockResolvedValueOnce({ pool: [] } as any);
    await commands.confirmUndo()(h.ctx());
    expect(h.state.search.feedbacksSinceFetch).toBe(0);

    const failed = harness(withUpload());
    vi.mocked(undoFeedback).mockRejectedValueOnce(new Error('undo broke'));
    await expect(commands.confirmUndo()(failed.ctx())).rejects.toThrow('undo broke');
    expect(failed.state.search.undoStage).toBe('confirming');
    expect(failed.state.search.status).toEqual({ kind: 'idle' });
  });
});

describe('trait profile command', () => {
  it('opening the sheet loads the debug radar in the same command', async () => {
    const profile = { axes: [] } as any;
    vi.mocked(fetchTraitProfile).mockResolvedValueOnce(profile);
    const h = harness(withUpload());

    await commands.openTraitSheet('u1')(h.ctx());
    expect(h.state.ui.traitSheetUrl).toBe('u1');
    expect(h.state.search.traitProfile).toBe(profile);
  });
});

describe('root state', () => {
  it('hydrates only persisted filter fields', () => {
    localStorage.setItem('rs_size_id', JSON.stringify(['S']));
    const state = createInitialState();
    expect(state.filters.selectedSizes).toEqual(['S']);
    expect(state.filters.selectedCategory).toBe('See all');
    expect(state.filters.selectedColors).toEqual([]);
  });
});
