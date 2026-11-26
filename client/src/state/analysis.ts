export interface AnalysisState {
  confirmedKeyword: string;
  suggestedKeywords: string[];
  showSuggestions: boolean;
  loading: boolean;
  suggestedColours: string[];
  suggestedCategory: string | null;
  uploadId: number | null;
}

/** The analysis payload is parsed into display-ready suggestions by the reducer. */
export interface AnalysisPayload {
  archetype: string;
  classified_tags?: string[] | null;
  colour_archetype?: string | null;
  colour_classified_tags?: string[] | null;
  category_archetype?: string | null;
}

export const initialAnalysisState: AnalysisState = {
  confirmedKeyword: '',
  suggestedKeywords: [],
  showSuggestions: false,
  loading: false,
  suggestedColours: [],
  suggestedCategory: null,
  uploadId: null,
};

export type AnalysisAction =
  | { type: 'KEYWORD_CHANGED'; value: string }
  | { type: 'KEYWORD_SELECTED'; value: string }
  | { type: 'UPLOAD_START' }
  | { type: 'UPLOAD_SUCCESS'; uploadId: number; analysis: AnalysisPayload }
  | { type: 'UPLOAD_FAILURE' };

export function analysisReducer(state: AnalysisState, action: AnalysisAction): AnalysisState {
  switch (action.type) {
    case 'KEYWORD_CHANGED':
    case 'KEYWORD_SELECTED':
      return { ...state, confirmedKeyword: action.value };

    // Hide stale suggestions immediately; a new upload needs a fresh false → true edge
    // to reopen a panel the user had closed.
    case 'UPLOAD_START':
      return { ...state, showSuggestions: false, loading: true };

    case 'UPLOAD_SUCCESS': {
      const { analysis } = action;
      return {
        ...state,
        loading: false,
        uploadId: action.uploadId,
        confirmedKeyword: analysis.archetype,
        // The archetype is also the first classified tag; duplicates would render twice.
        suggestedKeywords: [...new Set(analysis.classified_tags ?? [])],
        showSuggestions: true,
        suggestedColours: [
          ...new Set([analysis.colour_archetype, ...(analysis.colour_classified_tags ?? [])]),
        ],
        suggestedCategory: analysis.category_archetype ?? null,
      };
    }

    case 'UPLOAD_FAILURE':
      return { ...state, loading: false };

    default:
      return state;
  }
}
