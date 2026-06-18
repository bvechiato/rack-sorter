import { COLORS } from '../../static/constants';

function ColourPicker({ selectedColors, toggleColor }) {
  return (
    <div className="color-picker-container">
      <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
        Colours
      </label>
      
      <div className="color-swatch-grid">
        {COLORS.map((color) => {
          const isSelected = selectedColors.includes(color.name);
          return (
            <div
              key={color.name}
              className={`swatch ${color.class} ${isSelected ? 'selected' : ''}`}
              onClick={() => toggleColor(color.name)}
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