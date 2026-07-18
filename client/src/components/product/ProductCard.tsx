import React from 'react';
import { components } from '../../types/api';
import '../../styles/product.css';

type ItemResponse = components['schemas']['ItemResponse'];

interface ProductCardProps {
  item: ItemResponse;
  onFeedback: (itemUrl: string, feedbackType: 'MORE' | 'LESS', concept?: string) => Promise<void>;
  onCompare: (itemUrl: string) => Promise<void>;
  characteristics?: string[];
  isLoading?: boolean;
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

  const hasTraitsLoaded = characteristics !== undefined;

  return (
    <div className="product-card">
      <a href={item.url} target="_blank" rel="noopener noreferrer" className="product-img-link">
        <img src={item.image_url} alt="Listing" loading="lazy" className="product-img" />
      </a>

      <div className="product-info">
        <div className="product-title">{item.title}</div>
        <div className="similarity-score-badge">{formatMatchScore(item.similarity_score)}</div>

        {/* Primary Touch Grid Actions */}
        <div className="product-actions-grid">
          <div 
            role="button"
            className="action-btn action-btn-more"
            onClick={() => onFeedback(item.url, 'MORE')} 
          >
            ＋ More
          </div>

          <div 
            role="button"
            className="action-btn action-btn-less"
            onClick={() => onFeedback(item.url, 'LESS')} 
          >
            － Less
          </div>

          <div 
            role="button" 
            onClick={() => !isLoading && onCompare(item.image_url)}
            className={`tune-style-trigger ${hasTraitsLoaded ? 'is-active' : ''} ${isLoading ? 'is-loading' : ''}`}
          >
            Trait Specific
          </div>
        </div>

        {hasTraitsLoaded && (
          <div className="trait-carousel-container">            
            <div className="trait-carousel-track">
              {characteristics.length === 0 ? (
                <span className="no-traits-label">No distinct traits found</span>
              ) : (
                characteristics.map((char, idx) => (
                  <div key={idx} className="trait-widget-card">
                    
                    {/* Top Tier: Label */}
                    <div className="trait-widget-title" title={char}>
                      {char}
                    </div>
                    
                    {/* Bottom Tier: Split Action Row [ + | - ] */}
                    <div className="trait-widget-actions">
                      <div 
                        role="button" 
                        onClick={() => onFeedback(item.url, 'MORE', char)} 
                        className="trait-widget-btn widget-btn-more"
                      >
                        ＋
                      </div>
                      <div 
                        role="button" 
                        onClick={() => onFeedback(item.url, 'LESS', char)} 
                        className="trait-widget-btn widget-btn-less"
                      >
                        －
                      </div>
                    </div>

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