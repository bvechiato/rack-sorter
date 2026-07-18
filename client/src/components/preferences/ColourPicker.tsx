import React from 'react';
import { COLORS } from '../../static/constants';

type Props = {
  selectedColors: string[];
  toggleColour: (c: string) => void;
};

const ColourPicker: React.FC<Props> = ({ selectedColors, toggleColour }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'row', flexWrap: 'wrap', gap: '10px', alignItems: 'center' }}>
      {/* Converted to div to eliminate global button width layout breakages */}
      <div
        role="button"
        onClick={() => toggleColour("None")}
        style={{
          background: selectedColors.length === 0 ? 'rgba(0, 210, 255, 0.1)' : '#16161a',
          border: selectedColors.length === 0 ? '1px solid #00d2ff' : '1px solid #2a2a32',
          color: selectedColors.length === 0 ? '#00d2ff' : '#a1a1aa',
          padding: '6px 12px',
          borderRadius: '16px',
          fontSize: '12px',
          fontWeight: 500,
          cursor: 'pointer',
          whiteSpace: 'nowrap',
          userSelect: 'none'
        }}
      >
        All Colours
      </div>

      {COLORS.map((color) => {
        const isSelected = selectedColors.includes(color.name);
        return (
          <div
            key={color.name}
            role="button"
            onClick={() => toggleColour(color.name)}
            title={color.name}
            className={color.class} // Keeps your dynamic color class background configurations intact
            style={{
              width: '26px',
              height: '26px',
              borderRadius: '50%',
              cursor: 'pointer',
              border: isSelected ? '2px solid #00d2ff' : '1px solid #2a2a32',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxSizing: 'border-box',
              boxShadow: isSelected ? '0 0 8px rgba(0, 210, 255, 0.4)' : 'none'
            }}
          >
            {isSelected && (
              <span style={{ fontSize: '12px', color: '#fff', fontWeight: 'bold', textShadow: '0 1px 2px rgba(0,0,0,0.8)' }}>
                ✓
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
};

export default ColourPicker;