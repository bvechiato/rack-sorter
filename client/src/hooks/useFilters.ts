import { useState, useEffect, useRef } from 'react';

export function useFilters() {
  const [selectedSizes, setSelectedSizes] = useState<any[]>([]);
  const [maxPrice, setMaxPrice] = useState<string>('');
  const [selectedCategory, setSelectedCategoryState] = useState<string>('See all');
  const [selectedColors, setSelectedColorsState] = useState<any[]>([]);
  const [selectedConditions, setSelectedConditions] = useState<any[]>([]);
  // Analysis suggestions are only defaults: once the user picks a category or colour,
  // later analysis results must not replace that choice for the rest of the session.
  // Refs so a seed called in the same batch as a user action sees the touch immediately.
  const categoryTouched = useRef(false);
  const coloursTouched = useRef(false);

  // Load from localStorage on mount
  useEffect(() => {
    const savedSizes = localStorage.getItem('rs_size_id');
    const savedPrice = localStorage.getItem('rs_max_price');
    const savedConditions = localStorage.getItem('rs_condition_id');

    if (savedSizes) setSelectedSizes(JSON.parse(savedSizes));
    if (savedPrice) setMaxPrice(savedPrice);
    if (savedConditions) setSelectedConditions(JSON.parse(savedConditions));
  }, []);

  // Save sizes to localStorage
  useEffect(() => {
    localStorage.setItem('rs_size_id', JSON.stringify(selectedSizes));
  }, [selectedSizes]);

  // Save price to localStorage
  useEffect(() => {
    localStorage.setItem('rs_max_price', maxPrice);
  }, [maxPrice]);

  // Save conditions to localStorage
  useEffect(() => {
    localStorage.setItem('rs_condition_id', JSON.stringify(selectedConditions));
  }, [selectedConditions]);

  const toggleSize = (size: any) => {
    if (size === "See all") {
      setSelectedSizes([]);
      return;
    }
    if (selectedSizes.includes(size)) {
      setSelectedSizes(prev => prev.filter((s: any) => s !== size));
      console.log(`[INFO] Removed size: ${size}`);
    } else {
      setSelectedSizes(prev => [...prev, size]);
      console.log(`[INFO] Added size: ${size}`);
    }
  };

  const toggleCondition = (condition: any) => {
    if (selectedConditions.includes(condition)) {
      setSelectedConditions(prev => prev.filter((c: any) => c !== condition));
      console.log(`[INFO] Removed condition: ${condition}`);
    } else {
      setSelectedConditions(prev => [...prev, condition]);
      console.log(`[INFO] Added condition: ${condition}`);
    }
  };

  const toggleColour = (colour: any) => {
    coloursTouched.current = true;
    if (colour === "None") {
      setSelectedColorsState([]);
      return;
    }

    if (selectedColors.includes(colour)) {
      setSelectedColorsState(prev => prev.filter((c: any) => c !== colour));
      console.log(`[INFO] Removed colour: ${colour}`);
    } else {
      setSelectedColorsState(prev => [...prev, colour]);
      console.log(`[INFO] Added colour: ${colour}`);
    }
  };

  const setSelectedCategory = (value: string) => {
    categoryTouched.current = true;
    setSelectedCategoryState(value);
  };

  const setSelectedColors = (colours: any[]) => {
    coloursTouched.current = true;
    setSelectedColorsState(colours);
  };

  const seedCategory = (value: string | null) => {
    if (!value || categoryTouched.current) return;
    setSelectedCategoryState(value);
  };

  const seedColours = (colours: any[]) => {
    if (coloursTouched.current) return;
    setSelectedColorsState(colours);
  };

  return {
    filters: {
      selectedSizes,
      maxPrice,
      selectedCategory,
      selectedColors,
      selectedConditions,
    },
    actions: {
      setSelectedSizes,
      setMaxPrice,
      setSelectedCategory,
      setSelectedColors,
      setSelectedConditions,
      seedCategory,
      seedColours,
      toggleColour,
      toggleSize,
      toggleCondition,
    },
  };
}
