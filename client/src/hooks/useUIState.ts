import { useState } from 'react';

export function useUIState() {
  const [panelOpen, setPanelOpen] = useState<boolean>(false);
  const [preferencesOpen, setPreferencesOpen] = useState<boolean>(false);

  const togglePanel = () => setPanelOpen(prev => !prev);
  const closePanel = () => setPanelOpen(false);

  const togglePreferences = () => setPreferencesOpen(prev => !prev);

  return {
    state: {
      panelOpen,
      preferencesOpen,
    },
    actions: {
      togglePanel,
      closePanel,
      togglePreferences,
      setPanelOpen,
      setPreferencesOpen,
    },
  };
}
