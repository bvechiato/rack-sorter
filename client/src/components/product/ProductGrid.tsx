import React, { useRef } from 'react';
import Masonry from 'react-masonry-css';
import ProductCard from './ProductCard';
import { components } from '../../types/api';

type ItemResponse = components['schemas']['ItemResponse'];

interface ProductGridProps {
  products: ItemResponse[];
  onFeedback: (itemUrl: string, feedbackType: 'MORE' | 'LESS') => Promise<void>;
  onTune: (itemUrl: string) => void;
  tunedUrls?: Record<string, unknown>;
  /** A rerank is in flight; card actions stay disabled until it settles. */
  disabled?: boolean;
}

const ProductGrid: React.FC<ProductGridProps> = ({ products, onFeedback, onTune, tunedUrls = {}, disabled }) => {
  const containerRef = useRef<HTMLDivElement>(null);

  if (!products || products.length === 0) {
    return null;
  }

  // Pure, CSS-driven column breakpoints. No layout calculation lag.
  const breakpointColumnsObj = {
    default: 4,  // Desktop widescreen
    1100: 3,     // Laptops
    768: 2,      // Tablets
    480: 2       // Mobile phones (Forces a readable 2-column grid instead of 3)
  };

  return (
    <div ref={containerRef} style={{ width: '100%', padding: '0 8px', boxSizing: 'border-box' }}>
      <Masonry
        breakpointCols={breakpointColumnsObj}
        className="results-grid-masonry"
        columnClassName="results-grid-masonry_column"
      >
        {products.map((item, index) => (
          <ProductCard
            key={item.url || index}
            item={item}
            onFeedback={(itemUrl, feedbackType) => onFeedback(itemUrl, feedbackType)}
            onTune={onTune}
            isTuned={Boolean(tunedUrls[item.url])}
            disabled={disabled}
          />
        ))}
      </Masonry>
    </div>
  );
};

export default ProductGrid;
