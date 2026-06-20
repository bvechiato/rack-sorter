import { useState, useEffect } from 'react';

export function useFilters() {
  const [selectedSizes, setSelectedSizes] = useState([]);
  const [maxPrice, setMaxPrice] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('See all');
  const [selectedColors, setSelectedColors] = useState([]);
  const [selectedConditions, setSelectedConditions] = useState([]);

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

  const toggleSize = (size) => {
    if (size === "See all") {
      setSelectedSizes([]);
      return;
    } 
    if (selectedSizes.includes(size)) {
      setSelectedSizes(prev => prev.filter(s => s !== size));
      console.log(`[INFO] Removed size: ${size}`);
    } else {
      setSelectedSizes(prev => [...prev, size]);
      console.log(`[INFO] Added size: ${size}`);
    }
  };

  const toggleCondition = (condition) => {
    if (selectedConditions.includes(condition)) {
      setSelectedConditions(prev => prev.filter(c => c !== condition));
      console.log(`[INFO] Removed condition: ${condition}`);
    } else {
      setSelectedConditions(prev => [...prev, condition]);
      console.log(`[INFO] Added condition: ${condition}`);
    }
  };

  const toggleColour = (colour) => {
    if (colour === "None") {
      setSelectedColors([]);
      return;
    }

    if (selectedColors.includes(colour)) {
      setSelectedColors(prev => prev.filter(c => c !== colour));
      console.log(`[INFO] Removed colour: ${colour}`);
    } else {
      setSelectedColors(prev => [...prev, colour]);
      console.log(`[INFO] Added colour: ${colour}`);
    }
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
      toggleColour,
      toggleSize,
      toggleCondition,
    },
  };
}
