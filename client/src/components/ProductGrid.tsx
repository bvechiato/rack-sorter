import React from 'react';
import { components } from '../types/api'; 

type ItemResponse = components['schemas']['ItemResponse'];

const ProductGrid: React.FC<{ products: ItemResponse[] }> = ({ products }) => {
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

  // 1. Clone and sort products by similarity_score descending (highest first)
  const sortedProducts = [...products].sort((a, b) => {
    const scoreA = a.similarity_score ?? 0;
    const scoreB = b.similarity_score ?? 0;
    return scoreB - scoreA;
  });

  // 2. Helper to format decimal scores (e.g., 0.8543) into clean match percentages (e.g., 85% Match)
  const formatMatchScore = (score?: number) => {
    if (score == null) return '0% Match';
    return `${(score * 100).toFixed(0)}% Match`;
  };

  return (
    <div className="results-grid">
      {sortedProducts.map((item, index) => (
        <a
          key={index}
          className="product-card"
          href={item.url}
          target="_blank"
          rel="noopener noreferrer"
        >
          <img src={item.image_url} alt="Listing" loading="lazy" />
          <div className="product-info">
            <div className="product-title">{item.title}</div>
            <div className="similarity-score-badge">
              {formatMatchScore(item.similarity_score)}
            </div>
          </div>
        </a>
      ))}
    </div>
  );
}

export default ProductGrid;