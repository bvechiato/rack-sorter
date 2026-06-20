import { useState, useEffect } from 'react';

export function useVectorWeights(suggestedTags: string[]) {
  const [weights, setWeights] = useState<Record<string, number>>({});

  // Initialize weights when tags change
  useEffect(() => {
    const initialWeights: Record<string, number> = {};
    suggestedTags.forEach(tag => {
      initialWeights[tag] = (tag.includes('color') || tag === 'dress') ? 0.0 : 0.8;
    });
    setWeights(initialWeights);
  }, [suggestedTags]);

  const updateWeight = (tag: string, value: string | number) => {
    setWeights(prev => ({
      ...prev,
      [tag]: parseFloat(String(value)),
    }));
  };

  return {
    weights,
    updateWeight,
  };
}
