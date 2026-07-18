import React, { useEffect } from 'react';
import Header from './components/Header';
import SearchActionBar from './components/SearchActionBar';
import KeywordSuggestions from './components/KeywordSuggestions';
import PreferencesPanel from './components/preferences/PreferencesPanel';
import ProductGrid from './components/product/ProductGrid';
import ActiveFiltersSummary from './components/preferences/ActiveFiltersSummary';
import LoadingIndicator from './components/LoadingIndicator';
import {
  useFilters,
  useImageAnalysis,
  useProductSearch,
  useUIState,
  useCompareItem
} from './hooks';
import './styles/index.css';
import './styles/generic.css';

function App() {
  const { filters, actions: filterActions } = useFilters();
  const { state: imageState, actions: imageActions } = useImageAnalysis();
  const { state: searchState, actions: searchActions } = useProductSearch();
  const { state: comparisonState, actions: comparisonActions } = useCompareItem();
  const { state: uiState, actions: uiActions } = useUIState();

  const handleImageUpload = async (file: File | null) => {
    if (!file) return;
    try {
      await imageActions.handleImageUpload(file as File);
    } catch (err: any) {
      alert(err.message);
    }
  };

  const handleScrape = async () => {
    try {
      await searchActions.scrapeProducts(imageState.uploadId, imageState.confirmedKeyword, filters);
      uiActions.setPanelOpen(false);
    } catch (err: any) {
      alert(err.message);
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

  return (
    <div>
      <Header />

      <SearchActionBar
        confirmedKeyword={imageState.confirmedKeyword}
        setConfirmedKeyword={imageActions.setConfirmedKeyword}
        onImageUpload={handleImageUpload}
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

      {searchState.loading && <LoadingIndicator />}

      {!searchState.loading && searchState.products.length > 0 && (
        <ActiveFiltersSummary 
          keyword={imageState.confirmedKeyword} 
          filters={filters} 
        />
      )}

      <ProductGrid 
        products={searchState.products} 
        onFeedback={(imageUrl: string, feedbackType: "MORE" | "LESS", concept?: string) => 
          searchActions.rerankProducts(imageState.uploadId, imageUrl, feedbackType, concept)
        }
        onCompare={(imageUrl: string) => 
          comparisonActions.compareItem(imageState.uploadId, imageUrl)
        }
        comparisonCharacteristics={comparisonState.characteristics}
        comparisonLoadingMap={comparisonState.loadingMap}
      />

      <div
        className={`panel-overlay ${uiState.panelOpen ? 'show' : ''}`}
        onClick={uiActions.closePanel}
      />

      <button
        className="fab-menu"
        onClick={uiActions.togglePanel}
        title="Adjust Weights Matrix"
      >
        ☰
      </button>
    </div>
  );
}

export default App;