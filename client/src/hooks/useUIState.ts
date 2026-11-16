import { useState } from 'react';

export function useUIState() {
  const [panelOpen, setPanelOpen] = useState<boolean>(false);
  const [preferencesOpen, setPreferencesOpen] = useState<boolean>(false);
  const [traitSheetUrl, setTraitSheetUrl] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const togglePanel = () => setPanelOpen(prev => !prev);
  const closePanel = () => setPanelOpen(false);

  const togglePreferences = () => setPreferencesOpen(prev => !prev);

  const openTraitSheet = (itemUrl: string) => setTraitSheetUrl(itemUrl);
  const closeTraitSheet = () => setTraitSheetUrl(null);

  const showError = (message: string) => setErrorMessage(message);
  const clearError = () => setErrorMessage(null);

  return {
    state: {
      panelOpen,
      preferencesOpen,
      traitSheetUrl,
      errorMessage,
    },
    actions: {
      togglePanel,
      closePanel,
      togglePreferences,
      setPanelOpen,
      setPreferencesOpen,
      openTraitSheet,
      closeTraitSheet,
      showError,
      clearError,
    },
  };
}
