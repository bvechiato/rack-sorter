import { act } from 'react';
import { createRoot, type Root } from 'react-dom/client';
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { useFilters } from './useFilters';

// Category and colours are intentionally session-only (former F7, closed as "by design").
// These tests guard that contract: only sizes, price and conditions reach localStorage.

type FiltersApi = ReturnType<typeof useFilters>;

(globalThis as any).IS_REACT_ACT_ENVIRONMENT = true;

function Probe({ onReady }: { onReady: (api: FiltersApi) => void }) {
  onReady(useFilters());
  return null;
}

function persistedKeys(): string[] {
  const keys: string[] = [];
  for (let i = 0; i < localStorage.length; i += 1) {
    keys.push(localStorage.key(i) as string);
  }
  return keys.sort();
}

describe('useFilters session state', () => {
  let container: HTMLDivElement;
  let root: Root;
  let api: FiltersApi;

  const mount = () => {
    container = document.createElement('div');
    document.body.appendChild(container);
    root = createRoot(container);
    act(() => {
      root.render(<Probe onReady={value => { api = value; }} />);
    });
  };

  const unmount = () => {
    act(() => root.unmount());
    container.remove();
  };

  beforeEach(() => {
    localStorage.clear();
    mount();
  });

  afterEach(() => {
    unmount();
    localStorage.clear();
  });

  it('writes only the sizes, price and conditions keys to localStorage', () => {
    act(() => {
      api.actions.setSelectedCategory('Tops');
      api.actions.setSelectedColors(['Red', 'Blue']);
      api.actions.setSelectedSizes(['M']);
      api.actions.setMaxPrice('50');
      api.actions.setSelectedConditions(['New with tags']);
    });

    expect(JSON.parse(localStorage.getItem('rs_size_id') ?? 'null')).toEqual(['M']);
    expect(localStorage.getItem('rs_max_price')).toBe('50');
    expect(JSON.parse(localStorage.getItem('rs_condition_id') ?? 'null')).toEqual(['New with tags']);
    expect(persistedKeys()).toEqual(['rs_condition_id', 'rs_max_price', 'rs_size_id']);
  });

  it('resets category and colours on remount but restores the persisted filters', () => {
    act(() => {
      api.actions.setSelectedCategory('Dresses');
      api.actions.setSelectedColors(['Red']);
      api.actions.setSelectedSizes(['S']);
      api.actions.setMaxPrice('75');
      api.actions.setSelectedConditions(['Used']);
    });

    unmount();
    mount();

    expect(api.filters.selectedCategory).toBe('See all');
    expect(api.filters.selectedColors).toEqual([]);
    expect(api.filters.selectedSizes).toEqual(['S']);
    expect(api.filters.maxPrice).toBe('75');
    expect(api.filters.selectedConditions).toEqual(['Used']);
  });
});
