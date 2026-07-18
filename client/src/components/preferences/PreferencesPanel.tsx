import React from 'react';
import { CATEGORIES, CONDITION_OPTIONS } from '../../static/constants';
import SizePicker from './SizePicker';
import ColourPicker from './ColourPicker';

type Props = {
  selectedSizes: string[];
  toggleSize: (v: string) => void;
  maxPrice: string;
  setMaxPrice: (v: string) => void;
  selectedCategory: string;
  setSelectedCategory: (v: string) => void;
  selectedColors: string[];
  toggleColour: (v: string) => void;
  selectedConditions: string[];
  toggleCondition: (v: string) => void;
  isOpen: boolean;
  toggleOpen: () => void;
  onScrape: () => void;
};

const PreferencesPanel: React.FC<Props> = ({
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
}) => {
  return (
    <div style={{
      background: '#111113',
      border: '1px solid #222227',
      borderRadius: '10px',
      margin: '12px auto',
      width: 'calc(100% - 24px)',
      boxShadow: '0 4px 24px rgba(0, 0, 0, 0.5)',
      overflow: 'hidden'
    }}>
      <div 
        role="button"
        onClick={toggleOpen}
        style={{
          width: '100%',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          padding: '12px 18px',
          cursor: 'pointer',
          userSelect: 'none',
          color: '#f4f4f6',
          fontWeight: 600,
          fontSize: '14px'
        }}
      >
        <span>⚙️ Search Filters</span>
        <span style={{ transform: isOpen ? 'rotate(180deg)' : 'none', transition: 'transform 0.2s', fontSize: '10px', color: '#71717a' }}>▼</span>
      </div>

      {isOpen && (
        <div style={{
          padding: '16px 20px 20px 20px',
          borderTop: '1px solid #222227',
          background: '#0b0b0c',
          display: 'flex',
          flexDirection: 'column',
          gap: '16px'
        }}>
          {/* Category & Price Fields */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '10px', fontWeight: 700, color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Category</label>
              <select 
                value={selectedCategory} 
                onChange={(e) => setSelectedCategory(e.target.value)}
                style={{ background: '#16161a', border: '1px solid #2a2a32', borderRadius: '6px', padding: '8px 12px', color: '#e4e4e7', fontSize: '13px', width: '100%' }}
              >
                {CATEGORIES.map(cat => <option key={cat} value={cat}>{cat}</option>)}
              </select>
            </div>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
              <label style={{ fontSize: '10px', fontWeight: 700, color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Budget Cap</label>
              <input
                type="number"
                value={maxPrice}
                onChange={(e) => setMaxPrice(e.target.value)}
                placeholder="See all prices"
                style={{ background: '#16161a', border: '1px solid #2a2a32', borderRadius: '6px', padding: '8px 12px', color: '#e4e4e7', fontSize: '13px', width: '100%', boxSizing: 'border-box' }}
              />
            </div>
          </div>

          {/* Colours Wrapper */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ fontSize: '10px', fontWeight: 700, color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Colours Palette</label>
            <ColourPicker selectedColors={selectedColors} toggleColour={toggleColour} />
          </div>

          {/* Sizes Wrapper */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ fontSize: '10px', fontWeight: 700, color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Target Sizes</label>
            <SizePicker selectedSizes={selectedSizes} toggleSize={toggleSize} />
          </div>

          {/* Condition Chips Wrapper (Converted to layout-safe divs) */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
            <label style={{ fontSize: '10px', fontWeight: 700, color: '#71717a', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Garment Condition</label>
            <div style={{ display: 'flex', flexDirection: 'row', flexWrap: 'wrap', gap: '8px' }}>
              {CONDITION_OPTIONS.map(option => {
                const isSelected = selectedConditions.includes(option.value);
                return (
                  <div
                    key={option.value}
                    role="button"
                    onClick={() => toggleCondition(option.value)}
                    style={{
                      background: isSelected ? 'rgba(0, 210, 255, 0.08)' : '#16161a',
                      border: isSelected ? '1px solid #00d2ff' : '1px solid #2a2a32',
                      color: isSelected ? '#00d2ff' : '#d4d4d8',
                      padding: '6px 14px',
                      borderRadius: '16px',
                      fontSize: '12px',
                      cursor: 'pointer',
                      whiteSpace: 'nowrap',
                      userSelect: 'none'
                    }}
                  >
                    {option.label}
                  </div>
                );
              })}
            </div>
          </div>

          {/* Footer CTA */}
          <div style={{ display: 'flex', justifyContent: 'flex-end', borderTop: '1px solid #222227', paddingTop: '14px', marginTop: '4px' }}>
            <button 
              onClick={onScrape} 
              style={{ background: '#00d2ff', color: '#000', fontWeight: 600, border: 'none', borderRadius: '6px', padding: '10px 20px', fontSize: '13px', cursor: 'pointer', width: 'auto' }}
            >
              Apply Filters & Scrape
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default PreferencesPanel;