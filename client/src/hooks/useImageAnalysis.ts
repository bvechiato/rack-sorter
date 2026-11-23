import { useState } from 'react';
import { analyzeFile } from '../api';

export function useImageAnalysis() {
  const [confirmedKeyword, setConfirmedKeyword] = useState<string>('');
  const [suggestedKeywords, setSuggestedKeywords] = useState<any[]>([]);
  const [showSuggestions, setShowSuggestions] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(false);
  const [suggestedColours, setSuggestedColours] = useState<any[]>([]);
  const [suggestedCategory, setSuggestedCategory] = useState<any>(null);
  const [uploadId, setUploadId] = useState<any>(null);

  const handleImageUpload = async (file: File | null) => {
    if (!file) return;

    // A new upload starts a new session; stale suggestions must not linger, and the
    // panel-open effect needs a fresh false -> true edge to reopen a closed panel.
    setShowSuggestions(false);
    setLoading(true);
    try {
      const data = await analyzeFile(file);
      const analysis = data.analysis;
      setUploadId(data.upload_id);
      setConfirmedKeyword(analysis.archetype);

      // The archetype is also the first classified tag; duplicates would render twice.
      const rawKeywords = [...new Set(analysis.classified_tags || [])];
      setSuggestedKeywords(rawKeywords);
      setShowSuggestions(true);
      setSuggestedColours([
        ...new Set([analysis.colour_archetype, ...(analysis.colour_classified_tags || [])]),
      ]);
      setSuggestedCategory(analysis.category_archetype);
    } catch {
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
