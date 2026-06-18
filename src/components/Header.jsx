import React from 'react';

function Header() {
  return (
    <header>
      <h1>RackSorter //</h1>
      <div style={{
        fontSize: '11px',
        color: 'var(--accent)',
        fontWeight: 800,
        background: 'var(--accent-dim)',
        padding: '4px 10px',
        borderRadius: '20px',
        letterSpacing: '0.5px'
      }}>
        SANDBOX ACTIVE
      </div>
    </header>
  );
}

export default Header;
