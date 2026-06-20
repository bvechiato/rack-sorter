import { useState } from 'react';
import { fetchInitial } from '../api';

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
      const requestData = {
        uploadId: Number(uploadId),
        keyword: keyword,
        selectedSizes: filters.selectedSizes.join(','),
        selectedCategory: filters.selectedCategory,
        selectedColors: filters.selectedColors.join(','),
        maxPrice: String(filters.maxPrice),
        selectedConditions: filters.selectedConditions.join(',')
      };

      // Now this passes type checking!
      const poolData = await fetchInitial(requestData);
      console.log(`[INFO] Sending scrape request with filters: ${JSON.stringify(requestData)}`);

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

    //   const rankedData = await rerank(formData);
    //   setProducts(rankedData);
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
