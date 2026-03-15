import React, { useState } from 'react';
import './Home.css';

function Home({ onStart }) {
  const [showHow, setShowHow] = useState(false);

  return (
    <div className="home-container">
      {/* Hero */}
      <div className="hero-section">
        <div className="hero-badge">AI-Powered Health Screening</div>
        <h1>🩺 Nutri-Scan</h1>
        <p className="tagline">Non-Invasive Nutritional Deficiency Detection</p>
        <p className="subtitle">
          Scan your face to get a preliminary assessment for Jaundice and Anemia — no lab tests required.
        </p>
        <div className="cta-buttons">
          <button className="btn-primary" onClick={onStart}>
            📸 Start Free Scan
          </button>
          <button
            className="btn-secondary"
            onClick={() => setShowHow(!showHow)}
          >
            {showHow ? '✕ Close' : 'ℹ️ How It Works'}
          </button>
        </div>
      </div>

      {/* How It Works (toggle) */}
      {showHow && (
        <div className="how-it-works">
          <h2>How Nutri-Scan Works</h2>
          <div className="steps">
            <div className="step">
              <div className="step-number">1</div>
              <div>
                <h4>📸 Face Scan</h4>
                <p>
                  Take a selfie or upload a photo. Our AI analyzes your eyes,
                  lips, and skin tone for visual biomarkers.
                </p>
              </div>
            </div>
            <div className="step">
              <div className="step-number">2</div>
              <div>
                <h4>🤖 Smart Questionnaire</h4>
                <p>
                  Answer a few targeted questions about your symptoms and
                  lifestyle to validate and refine the visual findings.
                </p>
              </div>
            </div>
            <div className="step">
              <div className="step-number">3</div>
              <div>
                <h4>🎯 Risk Assessment</h4>
                <p>
                  Receive a GREEN / YELLOW / RED risk level with personalized
                  dietary and lifestyle recommendations.
                </p>
              </div>
            </div>
            <div className="step">
              <div className="step-number">4</div>
              <div>
                <h4>📄 Download Report</h4>
                <p>
                  Download a detailed PDF health summary to share with your
                  doctor or keep for your records.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Feature Cards */}
      <div className="features">
        <div className="feature-card">
          <span className="feature-icon">🟡</span>
          <h3>Jaundice</h3>
          <p>
            Checks for yellow scleral discoloration linked to liver dysfunction
          </p>
        </div>



        <div className="feature-card">
          <span className="feature-icon">🩸</span>
          <h3>Anemia</h3>
          <p>
            Detects pale lips and under-eye dark circles linked to low iron and poor oxygenation
          </p>
        </div>
      </div>

      {/* Disclaimer */}
      <div className="disclaimer">
        <p>
          ⚠️ <strong>Medical Disclaimer:</strong> Nutri-Scan is a preliminary
          screening tool and does not provide medical diagnoses. Always consult
          a qualified healthcare professional for medical advice, diagnosis,
          or treatment.
        </p>
      </div>
    </div>
  );
}

export default Home;