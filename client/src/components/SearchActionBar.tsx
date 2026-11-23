import React, { useState } from 'react';

type Props = {
  confirmedKeyword: string;
  setConfirmedKeyword: (v: string) => void;
  onImageUpload: (file: File | null) => void;
  analyzing: boolean;
};

const SearchActionBar: React.FC<Props> = ({ confirmedKeyword, setConfirmedKeyword, onImageUpload, analyzing }) => {
  const [backgroundImage, setBackgroundImage] = useState<string | null>(null);

  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0] || null;
    if (file) {
      const reader = new FileReader();
      reader.onloadend = () => {
        setBackgroundImage(String(reader.result));
      };
      reader.readAsDataURL(file);
      onImageUpload(file);
    }
  };

  return (
    <div>
      <label>Upload image or generic search keyword</label>
      <div className="search-action-bar">
        <div 
          className="upload-zone-btn" 
          style= {{
            backgroundImage: backgroundImage ? `url(${backgroundImage})` : 'none',
            backgroundSize: 'cover',
            backgroundPosition: 'center'
          }}
        >
          { backgroundImage ? <span style={{ fontSize: '18px' }}>↩️</span> 
                  : <span style={{ fontSize: '18px' }}>📸</span> }
          <input
            type="file"
            accept="image/*"
            disabled={analyzing}
            onChange={handleImageUpload}
          />
        </div>
        <div className="keyword-wrapper">
          <input
            type="text"
            value={confirmedKeyword}
            onChange={(e) => setConfirmedKeyword(e.target.value)}
            placeholder="striped"
          />
        </div>
      </div>
      {analyzing && (
        <p className="analysis-progress" role="status" aria-live="polite">
          <span className="loading-spinner" aria-hidden="true" />
          Analyzing image… this can take a few seconds.
        </p>
      )}
    </div>
  );
}

export default SearchActionBar;
