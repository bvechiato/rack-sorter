import type { FiltersState } from './filters';

/** Only these three filter fields survive a reload; category/colours are session-only. */
export interface PersistedFilters {
  selectedSizes?: string[];
  maxPrice?: string;
  selectedConditions?: string[];
}

export function readPersistedFilters(): PersistedFilters {
  const savedSizes = localStorage.getItem('rs_size_id');
  const savedPrice = localStorage.getItem('rs_max_price');
  const savedConditions = localStorage.getItem('rs_condition_id');
  const result: PersistedFilters = {};

  if (savedSizes) result.selectedSizes = JSON.parse(savedSizes);
  if (savedPrice) result.maxPrice = savedPrice;
  if (savedConditions) result.selectedConditions = JSON.parse(savedConditions);
  return result;
}

export function writePersistedFilters(filters: FiltersState): void {
  localStorage.setItem('rs_size_id', JSON.stringify(filters.selectedSizes));
  localStorage.setItem('rs_max_price', filters.maxPrice);
  localStorage.setItem('rs_condition_id', JSON.stringify(filters.selectedConditions));
}
