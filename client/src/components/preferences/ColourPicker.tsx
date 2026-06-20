import React from 'react';
import { COLORS } from '../../static/constants';

type Props = {
  selectedColors: string[];
  toggleColour: (c: string) => void;
};

const ColourPicker: React.FC<Props> = ({ selectedColors, toggleColour }) => {
  return (
    <div className="color-picker-container">
      <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
        Colours
      </label>
      
      <div className="color-swatch-grid">
        <div
            key="None"
            className={`swatch ${selectedColors.length == 0 ? 'selected' : ''}`}
            onClick={() => toggleColour("None")}
            title="None"
        > None </div>
        {COLORS.map((color) => {
          const isSelected = selectedColors.includes(color.name);
          return (
            <div
              key={color.name}
              className={`swatch ${color.class} ${isSelected ? 'selected' : ''}`}
              onClick={() => toggleColour(color.name)}
              title={color.name}
            >
              {isSelected && <span className="checkmark">✓</span>}
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default ColourPicker;
