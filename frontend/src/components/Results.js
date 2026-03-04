import React, { useState } from 'react';
import axios from 'axios';
import './Results.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const RISK_CONFIG = {
  GREEN: {
    color: '#22c55e',
    bg: '#f0fdf4',
    border: '#86efac',
    emoji: '🟢',
    label: 'Low Risk',
    message: 'Great! No significant nutritional deficiency indicators detected.',
  },
  YELLOW: {
    color: '#f59e0b',
    bg: '#fffbeb',
    border: '#fcd34d',
    emoji: '🟡',
    label: 'Moderate Risk',
    message: 'Some indicators detected. Follow the recommendations below.',
  },
  RED: {
    color: '#ef4444',
    bg: '#fef2f2',
    border: '#fca5a5',
    emoji: '🔴',
    label: 'High Risk',
    message: 'Significant indicators detected. Please consult a healthcare professional.',
  },
};



function ScoreBar({ label, icon, score, maxScore = 10 }) {
  const pct = Math.round((score / maxScore) * 100);
  const color = score >= 5 ? '#ef4444' : score >= 3 ? '#f59e0b' : '#22c55e';
  return (
    <div className="score-bar-item">
      <div className="score-bar-label">
        <span>{icon} {label}</span>
        <span className="score-value" style={{ color }}>{score}/10</span>
      </div>
      <div className="score-bar-track">
        <div
          className="score-bar-fill"
          style={{ width: `${pct}%`, backgroundColor: color }}
        />
      </div>
    </div>
  );
}

function Results({ sessionData, riskData, onNewScan }) {
  const [downloading, setDownloading] = useState(false);
  const [downloadError, setDownloadError] = useState(null);

  const risk = riskData?.risk || {};
  const evaluation = riskData?.evaluation || {};
  const recommendations = riskData?.recommendations || {};
  const combined = evaluation?.combined_scores || {};

  const riskLevel = risk.risk_level || 'GREEN';
  const config = RISK_CONFIG[riskLevel] || RISK_CONFIG.GREEN;

  const handleDownloadReport = async () => {
    setDownloading(true);
    setDownloadError(null);
    try {
      const response = await axios.get(
        `${API_URL}/api/report/${sessionData.session_id}/`,
        { responseType: 'blob' }
      );
      const url = window.URL.createObjectURL(new Blob([response.data]));
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', `nutriscan-report-${sessionData.session_id.slice(0, 8)}.pdf`);
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
    } catch (err) {
      setDownloadError('Failed to generate report. Please try again.');
    } finally {
      setDownloading(false);
    }
  };

  return (
    <div className="results-container">
      <div className="results-card">
        {/* Header */}
        <div className="results-header">
          <h2>🩺 Health Assessment Results</h2>
          <p className="results-subtitle">Based on facial analysis and your symptom responses</p>
        </div>

        {/* Risk Level Banner */}
        <div
          className="risk-banner"
          style={{ backgroundColor: config.bg, borderColor: config.border }}
        >
          <div className="risk-emoji">{config.emoji}</div>
          <div className="risk-content">
            <h3 style={{ color: config.color }}>{config.label}</h3>
            <p>{risk.risk_description || config.message}</p>
            <div className="risk-score">
              Overall Score: <strong style={{ color: config.color }}>{risk.overall_score || 0}/10</strong>
            </div>
          </div>
        </div>

        {/* Detected Conditions */}
        {(risk.detected_conditions || []).length > 0 && (
          <div className="detected-conditions">
            <h4>⚠️ Detected Indicators</h4>
            <div className="condition-tags">
              {risk.detected_conditions.map((c, i) => (
                <span key={i} className="condition-chip">{c}</span>
              ))}
            </div>
          </div>
        )}

        {/* Score Breakdown */}
        <div className="scores-section">
          <h4>📊 Condition Analysis</h4>
          <div className="scores-grid">
            <ScoreBar label="Anemia" icon="🩸" score={combined.anemia || 0} />
            <ScoreBar label="Jaundice" icon="🟡" score={combined.jaundice || 0} />
            <ScoreBar label="Dehydration" icon="💧" score={combined.dehydration || 0} />
            <ScoreBar label="Vitamins" icon="🍊" score={combined.vitamin || 0} />
          </div>
        </div>

        {/* Recommendations */}
        <div className="recommendations-section">
          <h4>💡 Personalized Recommendations</h4>

          {recommendations.dietary?.length > 0 && (
            <div className="rec-group">
              <h5>🥗 Dietary</h5>
              <ul>
                {recommendations.dietary.map((r, i) => <li key={i}>{r}</li>)}
              </ul>
            </div>
          )}

          {recommendations.hydration?.length > 0 && (
            <div className="rec-group">
              <h5>💧 Hydration</h5>
              <ul>
                {recommendations.hydration.map((r, i) => <li key={i}>{r}</li>)}
              </ul>
            </div>
          )}

          {recommendations.lifestyle?.length > 0 && (
            <div className="rec-group">
              <h5>🏃 Lifestyle</h5>
              <ul>
                {recommendations.lifestyle.map((r, i) => <li key={i}>{r}</li>)}
              </ul>
            </div>
          )}

          {recommendations.medical?.length > 0 && (
            <div className={`rec-group ${riskLevel === 'RED' ? 'rec-urgent' : ''}`}>
              <h5>🏥 Medical Advisory</h5>
              <ul>
                {recommendations.medical.map((r, i) => <li key={i}>{r}</li>)}
              </ul>
            </div>
          )}
        </div>

        {/* Disclaimer */}
        <div className="disclaimer-box">
          ⚠️ <strong>Disclaimer:</strong> This is a preliminary screening tool, not a medical diagnosis.
          Always consult a qualified healthcare professional for medical advice.
        </div>

        {/* Action Buttons */}
        <div className="results-actions">
          <button
            onClick={handleDownloadReport}
            disabled={downloading}
            className="btn-download"
          >
            {downloading ? '⏳ Generating...' : '📄 Download PDF Report'}
          </button>
          <button onClick={onNewScan} className="btn-new-scan">
            🔄 New Scan
          </button>
        </div>

        {downloadError && <div className="error-message">⚠️ {downloadError}</div>}
      </div>
    </div>
  );
}

export default Results;
