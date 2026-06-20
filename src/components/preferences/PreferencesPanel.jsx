import React from 'react';
import { CATEGORIES, CONDITION_OPTIONS } from '../../static/constants';
import SizePicker from './SizePicker';
import ColourPicker from './ColourPicker';

function PreferencesPanel({
  selectedSizes,
  toggleSize,
  maxPrice,
  setMaxPrice,
  selectedCategory,
  setSelectedCategory,
  selectedColors,
  toggleColour,
  selectedConditions,
  toggleCondition,
  isOpen,
  toggleOpen,
  onScrape,
}) {
  return (
    <div className="pref-container">
      <div
        className={`pref-summary ${isOpen ? 'open' : ''}`}
        onClick={toggleOpen}
      >
        Search filters
      </div>
      {isOpen && (
        <div className="pref-content show">
          <div style={{ marginBottom: '12px' }}>
            <label>Have a category in mind?</label>
            <select value={selectedCategory} onChange={(e) => setSelectedCategory(e.target.value)}>
              {CATEGORIES.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>

          <ColourPicker selectedColors={selectedColors} toggleColour={toggleColour} />

          <SizePicker selectedSizes={selectedSizes} toggleSize={toggleSize} />

          <div style={{ display: 'flex', gap: '8px', marginBottom: '12px' }}>
            <div style={{ flex: 1 }}>
              <label>Max price?</label>
              <input
                type="number"
                value={maxPrice}
                onChange={(e) => setMaxPrice(e.target.value)}
                placeholder="No, see all"
                className='inline'
              />
            </div>
          </div>

          <div>
            <label>Item Condition</label>
            <div className="condition-chips">
              {CONDITION_OPTIONS.map(option => (
                <div
                  key={option.value}
                  className={`chip ${selectedConditions.includes(option.value) ? 'selected' : ''}`}
                  onClick={() => toggleCondition(option.value)}
                >
                  {option.label}
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
      <button onClick={onScrape} className="btn-inline">Scrape</button>
    </div>
  );
}

export default PreferencesPanel;
