import { useMemo } from 'react';
import * as commands from './commands';
import { useStore } from './store';
import type { TraitPicks } from './types';

/**
 * The only React-facing adapter: binds UI intents to store events and async commands.
 * No feature hook owns state — components can read it from the store directly.
 */
export function useActions() {
  const { dispatch, execute } = useStore();

  return useMemo(
    () => ({
      setConfirmedKeyword: (value: string) => dispatch({ type: 'KEYWORD_CHANGED', value }),
      selectKeyword: (value: string) => dispatch({ type: 'KEYWORD_SELECTED', value }),
      analyzeImage: (file: File | null) => execute(commands.analyzeImage(file)),

      setMaxPrice: (value: string) => dispatch({ type: 'SET_MAX_PRICE', value }),
      setSelectedCategory: (value: string) => dispatch({ type: 'SET_CATEGORY', value }),
      toggleSize: (value: string) => dispatch({ type: 'TOGGLE_SIZE', value }),
      toggleColour: (value: string) => dispatch({ type: 'TOGGLE_COLOUR', value }),
      toggleCondition: (value: string) => dispatch({ type: 'TOGGLE_CONDITION', value }),

      togglePreferences: () => dispatch({ type: 'TOGGLE_PREFERENCES' }),
      openTraitSheet: (itemUrl: string) => execute(commands.openTraitSheet(itemUrl)),
      closeTraitSheet: () => dispatch({ type: 'CLOSE_TRAIT_SHEET' }),
      showError: (message: string) => dispatch({ type: 'SHOW_ERROR', message }),
      clearError: () => dispatch({ type: 'CLEAR_ERROR' }),

      search: () => execute(commands.search()),
      submitFeedback: (itemUrl: string, feedbackType: 'MORE' | 'LESS') =>
        execute(commands.rerank(itemUrl, feedbackType)),
      applyTraitPicks: (itemUrl: string, picks: TraitPicks) =>
        execute(commands.applyTraitPicks(itemUrl, picks)),
      toggleAesthetic: (phrase: string) => execute(commands.toggleAesthetic(phrase)),

      requestUndo: () => dispatch({ type: 'UNDO_REQUEST' }),
      cancelUndo: () => dispatch({ type: 'UNDO_CANCEL' }),
      confirmUndo: () => execute(commands.confirmUndo()),
    }),
    [dispatch, execute],
  );
}
