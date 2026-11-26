import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { useActions } from './actions';
import { StateProvider, useStore } from './store';
import type { AppState } from './store';

vi.mock('../api', () => ({
  analyzeFile: vi.fn(),
  fetchInitial: vi.fn(),
  fetchTraitProfile: vi.fn(),
  fetchLastFeedback: vi.fn(),
  rerankBatch: vi.fn(),
  undoFeedback: vi.fn(),
}));

(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;

type Api = { state: AppState; actions: ReturnType<typeof useActions> };

function Probe({ onReady }: { onReady: (api: Api) => void }) {
  const { state } = useStore();
  const actions = useActions();
  onReady({ state, actions });
  return null;
}

describe('StateProvider wiring', () => {
  let container: HTMLDivElement;
  let root: Root;
  let api: Api;

  beforeEach(() => {
    localStorage.clear();
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
    act(() => {
      root.render(
        <StateProvider>
          <Probe onReady={value => { api = value; }} />
        </StateProvider>,
      );
    });
  });

  afterEach(() => {
    const activeRoot = root;
    act(() => activeRoot.unmount());
    container.remove();
    vi.clearAllMocks();
  });

  it('runs a command against state dispatched earlier in the same session', async () => {
    await expect(api.actions.search()).rejects.toThrow(
      'Please provide or parse a lookup keyword first.',
    );

    act(() => api.actions.setConfirmedKeyword('striped'));
    await expect(api.actions.search()).rejects.toThrow('Upload an image before searching.');
  });

  it('persists filter changes through the provider effect', () => {
    act(() => api.actions.toggleSize('S'));
    expect(JSON.parse(localStorage.getItem('rs_size_id') ?? 'null')).toEqual(['S']);
  });
});
