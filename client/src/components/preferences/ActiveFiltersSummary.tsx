import React from 'react';
import { useFilters } from '../../hooks';
import { SIZES, CONDITION_OPTIONS } from '../../static/constants';
import '../../styles/preferences.css';

interface SummaryProps {
  keyword: string;
  filters: ReturnType<typeof useFilters>['filters'];
}

const ActiveFiltersSummary: React.FC<SummaryProps> = ({ keyword, filters }) => {
  
  // 1. DEDUPLICATE COLORS: Safeguards against array duplicates 
  const uniqueColors = Array.from(new Set(filters.selectedColors));
  
  // 2. AGGREGATE & SORT SIZES: Filter directly against the master constants array 
  // This automatically guarantees sizes show up sorted from smallest to largest
  const activeSizes = SIZES
    .filter(sizeOption => filters.selectedSizes.includes(sizeOption.value))
    .map(sizeOption => sizeOption.label.split(' / ')[0]); // Trims down "S / UK 8-10" -> "S"

  // 3. AGGREGATE CONDITIONS: Combines values cleanly using master array ordering
  const activeConditions = CONDITION_OPTIONS
    .filter(condOption => filters.selectedConditions.includes(condOption.value))
    .map(condOption => condOption.label);

  const isCategoryActive = filters.selectedCategory && filters.selectedCategory !== 'See all';

  const hasActiveFilters = 
    keyword || 
    isCategoryActive || 
    uniqueColors.length > 0 || 
    activeSizes.length > 0 || 
    filters.maxPrice || 
    activeConditions.length > 0;

  if (!hasActiveFilters) return null;

  return (
    <div className="active-filters-summary">
      <span className="summary-label">Showing results for:</span>
      <div className="summary-chips-container">
        
        {/* Keyword Phrase */}
        {keyword && <span className="summary-badge font-italic">🔍 "{keyword}"</span>}
        
        {/* Clean Category Group */}
        {isCategoryActive && <span className="summary-badge">📁 {filters.selectedCategory}</span>}
        
        {/* Combined Colors Pill */}
        {uniqueColors.length > 0 && (
          <span className="summary-badge color-badge">
            🎨 {uniqueColors.join(', ')}
          </span>
        )}
        
        {/* Combined & Ordered Sizes Pill */}
        {activeSizes.length > 0 && (
          <span className="summary-badge size-badge">
            📏 {activeSizes.join(', ')}
          </span>
        )}
        
        {/* Maximum Price Cap */}
        {filters.maxPrice && <span className="summary-badge price-badge">💰 Under £{filters.maxPrice}</span>}
        
        {/* Combined Conditions Pill */}
        {activeConditions.length > 0 && (
          <span className="summary-badge condition-badge">
            ✨ {activeConditions.join(', ')}
          </span>
        )}
        
      </div>
    </div>
  );
};

export default ActiveFiltersSummary;