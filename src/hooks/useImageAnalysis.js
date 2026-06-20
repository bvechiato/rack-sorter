import { useState } from 'react';
import { analyzeFile } from '../api';

export function useImageAnalysis() {
  const [confirmedKeyword, setConfirmedKeyword] = useState('');
  const [suggestedKeywords, setSuggestedKeywords] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [suggestedTags, setSuggestedTags] = useState([]);
  const [loading, setLoading] = useState(false);
  const [suggestedColours, setSuggestedColours] = useState([]);
  const [suggestedCategory, setSuggestedCategory] = useState(null);

  const handleImageUpload = async (file) => {
    if (!file) return;

    setLoading(true);
    try {
      const data = await analyzeFile(file);
      setConfirmedKeyword(data.archetype);

      // Build unique keywords (filter out color-related ones)
      const rawKeywords = [...(data.classified_tags || [])];
      setSuggestedKeywords(rawKeywords);
      setShowSuggestions(true);
      setSuggestedColours([data.colour_archetype, ...(data.colour_classified_tags || [])]);
      setSuggestedCategory(data.category_archetype);

      // Store tags for weight sliders
      setSuggestedTags(data.classified_tags || []);
    } catch (err) {
      throw new Error('Connection failure to local Python host engine');
    } finally {
      setLoading(false);
    }
  };

  const selectKeyword = (keyword) => {
    setConfirmedKeyword(keyword);
  };

  return {
    state: {
      confirmedKeyword,
      suggestedKeywords,
      showSuggestions,
      suggestedTags,
      suggestedColours,
      suggestedCategory,
      loading,
    },
    actions: {
      setConfirmedKeyword,
      handleImageUpload,
      selectKeyword,
    },
  };
}
