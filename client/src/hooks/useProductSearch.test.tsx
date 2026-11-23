import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { fetchInitial } from '../api';
import { useProductSearch } from './useProductSearch';

vi.mock('../api', () => ({
  fetchInitial: vi.fn(),
  rerankBatch: vi.fn(),
  fetchTraitProfile: vi.fn(),
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
});
