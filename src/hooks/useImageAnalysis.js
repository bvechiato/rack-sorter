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
  const [uploadId, setUploadId] = useState(null);

  const handleImageUpload = async (file) => {
    if (!file) return;

    setLoading(true);
    try {
      const data = await analyzeFile(file);
      const analysis = data.analysis;
      setUploadId(data.upload_id);
      setConfirmedKeyword(analysis.archetype);

      // Build unique keywords (filter out color-related ones)
      const rawKeywords = [...(analysis.classified_tags || [])];
      setSuggestedKeywords(rawKeywords);
      setShowSuggestions(true);
      setSuggestedColours([analysis.colour_archetype, ...(analysis.colour_classified_tags || [])]);
      setSuggestedCategory(analysis.category_archetype);

      // Store tags for weight sliders
      setSuggestedTags(analysis.classified_tags || []);
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
      uploadId,
    },
    actions: {
      setConfirmedKeyword,
      handleImageUpload,
      selectKeyword,
    },
  };
}
