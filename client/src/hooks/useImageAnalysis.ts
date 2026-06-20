import { useState } from 'react';
import { analyzeFile } from '../api';

export function useImageAnalysis() {
  const [confirmedKeyword, setConfirmedKeyword] = useState<string>('');
  const [suggestedKeywords, setSuggestedKeywords] = useState<any[]>([]);
  const [showSuggestions, setShowSuggestions] = useState<boolean>(false);
  const [suggestedTags, setSuggestedTags] = useState<any[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [suggestedColours, setSuggestedColours] = useState<any[]>([]);
  const [suggestedCategory, setSuggestedCategory] = useState<any>(null);
  const [uploadId, setUploadId] = useState<any>(null);

  const handleImageUpload = async (file: File | null) => {
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

  const selectKeyword = (keyword: string) => {
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
