import React from 'react';

function ProductGrid({ products }) {
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
            {item.score && (
              <div className="product-score">Match: {Math.round(item.score * 100)}%</div>
            )}
          </div>
        </a>
      ))}
    </div>
  );
}

export default ProductGrid;
