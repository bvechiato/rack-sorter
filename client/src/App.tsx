import React, { useEffect } from 'react';
import Header from './components/Header';
import SearchActionBar from './components/SearchActionBar';
import KeywordSuggestions from './components/KeywordSuggestions';
import PreferencesPanel from './components/preferences/PreferencesPanel';
import ProductGrid from './components/ProductGrid';
import VectorWeightPanel from './components/VectorWeightPanel';
import LoadingIndicator from './components/LoadingIndicator';
import {
  useFilters,
  useImageAnalysis,
  useProductSearch,
  useVectorWeights,
  useUIState,
} from './hooks';
import './styles/index.css';
import './styles/generic.css';

function App() {
  const { filters, actions: filterActions } = useFilters();
  const { state: imageState, actions: imageActions } = useImageAnalysis();
  const { state: searchState, actions: searchActions } = useProductSearch();
  const { weights, updateWeight } = useVectorWeights(imageState.suggestedTags);
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

  const handleRerank = async () => {
    try {
      await searchActions.rerankProducts(weights);
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
        isOpen={uiState.preferencesOpen || imageState.showSuggestions}
        toggleOpen={uiActions.togglePreferences}
        onScrape={handleScrape}
      />

      {searchState.loading && <LoadingIndicator />}

      <ProductGrid products={searchState.products} />

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

      <VectorWeightPanel
        isOpen={uiState.panelOpen}
        suggestedTags={imageState.suggestedTags}
        weights={weights}
        updateWeight={updateWeight}
        onRerank={handleRerank}
        onClose={uiActions.closePanel}
      />
    </div>
  );
}

export default App;
