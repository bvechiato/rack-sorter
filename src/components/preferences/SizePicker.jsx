import React from 'react';
import { SIZES } from '../../static/constants';
import './style.css';

function SizePicker({ selectedSizes, toggleSize }) {
  return (
    <div className="size-picker-container">
      <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
        Sizes
      </label>
      
      {/* Selection Menu */}
      <select 
        className="size-dropdown"
        onChange={(e) => {
            if (e.target.value) {
            toggleSize(e.target.value); // Pass the value, not the event
            e.target.value = ""; 
            }
        }}
      >
        <option value="">{selectedSizes.length > 0 ? 'Select size to add...' : 'See all'}</option>
        {SIZES.filter(s => !selectedSizes.includes(s.value)).map(s => (
          <option key={s.value} value={s.value}>
            {s.label}
          </option>
        ))}
      </select>

      {/* Active Tags */}
      <div className="size-tags-grid">
        {selectedSizes.map(sizeValue => {
          const sizeObj = SIZES.find(s => s.value === sizeValue);
          return (
            <div key={sizeValue} className="size-tag">
              {sizeObj?.label}
              <button 
                type="button" 
                onClick={() => toggleSize(sizeValue)}
                className="remove-btn"
              >×</button>
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default SizePicker;