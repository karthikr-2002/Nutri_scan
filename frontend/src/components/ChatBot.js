import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './ChatBot.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function ChatBot({ sessionData, onBack, onComplete }) {
  const [questions, setQuestions] = useState([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [selectedOption, setSelectedOption] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const [visualScores, setVisualScores] = useState({});

  useEffect(() => {
    if (sessionData) {
      const qs = sessionData.chatbot_questions || [];
      setQuestions(qs);
      setVisualScores({
        anemia: sessionData.visual_analysis?.anemia_score || 0,
        jaundice: sessionData.visual_analysis?.jaundice_score || 0,
        dehydration: sessionData.visual_analysis?.dehydration_score || 0,
        vitamin: sessionData.visual_analysis?.vitamin_score || 0,
      });
    }
  }, [sessionData]);

  const currentQ = questions[currentIndex];

  // ✅ FIXED PROGRESS CALCULATION
  const progress =
    questions.length > 0
      ? ((currentIndex + 1) / questions.length) * 100
      : 0;

  const handleOptionSelect = (optionIndex) => {
    setSelectedOption(optionIndex);
  };

  const handleNext = () => {
    if (selectedOption === null) return;

    const newAnswers = { ...answers, [currentQ.id]: selectedOption };
    setAnswers(newAnswers);
    setSelectedOption(null);

    if (currentIndex < questions.length - 1) {
      setCurrentIndex(currentIndex + 1);
    } else {
      handleSubmit(newAnswers);
    }
  };

  const handleSubmit = async (finalAnswers) => {
    setSubmitting(true);
    setError(null);
    try {
      const response = await axios.post(`${API_URL}/api/chatbot/`, {
        session_id: sessionData.session_id,
        answers: finalAnswers,
      });
      onComplete(response.data);
    } catch (err) {
      setError('Could not submit answers. Please try again.');
      setSubmitting(false);
    }
  };

  const conditionBadge = (label, score) => {
    const level = score >= 5 ? 'high' : score >= 3 ? 'moderate' : 'low';
    const icon = score >= 5 ? '🔴' : score >= 3 ? '🟡' : '🟢';
    return (
      <div key={label} className={`score-badge score-${level}`}>
        {icon} {label}: {score}/10
      </div>
    );
  };

  if (submitting) {
    return (
      <div className="chatbot-container">
        <div className="chatbot-card analyzing">
          <div className="analyzing-animation">
            <div className="pulse-ring" />
            <div className="pulse-ring delay1" />
            <div className="pulse-ring delay2" />
            <span className="brain-icon">🧠</span>
          </div>
          <h3>Analyzing your responses...</h3>
          <p>
            Combining visual analysis with your answers to generate your health
            assessment.
          </p>
        </div>
      </div>
    );
  }

  if (questions.length === 0) {
    return (
      <div className="chatbot-container">
        <div className="chatbot-card">
          <p>No questions loaded. Please go back and try again.</p>
          <button onClick={onBack} className="btn-back">
            ← Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="chatbot-container">
      <div className="chatbot-card">
        {/* Header */}
        <div className="chatbot-header">
          <button onClick={onBack} className="btn-back">
            ← Back
          </button>
          <div className="chatbot-title">
            <span className="chatbot-avatar">🤖</span>
            <div>
              <h3>NutriBot</h3>
              <p className="chatbot-subtitle">
                Health Assessment Assistant
              </p>
            </div>
          </div>
        </div>

        {/* Visual Scan Summary */}
        <div className="scan-summary">
          <p className="scan-summary-label">📊 Visual Scan Results</p>
          <div className="scores-row">
            {conditionBadge('Anemia', visualScores.anemia)}
            {conditionBadge('Jaundice', visualScores.jaundice)}
            {conditionBadge('Dehydration', visualScores.dehydration)}
            {conditionBadge('Vitamins', visualScores.vitamin)}
          </div>
        </div>

        {/* Progress Bar */}
        <div className="progress-bar-container">
          <div className="progress-label">
            Question {currentIndex + 1} of {questions.length}
          </div>
          <div className="progress-track">
            <div
              className="progress-fill"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>

        {/* Question Bubble */}
        <div className="question-section">
          {currentQ?.condition && (
            <span className={`condition-tag tag-${currentQ.condition}`}>
              {currentQ.condition.charAt(0).toUpperCase() +
                currentQ.condition.slice(1)}
            </span>
          )}
          <div className="question-bubble">
            <p className="question-text">{currentQ?.question}</p>
          </div>
        </div>

        {/* Answer Options */}
        <div className="options-section">
          {currentQ?.options?.map((option, index) => (
            <button
              key={index}
              className={`option-btn ${
                selectedOption === index ? 'selected' : ''
              }`}
              onClick={() => handleOptionSelect(index)}
            >
              <span className="option-letter">
                {String.fromCharCode(65 + index)}
              </span>
              <span className="option-text">{option}</span>
              {selectedOption === index && (
                <span className="option-check">✓</span>
              )}
            </button>
          ))}
        </div>

        {error && <div className="error-message">⚠️ {error}</div>}

        {/* Next Button */}
        <button
          onClick={handleNext}
          disabled={selectedOption === null}
          className={`btn-next ${
            selectedOption !== null ? 'active' : ''
          }`}
        >
          {currentIndex < questions.length - 1
            ? 'Next →'
            : '🔍 Get Results'}
        </button>
      </div>
    </div>
  );
}

export default ChatBot;