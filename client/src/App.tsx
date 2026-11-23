import { useEffect } from 'react';
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
import {
  useFilters,
  useImageAnalysis,
  useProductSearch,
  useUIState
} from './hooks';
import './styles/index.css';
import './styles/generic.css';

function App() {
  const { filters, actions: filterActions } = useFilters();
  const { state: imageState, actions: imageActions } = useImageAnalysis();
  const { state: searchState, actions: searchActions } = useProductSearch();
  const { state: uiState, actions: uiActions } = useUIState();

  const tunedItem = uiState.traitSheetUrl
    ? searchState.products.find(product => product.url === uiState.traitSheetUrl) ?? null
    : null;

  const handleImageUpload = async (file: File | null) => {
    if (!file) return;
    try {
      await imageActions.handleImageUpload(file as File);
    } catch (err: any) {
      uiActions.showError(err.message);
    }
  };

  const handleScrape = async () => {
    try {
      await searchActions.scrapeProducts(imageState.uploadId, imageState.confirmedKeyword, filters);
    } catch (err: any) {
      uiActions.showError(err.message);
    }
  };

  // Styles are global, so the strip toggles one phrase at a time and the whole pool reranks.
  const handleToggleAesthetic = async (phrase: string) => {
    const isActive = searchState.aesthetics.some(
      value => value.toLowerCase() === phrase.toLowerCase(),
    );
    try {
      await searchActions.toggleAesthetic(imageState.uploadId, phrase, isActive);
    } catch (err: any) {
      uiActions.showError(err.message);
    }
  };

  useEffect(() => {
    filterActions.setSelectedColors(imageState.suggestedColours);
  }, [imageState.suggestedColours]);

  useEffect(() => {
    if (imageState.suggestedCategory) {
      filterActions.setSelectedCategory(imageState.suggestedCategory);
    }
  }, [imageState.suggestedCategory]);

  useEffect(() => {
   if (imageState.showSuggestions && !uiState.preferencesOpen) {
    uiActions.togglePreferences();
  }
}, [imageState.showSuggestions]);

  // Seed the debug diagram as soon as the sheet opens, so the first tap has a baseline.
  useEffect(() => {
    if (uiState.traitSheetUrl) {
      searchActions.loadTraitProfile(imageState.uploadId, uiState.traitSheetUrl);
    }
  }, [uiState.traitSheetUrl, imageState.uploadId]);

  return (
    <ErrorBoundary>
      <div>
      <Header />

      <SearchActionBar
        confirmedKeyword={imageState.confirmedKeyword}
        setConfirmedKeyword={imageActions.setConfirmedKeyword}
        onImageUpload={handleImageUpload}
        analyzing={imageState.loading}
      />

      {imageState.showSuggestions && (
        <KeywordSuggestions
          keywords={imageState.suggestedKeywords}
          onSelectKeyword={imageActions.selectKeyword}
        />
      )}

      <PreferencesPanel
        selectedSizes={filters.selectedSizes}
        toggleSize={filterActions.toggleSize}
        maxPrice={filters.maxPrice}
        setMaxPrice={filterActions.setMaxPrice}
        selectedCategory={filters.selectedCategory}
        setSelectedCategory={filterActions.setSelectedCategory}
        selectedColors={filters.selectedColors}
        toggleColour={filterActions.toggleColour}
        selectedConditions={filters.selectedConditions}
        toggleCondition={filterActions.toggleCondition}
        isOpen={uiState.preferencesOpen}
        toggleOpen={uiActions.togglePreferences}
        onScrape={handleScrape}
      />

      <StyleStrip
        active={searchState.aesthetics}
        disabled={!imageState.uploadId || searchState.products.length === 0}
        busy={searchState.loading}
        onToggle={handleToggleAesthetic}
      />

      {searchState.loading && searchState.products.length === 0 && <LoadingIndicator />}

      {!searchState.loading && searchState.products.length > 0 && (
        <ActiveFiltersSummary 
          keyword={imageState.confirmedKeyword} 
          filters={filters} 
        />
      )}

      {!searchState.fetchingMore && searchState.products.length > 0 && (
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
                strokeDashoffset: 56.55 * (1 - searchState.feedbacksSinceFetch / 3),
              }}
            />
          </svg>
          <span>
            rate another {3 - searchState.feedbacksSinceFetch} item{3 - searchState.feedbacksSinceFetch === 1 ? '' : 's'} to rerank
          </span>
        </div>
      )}

      {searchState.fetchingMore && (
        <div className={`fixed-status-bar is-refreshing`} role="status" aria-live="polite">
          <span className="loading-spinner loading-spinner--sm" aria-hidden="true" />
          <span>Fetching more and reranking…</span>
        </div>
      )}

      <ProductGrid 
        products={searchState.products} 
        onFeedback={(itemUrl, feedbackType) =>
          searchActions.rerankProducts(imageState.uploadId, itemUrl, feedbackType)
        }
        onTune={uiActions.openTraitSheet}
        tunedUrls={searchState.traitPicks}
        disabled={searchState.loading}
      />

      {tunedItem && (
        <TraitSheet
          item={tunedItem}
          appliedPicks={searchState.traitPicks[tunedItem.url]}
          profile={searchState.traitProfile}
          profileError={searchState.profileError}
          onClose={uiActions.closeTraitSheet}
          onApply={(picks) =>
            searchActions.applyTraitPicks(imageState.uploadId, tunedItem.url, picks)
          }
        />
      )}

      {uiState.errorMessage && (
        <div className="toast toast-error" role="alert" onClick={uiActions.clearError}>
          {uiState.errorMessage}
          <button className="toast-close" aria-label="Dismiss">×</button>
        </div>
      )}

      </div>
    </ErrorBoundary>
  );
}

export default App;