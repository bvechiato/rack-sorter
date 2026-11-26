import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useReducer,
  useRef,
} from 'react';
import type { ReactNode } from 'react';
import {
  analysisReducer,
  initialAnalysisState,
  type AnalysisAction,
} from './analysis';
import {
  filtersReducer,
  initialFiltersState,
  type FiltersAction,
} from './filters';
import {
  initialSearchState,
  searchReducer,
  type SearchAction,
} from './search';
import { initialUIState, uiReducer, type UIAction } from './ui';
import { readPersistedFilters, writePersistedFilters } from './persistence';
import type { Command } from './commands';

/**
 * The single source of truth. Slices are pure reducers; `appReducer` also owns the
 * transitions that cross slices (analysis seeding filters and opening the panel), so
 * coordination lives in state, not in React effects scattered across components.
 */
export interface AppState {
  analysis: ReturnType<typeof analysisReducer>;
  filters: ReturnType<typeof filtersReducer>;
  search: ReturnType<typeof searchReducer>;
  ui: ReturnType<typeof uiReducer>;
}

export type AppAction = AnalysisAction | FiltersAction | SearchAction | UIAction;

export function createInitialState(): AppState {
  return {
    analysis: initialAnalysisState,
    filters: filtersReducer(initialFiltersState, {
      type: 'HYDRATE',
      payload: readPersistedFilters(),
    }),
    search: initialSearchState,
    ui: initialUIState,
  };
}

export function appReducer(state: AppState, action: AppAction): AppState {
  // Each slice returns the same reference for an action it does not own. Preserve the
  // root reference too, so a blocked action does not re-render the whole view.
  const analysis = analysisReducer(state.analysis, action as AnalysisAction);
  const filters = filtersReducer(state.filters, action as FiltersAction);
  const search = searchReducer(state.search, action as SearchAction);
  const ui = uiReducer(state.ui, action as UIAction);
  if (
    analysis === state.analysis &&
    filters === state.filters &&
    search === state.search &&
    ui === state.ui
  ) {
    return state;
  }

  // One upload result fans out to several slices. Keeping this here means a component
  // never has to watch another slice's state to keep its own in step.
  if (action.type === 'UPLOAD_SUCCESS') {
    return {
      analysis,
      filters: filtersReducer(
        filtersReducer(filters, {
          type: 'SEED_CATEGORY',
          value: analysis.suggestedCategory,
        }),
        { type: 'SEED_COLOURS', values: analysis.suggestedColours },
      ),
      search,
      ui: ui.preferencesOpen
        ? ui
        : uiReducer(ui, { type: 'SET_PREFERENCES_OPEN', value: true }),
    };
  }

  return { analysis, filters, search, ui };
}

export interface Store {
  state: AppState;
  dispatch: (action: AppAction) => void;
  /** Run an async command with the state visible when it is dispatched; events come back via dispatch. */
  execute: (command: Command) => Promise<void>;
}

const StoreContext = createContext<Store | null>(null);

export function StateProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(appReducer, undefined, createInitialState);
  const stateRef = useRef(state);
  stateRef.current = state;

  const execute = useCallback(
    async (command: Command) => {
      await command({ state: stateRef.current, dispatch });
    },
    [dispatch],
  );

  // Persistence is store infrastructure, not a feature concern.
  useEffect(() => {
    writePersistedFilters(state.filters);
  }, [state.filters]);

  const value = useMemo<Store>(
    () => ({ state, dispatch, execute }),
    [state, dispatch, execute],
  );

  return <StoreContext.Provider value={value}>{children}</StoreContext.Provider>;
}

export function useStore(): Store {
  const store = useContext(StoreContext);
  if (!store) throw new Error('useStore must be used inside <StateProvider>');
  return store;
}
