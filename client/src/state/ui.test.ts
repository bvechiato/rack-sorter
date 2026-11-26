import { describe, expect, it } from 'vitest';
import { initialUIState, uiReducer } from './ui';
import type { UIAction, UIState } from './ui';

function run(state: UIState, ...actions: UIAction[]): UIState {
  return actions.reduce(uiReducer, state);
}

describe('uiReducer', () => {
  it('keeps panel, sheet and error state as independent transitions', () => {
    const state = run(
      initialUIState,
      { type: 'TOGGLE_PREFERENCES' },
      { type: 'OPEN_TRAIT_SHEET', itemUrl: 'u1' },
      { type: 'SHOW_ERROR', message: 'backend down' },
      { type: 'TOGGLE_PREFERENCES' },
      { type: 'CLOSE_TRAIT_SHEET' },
      { type: 'CLEAR_ERROR' },
    );

    expect(state).toEqual({
      preferencesOpen: false,
      traitSheetUrl: null,
      errorMessage: null,
    });
  });
});
