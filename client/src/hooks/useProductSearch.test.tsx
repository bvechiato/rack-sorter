import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { fetchInitial, fetchLastFeedback, rerankBatch, undoFeedback } from '../api';
import { useProductSearch } from './useProductSearch';

vi.mock('../api', () => ({
  fetchInitial: vi.fn(),
  rerankBatch: vi.fn(),
  fetchTraitProfile: vi.fn(),
  fetchLastFeedback: vi.fn(),
  undoFeedback: vi.fn(),
}));

type SearchApi = ReturnType<typeof useProductSearch>;

const filters = {
  selectedSizes: [],
  selectedCategory: 'See all',
  selectedColors: [],
  maxPrice: '',
  selectedConditions: [],
};

(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;

function Probe({ onReady }: { onReady: (api: SearchApi) => void }) {
  onReady(useProductSearch());
  return null;
}

describe('useProductSearch.scrapeProducts validation', () => {
  let container: HTMLDivElement | undefined;
  let root: Root | undefined;
  let api: SearchApi;

  beforeEach(() => {
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
    act(() => {
      root.render(<Probe onReady={value => { api = value; }} />);
    });
  });

  afterEach(() => {
    if (root) {
      const activeRoot = root;
      act(() => activeRoot.unmount());
    }
    container?.remove();
    vi.clearAllMocks();
  });

  it('rejects a keyword-only search before calling the API', async () => {
    await expect(api.actions.scrapeProducts(null, 'striped', filters)).rejects.toThrow(
      'Upload an image before searching.',
    );
    expect(fetchInitial).not.toHaveBeenCalled();
  });

  it('rejects a negative price cap before calling the API', async () => {
    await expect(
      api.actions.scrapeProducts(1, 'striped', { ...filters, maxPrice: '-5' }),
    ).rejects.toThrow('Enter a valid non-negative price cap.');
    expect(fetchInitial).not.toHaveBeenCalled();
  });

  it('passes through the real fetch error', async () => {
    vi.mocked(fetchInitial).mockRejectedValueOnce(new Error('Upstream 502'));
    let caught: unknown;

    await act(async () => {
      try {
        await api.actions.scrapeProducts(1, 'striped', filters);
      } catch (err) {
        caught = err;
      }
    });

    expect((caught as Error).message).toBe('Upstream 502');
  });

  it('keeps the searching flag on for the whole scrape, including a re-submit', async () => {
    let resolveFetch: ((value: any) => void) | undefined;
    vi.mocked(fetchInitial).mockReturnValueOnce(new Promise<any>(resolve => {
      resolveFetch = resolve;
    }));

    await act(async () => {
      void api.actions.scrapeProducts(1, 'striped', filters);
    });
    expect(api.state.searching).toBe(true);

    await act(async () => {
      resolveFetch?.({ pool: [] });
    });
    expect(api.state.searching).toBe(false);
  });
});

describe('useProductSearch undo', () => {
  let container: HTMLDivElement | undefined;
  let root: Root | undefined;
  let api: SearchApi;

  beforeEach(() => {
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
    act(() => {
      root.render(<Probe onReady={value => { api = value; }} />);
    });
  });

  afterEach(() => {
    if (root) {
      const activeRoot = root;
      act(() => activeRoot.unmount());
    }
    container?.remove();
    vi.clearAllMocks();
  });

  it('confirmUndo never fetches more and clamps the cadence counter at zero', async () => {
    vi.mocked(undoFeedback).mockResolvedValueOnce({ pool: [] });
    vi.mocked(fetchLastFeedback).mockResolvedValueOnce(null);

    await act(async () => {
      await api.actions.confirmUndo(1);
    });

    expect(undoFeedback).toHaveBeenCalledWith({ upload_id: 1, fetch_more: false });
    expect(api.state.feedbacksSinceFetch).toBe(0);
    expect(api.state.lastFeedback).toBeNull();
  });

  it('confirmUndo gives back the cadence slot of the undone feedback', async () => {
    // Reach "rate another 2 items" (one feedback since the last page fetch).
    vi.mocked(rerankBatch).mockResolvedValueOnce({ pool: [] });
    vi.mocked(fetchLastFeedback).mockResolvedValue(null);
    await act(async () => {
      await api.actions.rerankProducts(1, 'u1', 'MORE');
    });
    expect(api.state.feedbacksSinceFetch).toBe(1);

    // Add another → "rate another 1 item".
    vi.mocked(rerankBatch).mockResolvedValueOnce({ pool: [] });
    await act(async () => {
      await api.actions.rerankProducts(1, 'u2', 'MORE');
    });
    expect(api.state.feedbacksSinceFetch).toBe(2);

    // Undo the last one → back to "rate another 2 items" (counter 1), no page fetch.
    vi.mocked(undoFeedback).mockResolvedValueOnce({ pool: [] });
    await act(async () => {
      await api.actions.confirmUndo(1);
    });
    expect(api.state.feedbacksSinceFetch).toBe(1);
  });

  it('fetchLastFeedback hides the undo button when there is no feedback', async () => {
    vi.mocked(fetchLastFeedback).mockResolvedValueOnce(null);
    await act(async () => {
      await api.actions.fetchLastFeedback(1);
    });
    expect(api.state.lastFeedback).toBeNull();
  });

  it('fetchLastFeedback exposes the most recent event for the undo preview', async () => {
    const event = { item_url: 'u2', feedback_type: 'LESS', concept: 'sleeves' };
    vi.mocked(fetchLastFeedback).mockResolvedValueOnce(event as any);
    await act(async () => {
      await api.actions.fetchLastFeedback(1);
    });
    expect(api.state.lastFeedback).toEqual(event);
    expect(api.state.undoPreview).toBe('LESS sleeves');
  });

  it('previews visual MORE/LESS card taps (no concept)', async () => {
    const event = { item_url: 'u2', feedback_type: 'LESS', concept: null, aesthetic: null };
    vi.mocked(fetchLastFeedback).mockResolvedValueOnce(event as any);
    await act(async () => {
      await api.actions.fetchLastFeedback(1);
    });
    expect(api.state.undoPreview).toBe('LESS like `a card`');
  });

  it('previews a visual tap with only the product name, not brand/size/price', async () => {
    vi.mocked(fetchInitial).mockResolvedValueOnce({
      pool: [{
        title: 'Hand made ruched shirt, Brand: no brand, Condition: Very good, Size: S / UK 8-10, 2.00 £, 2.80 £',
        url: 'u2',
        image_url: 'i2.jpg',
        similarity_score: 0.8,
      }],
    } as any);
    await act(async () => {
      await api.actions.scrapeProducts(1, 'striped', filters);
    });

    const event = { item_url: 'u2', feedback_type: 'MORE', concept: null, aesthetic: null };
    vi.mocked(fetchLastFeedback).mockResolvedValueOnce(event as any);
    await act(async () => {
      await api.actions.fetchLastFeedback(1);
    });
    expect(api.state.undoPreview).toBe('MORE like `Hand made ruched shirt`');
  });

  it('hides the undo preview for aesthetic events', async () => {
    const event = { item_url: 'global', feedback_type: 'MORE', concept: null, aesthetic: 'formal' };
    vi.mocked(fetchLastFeedback).mockResolvedValueOnce(event as any);
    await act(async () => {
      await api.actions.fetchLastFeedback(1);
    });
    expect(api.state.lastFeedback).toEqual(event);
    expect(api.state.undoPreview).toBeNull();
  });
});
