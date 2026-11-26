export interface UIState {
  preferencesOpen: boolean;
  traitSheetUrl: string | null;
  errorMessage: string | null;
}

export const initialUIState: UIState = {
  preferencesOpen: false,
  traitSheetUrl: null,
  errorMessage: null,
};

export type UIAction =
  | { type: 'TOGGLE_PREFERENCES' }
  | { type: 'SET_PREFERENCES_OPEN'; value: boolean }
  | { type: 'OPEN_TRAIT_SHEET'; itemUrl: string }
  | { type: 'CLOSE_TRAIT_SHEET' }
  | { type: 'SHOW_ERROR'; message: string }
  | { type: 'CLEAR_ERROR' };

export function uiReducer(state: UIState, action: UIAction): UIState {
  switch (action.type) {
    case 'TOGGLE_PREFERENCES':
      return { ...state, preferencesOpen: !state.preferencesOpen };
    case 'SET_PREFERENCES_OPEN':
      return { ...state, preferencesOpen: action.value };
    case 'OPEN_TRAIT_SHEET':
      return { ...state, traitSheetUrl: action.itemUrl };
    case 'CLOSE_TRAIT_SHEET':
      return { ...state, traitSheetUrl: null };
    case 'SHOW_ERROR':
      return { ...state, errorMessage: action.message };
    case 'CLEAR_ERROR':
      return { ...state, errorMessage: null };
    default:
      return state;
  }
}
