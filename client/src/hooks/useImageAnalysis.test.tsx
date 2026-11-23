import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { analyzeFile } from '../api';
import { useImageAnalysis } from './useImageAnalysis';

vi.mock('../api', () => ({ analyzeFile: vi.fn() }));

type AnalysisApi = ReturnType<typeof useImageAnalysis>;

(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;

function Probe({ onReady }: { onReady: (api: AnalysisApi) => void }) {
  onReady(useImageAnalysis());
  return null;
}

describe('useImageAnalysis', () => {
  let container: HTMLDivElement | undefined;
  let root: Root | undefined;
  let api: AnalysisApi;

  beforeEach(() => {
    vi.mocked(analyzeFile).mockResolvedValue({
      upload_id: 7,
      analysis: {
        archetype: 'long sleeve',
        classified_tags: ['long sleeve', 'striped', 'long sleeve'],
        colour_archetype: 'Blue',
        colour_classified_tags: ['Blue', 'Red'],
        category_archetype: 'Tops',
      },
    } as any);

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

  it('deduplicates keyword and colour suggestions from the analysis payload', async () => {
    await act(async () => {
      await api.actions.handleImageUpload(new File(['x'], 'shirt.jpg', { type: 'image/jpeg' }));
    });

    expect(api.state.suggestedKeywords).toEqual(['long sleeve', 'striped']);
    expect(api.state.suggestedColours).toEqual(['Blue', 'Red']);
  });

  it('hides stale suggestions while a replacement upload is in flight', async () => {
    const file = new File(['x'], 'shirt.jpg', { type: 'image/jpeg' });
    await act(async () => {
      await api.actions.handleImageUpload(file);
    });
    expect(api.state.showSuggestions).toBe(true);

    let resolveSecond: ((value: any) => void) | undefined;
    vi.mocked(analyzeFile).mockReturnValueOnce(new Promise<any>(resolve => {
      resolveSecond = resolve;
    }));

    await act(async () => {
      void api.actions.handleImageUpload(file);
    });
    expect(api.state.showSuggestions).toBe(false);

    await act(async () => {
      resolveSecond?.({
        upload_id: 8,
        analysis: { archetype: 'striped', classified_tags: [], colour_archetype: 'Red' },
      });
    });
  });
});
