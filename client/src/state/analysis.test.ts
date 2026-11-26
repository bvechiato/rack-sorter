import { describe, expect, it } from 'vitest';
import { analysisReducer, initialAnalysisState } from './analysis';
import type { AnalysisAction, AnalysisState } from './analysis';

function run(state: AnalysisState, ...actions: AnalysisAction[]): AnalysisState {
  return actions.reduce(analysisReducer, state);
}

describe('analysisReducer', () => {
  it('hides stale suggestions on upload start and dedupes the success payload', () => {
    const started = analysisReducer(initialAnalysisState, { type: 'UPLOAD_START' });
    expect(started.loading).toBe(true);
    expect(started.showSuggestions).toBe(false);

    const done = analysisReducer(started, {
      type: 'UPLOAD_SUCCESS',
      uploadId: 7,
      analysis: {
        archetype: 'long sleeve',
        classified_tags: ['long sleeve', 'striped', 'long sleeve'],
        colour_archetype: 'Blue',
        colour_classified_tags: ['Blue', 'Red'],
        category_archetype: 'Tops',
      },
    });

    expect(done.loading).toBe(false);
    expect(done.uploadId).toBe(7);
    expect(done.confirmedKeyword).toBe('long sleeve');
    expect(done.suggestedKeywords).toEqual(['long sleeve', 'striped']);
    expect(done.suggestedColours).toEqual(['Blue', 'Red']);
    expect(done.suggestedCategory).toBe('Tops');
    expect(done.showSuggestions).toBe(true);
  });

  it('keeps the failure in flight state clean and treats keyword edits as one transition', () => {
    const failed = run(
      initialAnalysisState,
      { type: 'UPLOAD_START' },
      { type: 'UPLOAD_FAILURE' },
    );
    expect(failed.loading).toBe(false);

    const typed = analysisReducer(failed, { type: 'KEYWORD_CHANGED', value: 'striped' });
    const selected = analysisReducer(typed, { type: 'KEYWORD_SELECTED', value: 'boho' });
    expect(selected.confirmedKeyword).toBe('boho');
  });
});
