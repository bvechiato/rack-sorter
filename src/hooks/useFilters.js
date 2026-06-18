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
    setSelectedSizes(prev =>
      prev.includes(size) ? prev.filter(s => s !== size) : [...prev, size]
    );
  };

  const toggleCondition = (condition) => {
    setSelectedConditions(prev =>
      prev.includes(condition) ? prev.filter(c => c !== condition) : [...prev, condition]
    );
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
      toggleSize,
      toggleCondition,
    },
  };
}
