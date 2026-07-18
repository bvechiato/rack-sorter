import React, { useRef } from 'react';
import Masonry from 'react-masonry-css';
import ProductCard from './ProductCard';
import { components } from '../../types/api';

type ItemResponse = components['schemas']['ItemResponse'];

interface ProductGridProps {
  products: ItemResponse[];
  onFeedback: (itemUrl: string, feedbackType: 'MORE' | 'LESS', concept?: string) => Promise<void>;
  onCompare: (itemUrl: string) => Promise<void>;
  comparisonCharacteristics?: Record<string, string[]>;
  comparisonLoadingMap?: Record<string, boolean>;
}

const ProductGrid: React.FC<ProductGridProps> = ({
  products,
  onFeedback,
  onCompare,
  comparisonCharacteristics = {},
  comparisonLoadingMap = {},
}) => {
  const containerRef = useRef<HTMLDivElement>(null);

  const handleFeedbackAndScroll = async (
    itemUrl: string,
    feedbackType: 'MORE' | 'LESS',
    concept?: string
  ) => {
    const feedbackPromise = onFeedback(itemUrl, feedbackType, concept);
    containerRef.current?.scrollIntoView({ 
      behavior: 'smooth', 
      block: 'start' 
    });
    await feedbackPromise;
  };

  if (!products || products.length === 0) {
    return (
      <div className="results-grid">
        <div style={{ textAlign: 'center', color: '#71717a', padding: '40px 0', width: '100%' }}>
          No matching data layers found in background storage.
        </div>
      </div>
    );
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
            key={index}
            item={item}
            onFeedback={handleFeedbackAndScroll}
            onCompare={onCompare}
            characteristics={comparisonCharacteristics[item.image_url]}
            isLoading={comparisonLoadingMap[item.image_url]}
          />
        ))}
      </Masonry>
    </div>
  );
};

export default ProductGrid;