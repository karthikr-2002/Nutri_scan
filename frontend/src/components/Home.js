import React, { useState } from 'react';
import ImageCapture from './ImageCapture';
import './Home.css';

function Home() {
  const [showCapture, setShowCapture] = useState(false);

  if (showCapture) {
  return <ImageCapture onBack={() => setShowCapture(false)} />;
}

  return (
    <div className="home-container">
      <div className="hero-section">
        <h1>🩺 Nutri-Scan</h1>
        <p className="tagline">AI-Powered Nutritional Health Screening</p>
        <p className="subtitle">
          Non-invasive preliminary assessment for nutritional deficiencies
        </p>
        
        <div className="cta-buttons">
          <button className="btn-primary" onClick={() => setShowCapture(true)}>
            📸 Start Scan
          </button>
          <button className="btn-secondary">
            ℹ️ How It Works
          </button>
        </div>
      </div>

      {/* Rest of the component stays the same */}
      <div className="features">
        <div className="feature-card">
          <span className="feature-icon">🩸</span>
          <h3>Anemia Detection</h3>
          <p>Analyze pallor indicators</p>
        </div>
        
        <div className="feature-card">
          <span className="feature-icon">🟡</span>
          <h3>Jaundice Screening</h3>
          <p>Check for yellow discoloration</p>
        </div>
        
        <div className="feature-card">
          <span className="feature-icon">💧</span>
          <h3>Dehydration Check</h3>
          <p>Assess hydration status</p>
        </div>
        
        <div className="feature-card">
          <span className="feature-icon">🍊</span>
          <h3>Vitamin Deficiency</h3>
          <p>Identify deficiency signs</p>
        </div>
      </div>

      <div className="disclaimer">
        <p>
          ⚠️ <strong>Disclaimer:</strong> This is a preliminary screening tool, 
          not a medical diagnosis. Always consult healthcare professionals 
          for medical advice.
        </p>
      </div>
    </div>
  );
}

export default Home;