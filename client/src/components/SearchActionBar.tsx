import React, { useState } from 'react';

type Props = {
  confirmedKeyword: string;
  setConfirmedKeyword: (v: string) => void;
  onImageUpload: (file: File | null) => void;
};

const SearchActionBar: React.FC<Props> = ({ confirmedKeyword, setConfirmedKeyword, onImageUpload }) => {
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
    </div>
  );
}

export default SearchActionBar;
