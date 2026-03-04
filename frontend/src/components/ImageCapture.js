import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import './ImageCapture.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

function ImageCapture({ onBack, onScanComplete }) {
  const [selectedImage, setSelectedImage] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const [showWebcam, setShowWebcam] = useState(false);
  const [stream, setStream] = useState(null);
  const [isMobile, setIsMobile] = useState(false);

  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  useEffect(() => {
    // Detect mobile device
    setIsMobile(/Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent));
    return () => {
      if (stream) stream.getTracks().forEach(t => t.stop());
    };
  }, [stream]);

  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedImage(file);
      setPreviewUrl(URL.createObjectURL(file));
      setError(null);
      setShowWebcam(false);
    }
  };

  const handleCameraCapture = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedImage(file);
      setPreviewUrl(URL.createObjectURL(file));
      setError(null);
      setShowWebcam(false);
    }
  };

  const startWebcam = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 1280 }, height: { ideal: 720 }, facingMode: 'user' }
      });
      setStream(mediaStream);
      setShowWebcam(true);
      setError(null);
      setTimeout(() => {
        if (videoRef.current) videoRef.current.srcObject = mediaStream;
      }, 100);
    } catch (err) {
      setError('Could not access camera. Please allow camera permission or use file upload.');
    }
  };

  const captureFromWebcam = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (video && canvas) {
      const ctx = canvas.getContext('2d');
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      ctx.drawImage(video, 0, 0);
      canvas.toBlob((blob) => {
        const file = new File([blob], 'webcam-capture.jpg', { type: 'image/jpeg' });
        setSelectedImage(file);
        setPreviewUrl(URL.createObjectURL(file));
        stopWebcam();
      }, 'image/jpeg', 0.95);
    }
  };

  const stopWebcam = () => {
    if (stream) {
      stream.getTracks().forEach(t => t.stop());
      setStream(null);
    }
    setShowWebcam(false);
  };

  const handleReset = () => {
    setSelectedImage(null);
    setPreviewUrl(null);
    setError(null);
    setShowWebcam(false);
    if (stream) { stream.getTracks().forEach(t => t.stop()); setStream(null); }
    if (fileInputRef.current) fileInputRef.current.value = '';
    if (cameraInputRef.current) cameraInputRef.current.value = '';
  };

  const handleUpload = async () => {
    if (!selectedImage) { setError('Please select or capture an image first'); return; }

    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('image', selectedImage);

    try {
      const response = await axios.post(`${API_URL}/api/upload/`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      // Pass full session data (including chatbot_questions) to parent
      onScanComplete(response.data);
    } catch (err) {
      const msg = err.response?.data?.error || 'Upload failed. Check your connection and try again.';
      setError(msg);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="capture-container">
      <div className="capture-card">
        <button onClick={onBack} className="btn-back">← Back</button>

        <div className="capture-header">
          <h2>📸 Face Scan</h2>
          <p className="instruction">Take a clear selfie or upload a face photo for analysis</p>
        </div>

        {/* Webcam View */}
        {showWebcam && (
          <div className="webcam-section">
            <video ref={videoRef} autoPlay playsInline className="webcam-video" />
            <canvas ref={canvasRef} style={{ display: 'none' }} />
            <div className="webcam-controls">
              <button onClick={captureFromWebcam} className="btn-capture">📸 Capture</button>
              <button onClick={stopWebcam} className="btn-cancel">✕ Cancel</button>
            </div>
          </div>
        )}

        {/* Image Preview */}
        {previewUrl && !showWebcam && (
          <div className="preview-section">
            <img src={previewUrl} alt="Preview" className="preview-image" />
            <button onClick={handleReset} className="btn-reset">✕ Remove</button>
          </div>
        )}

        {/* Upload Options */}
        {!previewUrl && !showWebcam && (
          <>
            <div className="upload-options">
              {/* Mobile: direct camera button */}
              {isMobile ? (
                <div className="upload-option">
                  <input
                    type="file" accept="image/*" capture="user"
                    ref={cameraInputRef} onChange={handleCameraCapture}
                    style={{ display: 'none' }} id="camera-input"
                  />
                  <label htmlFor="camera-input" className="btn-camera option-btn">
                    <span className="btn-icon">📷</span>
                    <span>Take Selfie</span>
                  </label>
                </div>
              ) : (
                /* Desktop: webcam button */
                <div className="upload-option">
                  <button onClick={startWebcam} className="btn-webcam option-btn">
                    <span className="btn-icon">📹</span>
                    <span>Use Webcam</span>
                  </button>
                </div>
              )}

              <div className="upload-option">
                <input
                  type="file" accept="image/*" ref={fileInputRef}
                  onChange={handleFileSelect} style={{ display: 'none' }} id="file-input"
                />
                <label htmlFor="file-input" className="btn-upload option-btn">
                  <span className="btn-icon">📁</span>
                  <span>Upload Photo</span>
                </label>
              </div>
            </div>

            <div className="guidelines">
              <h4>📋 For Best Results:</h4>
              <ul>
                <li>✓ Good natural lighting</li>
                <li>✓ Face centered &amp; clearly visible</li>
                <li>✓ Remove glasses if possible</li>
                <li>✓ Neutral expression, front-facing</li>
              </ul>
            </div>
          </>
        )}

        {/* Analyze Button */}
        {previewUrl && !showWebcam && (
          <button onClick={handleUpload} disabled={uploading} className="btn-analyze">
            {uploading ? (
              <><span className="spinner" /> Analyzing...</>
            ) : (
              '🔍 Analyze Image'
            )}
          </button>
        )}

        {/* Error */}
        {error && <div className="error-message">⚠️ {error}</div>}
      </div>
    </div>
  );
}

export default ImageCapture;