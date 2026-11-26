export interface FiltersState {
  selectedSizes: string[];
  maxPrice: string;
  selectedCategory: string;
  selectedColors: string[];
  selectedConditions: string[];
  /** Analysis seeds are defaults only: a user pick wins for the rest of the session. */
  categoryTouched: boolean;
  coloursTouched: boolean;
}

export const initialFiltersState: FiltersState = {
  selectedSizes: [],
  maxPrice: '',
  selectedCategory: 'See all',
  selectedColors: [],
  selectedConditions: [],
  categoryTouched: false,
  coloursTouched: false,
};

export type FiltersAction =
  | {
      type: 'HYDRATE';
      payload: Partial<Pick<FiltersState, 'selectedSizes' | 'maxPrice' | 'selectedConditions'>>;
    }
  | { type: 'TOGGLE_SIZE'; value: string }
  | { type: 'SET_MAX_PRICE'; value: string }
  | { type: 'SET_CATEGORY'; value: string }
  | { type: 'TOGGLE_COLOUR'; value: string }
  | { type: 'TOGGLE_CONDITION'; value: string }
  | { type: 'SEED_CATEGORY'; value: string | null }
  | { type: 'SEED_COLOURS'; values: string[] };

export function filtersReducer(state: FiltersState, action: FiltersAction): FiltersState {
  switch (action.type) {
    case 'HYDRATE':
      // Persisted values are not user picks made this session, so they leave the
      // seed guards alone.
      return { ...state, ...action.payload };

    case 'TOGGLE_SIZE':
      if (action.value === 'See all') return { ...state, selectedSizes: [] };
      return {
        ...state,
        selectedSizes: state.selectedSizes.includes(action.value)
          ? state.selectedSizes.filter(size => size !== action.value)
          : [...state.selectedSizes, action.value],
      };

    case 'SET_MAX_PRICE':
      return { ...state, maxPrice: action.value };

    case 'SET_CATEGORY':
      return { ...state, selectedCategory: action.value, categoryTouched: true };

    case 'TOGGLE_COLOUR': {
      // Any explicit colour interaction locks out later analysis seeds, including "None".
      if (action.value === 'None') return { ...state, selectedColors: [], coloursTouched: true };
      return {
        ...state,
        coloursTouched: true,
        selectedColors: state.selectedColors.includes(action.value)
          ? state.selectedColors.filter(colour => colour !== action.value)
          : [...state.selectedColors, action.value],
      };
    }

    case 'TOGGLE_CONDITION':
      return {
        ...state,
        selectedConditions: state.selectedConditions.includes(action.value)
          ? state.selectedConditions.filter(condition => condition !== action.value)
          : [...state.selectedConditions, action.value],
      };

    case 'SEED_CATEGORY':
      if (!action.value || state.categoryTouched) return state;
      return { ...state, selectedCategory: action.value };

    case 'SEED_COLOURS':
      if (state.coloursTouched) return state;
      return { ...state, selectedColors: action.values };

    default:
      return state;
  }
}
