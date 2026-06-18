import { useState, useEffect } from 'react';

export function useVectorWeights(suggestedTags) {
  const [weights, setWeights] = useState({});

  // Initialize weights when tags change
  useEffect(() => {
    const initialWeights = {};
    suggestedTags.forEach(tag => {
      initialWeights[tag] = (tag.includes('color') || tag === 'dress') ? 0.0 : 0.8;
    });
    setWeights(initialWeights);
  }, [suggestedTags]);

  const updateWeight = (tag, value) => {
    setWeights(prev => ({
      ...prev,
      [tag]: parseFloat(value),
    }));
  };

  return {
    weights,
    updateWeight,
  };
}
