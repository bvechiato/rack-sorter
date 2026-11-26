import Header from './components/Header';
import ErrorBoundary from './components/ErrorBoundary';
import SearchActionBar from './components/SearchActionBar';
import StyleStrip from './components/StyleStrip';
import KeywordSuggestions from './components/KeywordSuggestions';
import PreferencesPanel from './components/preferences/PreferencesPanel';
import ProductGrid from './components/product/ProductGrid';
import TraitSheet from './components/product/TraitSheet';
import ActiveFiltersSummary from './components/preferences/ActiveFiltersSummary';
import LoadingIndicator from './components/LoadingIndicator';
import { useActions } from './state/actions';
import {
  selectFetchingMore,
  selectLoading,
  selectSearching,
  selectUndoing,
  selectUndoPreview,
} from './state/search';
import { useStore } from './state/store';
import { FETCH_EVERY } from './state/types';
import './styles/index.css';
import './styles/generic.css';

/** The view reads one state tree and sends intents; it owns no state and no effects. */
function App() {
  const { state } = useStore();
  const actions = useActions();
  const { analysis, filters, search, ui } = state;

  const loading = selectLoading(search);
  const searching = selectSearching(search);
  const fetchingMore = selectFetchingMore(search);
  const undoing = selectUndoing(search);
  const undoPreview = selectUndoPreview(search);

  const tunedItem = ui.traitSheetUrl
    ? search.products.find(product => product.url === ui.traitSheetUrl) ?? null
    : null;

  const handleImageUpload = async (file: File | null) => {
    if (!file) return;
    try {
      await actions.analyzeImage(file);
    } catch (err: any) {
      actions.showError(err.message);
    }
  };

  const handleScrape = async () => {
    try {
      await actions.search();
    } catch (err: any) {
      actions.showError(err.message);
    }
  };

  const handleToggleAesthetic = async (phrase: string) => {
    try {
      await actions.toggleAesthetic(phrase);
    } catch (err: any) {
      actions.showError(err.message);
    }
  };

  const handleConfirmUndo = async () => {
    try {
      await actions.confirmUndo();
    } catch (err: any) {
      // confirmUndo reopens the confirmation stage; surface the reason with a toast.
      actions.showError(err.message);
    }
  };

  return (
    <ErrorBoundary>
      <div>
      <Header />

      <SearchActionBar
        confirmedKeyword={analysis.confirmedKeyword}
        setConfirmedKeyword={actions.setConfirmedKeyword}
        onImageUpload={handleImageUpload}
        analyzing={analysis.loading}
      />

      {analysis.showSuggestions && (
        <KeywordSuggestions
          keywords={analysis.suggestedKeywords}
          confirmedKeyword={analysis.confirmedKeyword}
          onSelectKeyword={actions.selectKeyword}
        />
      )}

      <PreferencesPanel
        selectedSizes={filters.selectedSizes}
        toggleSize={actions.toggleSize}
        maxPrice={filters.maxPrice}
        setMaxPrice={actions.setMaxPrice}
        selectedCategory={filters.selectedCategory}
        setSelectedCategory={actions.setSelectedCategory}
        selectedColors={filters.selectedColors}
        toggleColour={actions.toggleColour}
        selectedConditions={filters.selectedConditions}
        toggleCondition={actions.toggleCondition}
        isOpen={ui.preferencesOpen}
        toggleOpen={actions.togglePreferences}
        onScrape={handleScrape}
      />

      <StyleStrip
        active={search.aesthetics}
        disabled={!analysis.uploadId || search.products.length === 0}
        busy={loading}
        onToggle={handleToggleAesthetic}
      />

      {searching && <LoadingIndicator />}

      {!loading && search.products.length > 0 && (
        <ActiveFiltersSummary keyword={analysis.confirmedKeyword} filters={filters} />
      )}

      {!fetchingMore && search.products.length > 0 && (
        <div className="fixed-status-bar" role="status" aria-live="polite">
          <svg className="feedback-progress" viewBox="0 0 24 24" aria-hidden="true">
            <circle className="feedback-progress-track" cx="12" cy="12" r="9" />
            <circle
              className="feedback-progress-fill"
              cx="12"
              cy="12"
              r="9"
              style={{
                strokeDasharray: 56.55,
                strokeDashoffset: 56.55 * (1 - search.feedbacksSinceFetch / FETCH_EVERY),
              }}
            />
          </svg>
          <span>
            rate another {FETCH_EVERY - search.feedbacksSinceFetch} item{FETCH_EVERY - search.feedbacksSinceFetch === 1 ? '' : 's'} to rerank
          </span>
        </div>
      )}

      {fetchingMore && (
        <div className={`fixed-status-bar is-refreshing`} role="status" aria-live="polite">
          <span className="loading-spinner loading-spinner--sm" aria-hidden="true" />
          <span>Fetching more and reranking…</span>
        </div>
      )}

      {search.undoStage === 'preview' && (
        <div className="fixed-status-bar undo-bar" role="status" aria-live="polite">
          <span>↩ Undo last feedback: {undoPreview}</span>
          <button className="undo-bar-action" onClick={actions.requestUndo}>
            Undo
          </button>
        </div>
      )}

      {(search.undoStage === 'confirming' || search.undoStage === 'undoing') && (
        <div className="fixed-status-bar undo-bar is-confirming" role="alert" aria-live="assertive">
          <span>Confirm undo: {undoPreview}?</span>
          {search.undoStage === 'confirming' && (
            <button className="undo-bar-action" onClick={actions.cancelUndo}>
              Cancel
            </button>
          )}
          <button
            className="undo-bar-action undo-bar-action--confirm"
            onClick={handleConfirmUndo}
            disabled={undoing}
          >
            {undoing ? 'Undoing…' : 'Confirm'}
          </button>
        </div>
      )}

      <ProductGrid
        products={search.products}
        onFeedback={(itemUrl, feedbackType) => actions.submitFeedback(itemUrl, feedbackType)}
        onTune={actions.openTraitSheet}
        tunedUrls={search.traitPicks}
        disabled={loading}
      />

      {tunedItem && (
        <TraitSheet
          item={tunedItem}
          appliedPicks={search.traitPicks[tunedItem.url]}
          profile={search.traitProfile}
          profileError={search.profileError}
          onClose={actions.closeTraitSheet}
          onApply={(picks) => actions.applyTraitPicks(tunedItem.url, picks)}
        />
      )}

      {ui.errorMessage && (
        <div className="toast toast-error" role="alert" onClick={actions.clearError}>
          {ui.errorMessage}
          <button className="toast-close" aria-label="Dismiss">×</button>
        </div>
      )}

      </div>
    </ErrorBoundary>
  );
}

export default App;
