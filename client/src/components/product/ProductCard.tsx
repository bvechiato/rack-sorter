import React from 'react';
import { components } from '../../types/api';
import '../../styles/product.css';

type ItemResponse = components['schemas']['ItemResponse'];

interface ProductCardProps {
  item: ItemResponse;
  onFeedback: (itemUrl: string, feedbackType: 'MORE' | 'LESS') => Promise<void>;
  onTune: (itemUrl: string) => void;
  /** True when this item already carries trait feedback, so the trigger reads as active. */
  isTuned?: boolean;
  /** A rerank is in flight; block duplicate taps until it settles. */
  disabled?: boolean;
}

const ProductCard: React.FC<ProductCardProps> = ({ item, onFeedback, onTune, isTuned, disabled }) => {
  const score = item.rerank_score ?? item.similarity_score ?? 0;
  // `rerank_score` is the base cosine plus a trait bonus, so it can exceed 1 after
  // strong feedback. The badge is a match indicator, not a sum: saturate at 100%.
  const formatMatchScore = (value: number) => `${(Math.min(1, Math.max(0, value)) * 100).toFixed(0)}% Match`;

  return (
    <div className="product-card">
      <a href={item.url} target="_blank" rel="noopener noreferrer" className="product-img-link">
        <img src={item.image_url} alt="Listing" loading="lazy" className="product-img" />
      </a>

      <div className="product-info">
        <div className="product-title">{item.title}</div>
        <div className="similarity-score-badge">{formatMatchScore(score)}</div>

        {/* Primary Touch Grid Actions */}
        <div className="product-actions-grid">
          <button
            type="button"
            className="action-btn action-btn-more"
            disabled={disabled}
            onClick={() => onFeedback(item.url, 'MORE')}
          >
            ＋ More
          </button>

          <button
            type="button"
            className="action-btn action-btn-less"
            disabled={disabled}
            onClick={() => onFeedback(item.url, 'LESS')}
          >
            － Less
          </button>

          <button
            type="button"
            className={['tune-style-trigger', isTuned ? 'is-active' : '', disabled ? 'is-loading' : '']
              .filter(Boolean)
              .join(' ')}
            aria-haspopup="dialog"
            disabled={disabled}
            onClick={() => onTune(item.url)}
          >
            ⚙ Tune
          </button>
        </div>
      </div>
    </div>
  );
};

export default ProductCard;
