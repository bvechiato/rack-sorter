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

  const rerankProducts = async (uploadId: any, itemUrl: string, feedbackType: 'MORE' | 'LESS') => {
    if (!uploadId) {
      throw new Error('Missing upload id');
    }

    setLoading(true);

    try {
      const rankedData = await rerank({
        upload_id: uploadId,
        item_url: itemUrl,
        feedback_type: feedbackType,
      });

      setProducts(rankedData.pool || []);
      setCurrentPool(rankedData.pool || []);
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
