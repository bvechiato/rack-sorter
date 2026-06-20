import React from 'react';

type Props = {
  keywords: string[];
  onSelectKeyword: (k: string) => void;
};

const KeywordSuggestions: React.FC<Props> = ({ keywords, onSelectKeyword }) => {
  const [selected, setSelected] = React.useState<string | undefined>(keywords[0]);

  const handleSelect = (keyword: string) => {
    setSelected(keyword);
    onSelectKeyword(keyword);
  };

  return (
    <div style={{ marginBottom: '16px' }}>
      <label>Or try one of these</label>
      <div className="condition-chips">
        {keywords.map((keyword, index) => (
          <div
            key={index}
            className={`chip ${selected === keyword ? 'selected' : ''}`}
            onClick={() => handleSelect(keyword)}
          >
            {keyword}
          </div>
        ))}
      </div>
    </div>
  );
}

export default KeywordSuggestions;
