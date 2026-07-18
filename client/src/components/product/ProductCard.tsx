import React from 'react';
import { components } from '../../types/api';
import '../../styles/product.css';


type ItemResponse = components['schemas']['ItemResponse'];

interface ProductCardProps {
  item: ItemResponse;
  onFeedback: (
    itemUrl: string,
    feedbackType: 'MORE' | 'LESS',
    concept?: string
  ) => Promise<void>;
  onCompare: (itemUrl: string) => Promise<void>;
  characteristics?: string[]; // Receives only its own traits array
  isLoading?: boolean;        // Receives only its own loading boolean
}

const ProductCard: React.FC<ProductCardProps> = ({
  item,
  onFeedback,
  onCompare,
  characteristics,
  isLoading,
}) => {
  const formatMatchScore = (score?: number) => {
    if (score == null) return '0% Match';
    return `${(score * 100).toFixed(0)}% Match`;
  };

  return (
    <div className="product-card">
      <a href={item.url} target="_blank" rel="noopener noreferrer">
        <img src={item.image_url} alt="Listing" loading="lazy" />
      </a>

      <div className="product-info">
        <div className="product-title">{item.title}</div>
        <div className="similarity-score-badge">{formatMatchScore(item.similarity_score)}</div>

        {/* Primary Action Bar: Clean, equal-width segmented toolbar */}
        <div className="product-action-bar">
          <button 
            className="action-bar-btn" 
            onClick={() => onFeedback(item.url, 'MORE')} 
            title="More Like This"
          >
            <span className="btn-icon">👍</span>
          </button>

          <button 
            className="action-bar-btn" 
            onClick={() => onFeedback(item.url, 'LESS')} 
            title="Less Like This"
          >
            <span className="btn-icon">👎</span>
          </button>

          {characteristics === undefined ? (
            <button 
              className="action-bar-btn compare-trigger" 
              disabled={isLoading}
              onClick={() => onCompare(item.image_url)}
            >
              {isLoading ? '...' : 'Compare'}
            </button>
          ) : (
            <button className="action-bar-btn compare-trigger active" disabled>
              ✓ Active
            </button>
          )}
        </div>

        {/* Secondary Section for Specific Aspect/Trait Feedback */}
        {characteristics !== undefined && (
          <div className="trait-refinement-container">
            <span className="trait-heading">Tune specific characteristics:</span>
            <div className="trait-pills-group">
              {characteristics.length === 0 ? (
                <span className="no-traits-label">No distinct traits found</span>
              ) : (
                characteristics.map((char, idx) => (
                  <div key={idx} className="trait-split-pill">
                    <span className="trait-name">{char}</span>
                    
                    <button
                      className="trait-action-btn boost"
                      onClick={() => onFeedback(item.url, 'MORE', char)}
                      title={`Show more items with ${char}`}
                    >
                      ＋
                    </button>
                    
                    <button
                      className="trait-action-btn bury"
                      onClick={() => onFeedback(item.url, 'LESS', char)}
                      title={`Show fewer items with ${char}`}
                    >
                      －
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ProductCard;