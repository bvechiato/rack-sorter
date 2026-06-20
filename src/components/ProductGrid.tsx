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

  return (
    <div className="results-grid">
      {products.map((item, index) => (
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
          </div>
        </a>
      ))}
    </div>
  );
}

export default ProductGrid;
