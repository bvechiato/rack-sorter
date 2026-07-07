import React from 'react';
import { components } from '../types/api'; 

type ItemResponse = components['schemas']['ItemResponse'];

const ProductGrid: React.FC<{
  products: ItemResponse[];
  onFeedback: (
    itemUrl: string,
    feedbackType: 'MORE' | 'LESS'
  ) => Promise<void>;
}> = ({ products, onFeedback }) => {
  if (!products || products.length === 0) {
    return (
      <div className="results-grid">
        <div style={{
          gridColumn: 'span 12',
          textAlign: 'center',
          color: 'var(--text-muted)',
          padding: '40px 0',
        }}>
          No matching data layers found in background storage.
        </div>
      </div>
    );
  }

  const formatMatchScore = (score?: number) => {
    if (score == null) return '0% Match';
    return `${(score * 100).toFixed(0)}% Match`;
  };

  return (
    <div className="results-grid">
      {products.map((item, index) => (
        <div
          key={index}
          className="product-card"
        >
          <a
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
          >
            <img
              src={item.image_url}
              alt="Listing"
              loading="lazy"
            />
          </a>

          <div className="product-info">
            <div className="product-title">
              {item.title}
            </div>

            <div className="similarity-score-badge">
              {formatMatchScore(item.similarity_score)}
            </div>

            <div className="feedback-actions">
              <button onClick={() => onFeedback(item.url, 'MORE')}>
                👍 More Like This
              </button>

              <button onClick={() => onFeedback(item.url, 'LESS')}>
                👎 Less Like This
              </button>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}

export default ProductGrid;