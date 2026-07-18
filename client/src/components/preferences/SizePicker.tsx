import React from 'react';
import { SIZES } from '../../static/constants';

type Props = {
  selectedSizes: string[];
  toggleSize: (v: string) => void;
};

const SizePicker: React.FC<Props> = ({ selectedSizes, toggleSize }) => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
      <select 
        onChange={(e) => {
          if (e.target.value) {
            toggleSize(e.target.value);
            e.target.value = ""; 
          }
        }}
        style={{ background: '#16161a', border: '1px solid #2a2a32', borderRadius: '6px', padding: '8px 12px', color: '#e4e4e7', fontSize: '13px', width: '100%', cursor: 'pointer' }}
      >
        <option value="">
          {selectedSizes.length > 0 ? 'Add another size...' : 'Select sizes to filter...'}
        </option>
        {SIZES.filter(s => !selectedSizes.includes(s.value)).map(s => (
          <option key={s.value} value={s.value}>{s.label}</option>
        ))}
        {selectedSizes.length > 0 && <option value="See all">Clear and see all</option>}
      </select>

      {selectedSizes.length > 0 && (
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px', marginTop: '2px' }}>
          {selectedSizes.map(sizeValue => {
            const sizeObj = SIZES.find(s => s.value === sizeValue);
            return (
              <div 
                key={sizeValue} 
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  background: '#16161a',
                  border: '1px solid #2a2a32',
                  borderRadius: '4px',
                  padding: '3px 4px 3px 8px',
                  fontSize: '12px',
                  color: '#e4e4e7'
                }}
              >
                <span style={{ paddingRight: '6px', fontWeight: 500 }}>{sizeObj?.label}</span>
                <span 
                  role="button" 
                  onClick={() => toggleSize(sizeValue)}
                  style={{
                    cursor: 'pointer',
                    color: '#71717a',
                    fontSize: '10px',
                    padding: '2px 4px',
                    borderRadius: '3px',
                    userSelect: 'none'
                  }}
                  onMouseEnter={(e) => { e.currentTarget.style.color = '#ef4444'; e.currentTarget.style.background = 'rgba(239, 68, 68, 0.1)'; }}
                  onMouseLeave={(e) => { e.currentTarget.style.color = '#71717a'; e.currentTarget.style.background = 'transparent'; }}
                >
                  ✕
                </span>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default SizePicker;