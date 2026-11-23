import React from 'react';

type Props = {
  keywords: string[];
  confirmedKeyword: string;
  onSelectKeyword: (k: string) => void;
};

const KeywordSuggestions: React.FC<Props> = ({ keywords, confirmedKeyword, onSelectKeyword }) => {
  return (
    <div style={{ marginBottom: '16px' }}>
      <label>Or try one of these</label>
      <div className="condition-chips">
        {keywords.map((keyword) => (
          <div
            key={keyword}
            className={`chip ${confirmedKeyword === keyword ? 'selected' : ''}`}
            onClick={() => onSelectKeyword(keyword)}
          >
            {keyword}
          </div>
        ))}
      </div>
    </div>
  );
}

export default KeywordSuggestions;
