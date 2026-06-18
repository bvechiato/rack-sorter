import React from 'react';

function KeywordSuggestions({ keywords, onSelectKeyword }) {
  const [selected, setSelected] = React.useState(keywords[0]);

  const handleSelect = (keyword) => {
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
