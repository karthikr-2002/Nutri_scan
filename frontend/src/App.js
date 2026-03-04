import React, { useState } from 'react';
import Home from './components/Home';
import ImageCapture from './components/ImageCapture';
import ChatBot from './components/ChatBot';
import Results from './components/Results';
import './App.css';

// App-level navigation states
// 'home' → 'scan' → 'chatbot' → 'results'
function App() {
  const [page, setPage] = useState('home');
  const [sessionData, setSessionData] = useState(null);
  const [riskData, setRiskData] = useState(null);

  const goHome = () => {
    setPage('home');
    setSessionData(null);
    setRiskData(null);
  };

  const goToScan = () => setPage('scan');

  const goToChatbot = (data) => {
    setSessionData(data);
    setPage('chatbot');
  };

  const goToResults = (data) => {
    setRiskData(data);
    setPage('results');
  };

  return (
    <div className="app">
      {page === 'home' && <Home onStart={goToScan} />}
      {page === 'scan' && (
        <ImageCapture
          onBack={goHome}
          onScanComplete={goToChatbot}
        />
      )}
      {page === 'chatbot' && (
        <ChatBot
          sessionData={sessionData}
          onBack={goHome}
          onComplete={goToResults}
        />
      )}
      {page === 'results' && (
        <Results
          sessionData={sessionData}
          riskData={riskData}
          onNewScan={goHome}
        />
      )}
    </div>
  );
}

export default App;