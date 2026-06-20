import React from 'react';

type Props = {
  isOpen: boolean;
  suggestedTags: string[];
  weights: Record<string, number>;
  updateWeight: (tag: string, value: string | number) => void;
  onRerank: () => void;
  onClose: () => void;
};

const VectorWeightPanel: React.FC<Props> = ({ isOpen, suggestedTags, weights, updateWeight, onRerank, onClose }) => {
  return (
    <div className={`side-panel ${isOpen ? 'active' : ''}`}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
        <h3 style={{ margin: 0, fontSize: '16px' }}>🧬 Vector Weight Matrix</h3>
        <span
          onClick={onClose}
          style={{ cursor: 'pointer', fontSize: '20px', color: 'var(--text-muted)' }}
        >
          ×
        </span>
      </div>
      <div>
        {suggestedTags.length === 0 ? (
          <p style={{ fontSize: '13px', color: 'var(--text-muted)', textAlign: 'center', margin: '20px 0' }}>
            Upload an archetype image to extract deep vector dimensions.
          </p>
        ) : (
          suggestedTags.map(tag => (
            <div key={tag} className="slider-group">
              <div className="slider-header">
                <span>{tag}</span>
                <span>{weights[tag] ?? 0.8}</span>
              </div>
              <input
                type="range"
                className="weight-slider"
                min="0"
                max="1"
                step="0.1"
                value={weights[tag] ?? 0.8}
                onChange={(e) => updateWeight(tag, e.target.value)}
              />
            </div>
          ))
        )}
      </div>
      <button onClick={onRerank} style={{ marginTop: '12px' }}>Sort</button>
    </div>
  );
}

export default VectorWeightPanel;
