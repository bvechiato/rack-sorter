import { useState } from 'react';
import { analyzeFile } from '../api';

export function useImageAnalysis() {
  const [confirmedKeyword, setConfirmedKeyword] = useState('');
  const [suggestedKeywords, setSuggestedKeywords] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [suggestedTags, setSuggestedTags] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleImageUpload = async (file) => {
    if (!file) return;

    setLoading(true);
    try {
      const data = await analyzeFile(file);
      setConfirmedKeyword(data.archetype);

      // Build unique keywords (filter out color-related ones)
      const rawKeywords = [data.archetype, ...(data.suggested_tags || [])];
      const uniqueKeywords = [...new Set(rawKeywords.filter(k => k && !k.includes('color')))];
      setSuggestedKeywords(uniqueKeywords);
      setShowSuggestions(true);

      // Store tags for weight sliders
      setSuggestedTags(data.suggested_tags || []);
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
      loading,
    },
    actions: {
      setConfirmedKeyword,
      handleImageUpload,
      selectKeyword,
    },
  };
}
