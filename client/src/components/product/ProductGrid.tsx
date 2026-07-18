import React, { useState, useEffect, useRef } from 'react';
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
  const [containerWidth, setContainerWidth] = useState(0);

  // Measure the EXACT available width of the grid container
  useEffect(() => {
    if (!containerRef.current) return;

    const observer = new ResizeObserver((entries) => {
      for (let entry of entries) {
        setContainerWidth(entry.contentRect.width);
      }
    });

    observer.observe(containerRef.current);
    return () => observer.disconnect();
  }, []);

  // NEW: Intercept feedback action and trigger a smooth scroll to the top
  const handleFeedbackAndScroll = async (
    itemUrl: string,
    feedbackType: 'MORE' | 'LESS',
    concept?: string
  ) => {
    // 1. Fire off the feedback network request/state handler asynchronously
    const feedbackPromise = onFeedback(itemUrl, feedbackType, concept);

    // 2. Instantly scroll the viewport back to the top of the grid container
    containerRef.current?.scrollIntoView({ 
      behavior: 'smooth', 
      block: 'start' 
    });

    // 3. Await the underlying promise to preserve async behavior downstream
    await feedbackPromise;
  };

  if (!products || products.length === 0) {
    return (
      <div className="results-grid">
        <div style={{ gridColumn: 'span 12', textAlign: 'center', color: 'var(--text-muted)', padding: '40px 0' }}>
          No matching data layers found in background storage.
        </div>
      </div>
    );
  }

  const IDEAL_CARD_WIDTH = 300; 
  const dynamicColumns = containerWidth > 0 
    ? Math.max(1, Math.floor(containerWidth / IDEAL_CARD_WIDTH)) 
    : 3; 

  return (
    <div ref={containerRef} style={{ width: '100%' }}>
      <Masonry
        breakpointCols={dynamicColumns}
        className="results-grid-masonry"
        columnClassName="results-grid-masonry_column"
      >
        {products.map((item, index) => (
          <ProductCard
            key={index}
            item={item}
            onFeedback={handleFeedbackAndScroll} // Pass the wrapper function here
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