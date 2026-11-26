import { describe, expect, it } from 'vitest';
import { filtersReducer, initialFiltersState } from './filters';
import type { FiltersAction, FiltersState } from './filters';

function run(state: FiltersState, ...actions: FiltersAction[]): FiltersState {
  return actions.reduce(filtersReducer, state);
}

describe('filtersReducer', () => {
  it('hydrates persisted values without marking session seeds as touched', () => {
    const hydrated = run(
      initialFiltersState,
      {
        type: 'HYDRATE',
        payload: { selectedSizes: ['S'], maxPrice: '75', selectedConditions: ['New with tags'] },
      },
      { type: 'SEED_CATEGORY', value: 'Dresses' },
      { type: 'SEED_COLOURS', values: ['Blue'] },
    );

    expect(hydrated.selectedSizes).toEqual(['S']);
    expect(hydrated.maxPrice).toBe('75');
    expect(hydrated.selectedConditions).toEqual(['New with tags']);
    expect(hydrated.selectedCategory).toBe('Dresses');
    expect(hydrated.selectedColors).toEqual(['Blue']);
  });

  it('locks out later seeds once the user picks a category or colour', () => {
    const picked = run(
      initialFiltersState,
      { type: 'SEED_CATEGORY', value: 'Dresses' },
      { type: 'SEED_COLOURS', values: ['Blue', 'Red'] },
      { type: 'SET_CATEGORY', value: 'Tops' },
      { type: 'TOGGLE_COLOUR', value: 'Green' },
      { type: 'SEED_CATEGORY', value: 'Outerwear' },
      { type: 'SEED_COLOURS', values: ['Black'] },
    );

    expect(picked.selectedCategory).toBe('Tops');
    expect(picked.selectedColors).toEqual(['Blue', 'Red', 'Green']);
  });

  it('treats "See all" and "None" as clear actions and "None" locks the seeds', () => {
    const cleared = run(
      initialFiltersState,
      { type: 'TOGGLE_SIZE', value: 'S' },
      { type: 'TOGGLE_SIZE', value: 'M' },
      { type: 'SEED_COLOURS', values: ['Blue'] },
      { type: 'TOGGLE_SIZE', value: 'See all' },
      { type: 'TOGGLE_COLOUR', value: 'None' },
      { type: 'SEED_COLOURS', values: ['Red'] },
    );

    expect(cleared.selectedSizes).toEqual([]);
    expect(cleared.selectedColors).toEqual([]);
  });

  it('toggles sizes, colours and conditions without a reducer mutating state', () => {
    const once = run(
      initialFiltersState,
      { type: 'TOGGLE_SIZE', value: 'S' },
      { type: 'TOGGLE_COLOUR', value: 'Red' },
      { type: 'TOGGLE_CONDITION', value: '2' },
    );
    const twice = run(
      once,
      { type: 'TOGGLE_SIZE', value: 'S' },
      { type: 'TOGGLE_COLOUR', value: 'Red' },
      { type: 'TOGGLE_CONDITION', value: '2' },
    );

    expect(once.selectedSizes).toEqual(['S']);
    expect(once.selectedColors).toEqual(['Red']);
    expect(once.selectedConditions).toEqual(['2']);
    expect(twice.selectedSizes).toEqual([]);
    expect(twice.selectedColors).toEqual([]);
    expect(twice.selectedConditions).toEqual([]);
    expect(initialFiltersState.selectedSizes).toEqual([]);
  });
});
