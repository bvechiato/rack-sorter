import { useState } from 'react';
import { compare } from '../api';

export function useCompareItem() {
  // Key both states by the item's unique image URL string
  const [characteristics, setCharacteristics] = useState<Record<string, string[]>>({});
  const [loadingMap, setLoadingMap] = useState<Record<string, boolean>>({});

  const compareItem = async (uploadId: any, itemUrl: string) => {
    if (!uploadId) {
      throw new Error('Missing upload id');
    }

    // Set loading just for this single asset card
    setLoadingMap(prev => ({ ...prev, [itemUrl]: true }));

    try {
      const res = await compare({
        upload_id: uploadId,
        item_clicked_url: itemUrl
      });

      const tags = res.distinguishing_characteristics || [];
      
      // Store features tied explicitly to this specific image
      setCharacteristics(prev => ({ 
        ...prev, 
        [itemUrl]: tags 
      }));
    } catch (err) {
      throw new Error('Vector calculation error');
    } finally {
      setLoadingMap(prev => ({ ...prev, [itemUrl]: false }));
    }
  };

  return {
    state: {
      characteristics,
      loadingMap // Exposed to show individual loading rings/spinners if needed
    },
    actions: {
      compareItem,
    },
  };
}