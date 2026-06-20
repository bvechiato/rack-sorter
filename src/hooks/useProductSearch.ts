import { useState } from 'react';
import { fetchInitial, rerank } from '../api';

export function useProductSearch() {
  const [currentPool, setCurrentPool] = useState<any[]>([]);
  const [products, setProducts] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);

  const scrapeProducts = async (uploadId: any, keyword: string, filters: any) => {
    if (!keyword.trim()) {
      throw new Error('Please provide or parse a lookup keyword first.');
    }

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('keyword', keyword);
      formData.append('selectedSizes', filters.selectedSizes.join(','));
      formData.append('maxPrice', filters.maxPrice);
      formData.append('selectedCategory', filters.selectedCategory);
      formData.append('selectedColors', filters.selectedColors.join(','));
      formData.append('selectedConditions', filters.selectedConditions.join(','));
      formData.append('uploadId', uploadId);

      console.log(`[INFO] Sending scrape request with filters: ${JSON.stringify(formData)}`);

      const poolData = await fetchInitial(formData);
      setCurrentPool(poolData.pool || []);
      setProducts(poolData.pool || []);
    } catch (err) {
      throw new Error('Failed fetching items with the chosen keyword.');
    } finally {
      setLoading(false);
    }
  };

  const rerankProducts = async (weights: any) => {
    if (!currentPool.length) {
      throw new Error('Run an initial scraping pass before sorting vectors.');
    }

    setLoading(true);
    try {
      const formData = new FormData();
      formData.append('pool_data', JSON.stringify(currentPool));
      formData.append('weights', JSON.stringify(weights));

      const rankedData = await rerank(formData);
      setProducts(rankedData);
    } catch (err) {
      throw new Error('Vector calculation error');
    } finally {
      setLoading(false);
    }
  };

  return {
    state: {
      currentPool,
      products,
      loading,
    },
    actions: {
      scrapeProducts,
      rerankProducts,
    },
  };
}
