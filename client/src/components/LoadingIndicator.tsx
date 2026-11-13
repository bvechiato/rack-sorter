import React from 'react';

const LoadingIndicator: React.FC = () => {
  return (
    <div className="loading loading--scrape" role="status" aria-live="polite">
      <span className="loading-spinner" aria-hidden="true" />
      <span className="loading-text">Scraping and ranking listings…</span>
      <span className="loading-sub">This can take a few seconds while we fetch and embed candidates.</span>
    </div>
  );
};

export default LoadingIndicator;
