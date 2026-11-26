import { beforeEach, describe, expect, it } from 'vitest';
import { initialFiltersState } from './filters';
import { readPersistedFilters, writePersistedFilters } from './persistence';

beforeEach(() => localStorage.clear());

describe('filter persistence', () => {
  it('writes only sizes, price and conditions', () => {
    writePersistedFilters({
      ...initialFiltersState,
      selectedSizes: ['M'],
      maxPrice: '50',
      selectedConditions: ['New with tags'],
      selectedCategory: 'Tops',
      selectedColors: ['Red'],
    });

    expect(JSON.parse(localStorage.getItem('rs_size_id') ?? 'null')).toEqual(['M']);
    expect(localStorage.getItem('rs_max_price')).toBe('50');
    expect(JSON.parse(localStorage.getItem('rs_condition_id') ?? 'null')).toEqual([
      'New with tags',
    ]);
    expect(
      Array.from({ length: localStorage.length }, (_, index) => localStorage.key(index)).sort(),
    ).toEqual(['rs_condition_id', 'rs_max_price', 'rs_size_id']);
  });

  it('reads back only the persisted fields', () => {
    localStorage.setItem('rs_size_id', JSON.stringify(['S']));
    localStorage.setItem('rs_max_price', '75');

    expect(readPersistedFilters()).toEqual({
      selectedSizes: ['S'],
      maxPrice: '75',
    });
  });
});
