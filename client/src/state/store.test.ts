import { beforeEach, describe, expect, it } from 'vitest';
import { appReducer, createInitialState } from './store';

beforeEach(() => localStorage.clear());

describe('root store', () => {
  it('fans one analysis result out to filters and the panel', () => {
    const state = appReducer(createInitialState(), {
      type: 'UPLOAD_SUCCESS',
      uploadId: 1,
      analysis: {
        archetype: 'striped',
        colour_archetype: 'Blue',
        category_archetype: 'Tops',
      },
    });

    expect(state.filters.selectedCategory).toBe('Tops');
    expect(state.filters.selectedColors).toEqual(['Blue']);
    expect(state.ui.preferencesOpen).toBe(true);
  });

  it('does not close a panel the user already opened', () => {
    const opened = appReducer(createInitialState(), { type: 'TOGGLE_PREFERENCES' });
    const uploaded = appReducer(opened, {
      type: 'UPLOAD_SUCCESS',
      uploadId: 1,
      analysis: { archetype: 'striped' },
    });
    expect(uploaded.ui.preferencesOpen).toBe(true);
  });

  it('hydrates persisted filters but keeps session-only fields at their defaults', () => {
    localStorage.setItem('rs_size_id', JSON.stringify(['S']));
    const state = createInitialState();
    expect(state.filters.selectedSizes).toEqual(['S']);
    expect(state.filters.selectedCategory).toBe('See all');
    expect(state.filters.selectedColors).toEqual([]);
  });
});
