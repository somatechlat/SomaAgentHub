import React from 'react';

const brandColor = '{{BRAND_COLOR}}';

export function App() {
  return (
    <div style={{ fontFamily: 'sans-serif', padding: 24 }}>
      <h1 style={{ color: brandColor }}>Welcome to {{APP_NAME}}</h1>
      <p>Generated UI scaffold. Customize components via the UI-Customizer agent.</p>
    </div>
  );
}

export default App;
