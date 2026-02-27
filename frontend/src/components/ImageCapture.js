import React, { useState, useRef, useEffect } from 'react';
import axios from 'axios';
import './ImageCapture.css';

function ImageCapture({ onBack }) {
  const [selectedImage, setSelectedImage] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [showWebcam, setShowWebcam] = useState(false);
  const [stream, setStream] = useState(null);
  
  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);
  const videoRef = useRef(null);
  const canvasRef = useRef(null);

  // Cleanup webcam stream on unmount
  useEffect(() => {
    return () => {
      if (stream) {
        stream.getTracks().forEach(track => track.stop());
      }
    };
  }, [stream]);

  // Handle file selection from gallery
  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedImage(file);
      setPreviewUrl(URL.createObjectURL(file));
      setError(null);
      setResult(null);
      setShowWebcam(false);
    }
  };

  // Handle camera capture (mobile)
  const handleCameraCapture = (event) => {
    const file = event.target.files[0];
    if (file) {
      setSelectedImage(file);
      setPreviewUrl(URL.createObjectURL(file));
      setError(null);
      setResult(null);
      setShowWebcam(false);
    }
  };

  // Start webcam (desktop)
  const startWebcam = async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: 'user' // Front camera
        }
      });
      
      setStream(mediaStream);
      setShowWebcam(true);
      setError(null);
      
      // Wait for video element to be ready
      setTimeout(() => {
        if (videoRef.current) {
          videoRef.current.srcObject = mediaStream;
        }
      }, 100);
      
    } catch (err) {
      console.error('Webcam error:', err);
      setError('Could not access webcam. Please check permissions or use file upload.');
    }
  };

  // Capture photo from webcam
  const captureFromWebcam = () => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    
    if (video && canvas) {
      const context = canvas.getContext('2d');
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      
      // Draw video frame to canvas
      context.drawImage(video, 0, 0);
      
      // Convert canvas to blob
      canvas.toBlob((blob) => {
        const file = new File([blob], 'webcam-capture.jpg', { type: 'image/jpeg' });
        setSelectedImage(file);
        setPreviewUrl(URL.createObjectURL(file));
        
        // Stop webcam
        stopWebcam();
      }, 'image/jpeg', 0.95);
    }
  };

  // Stop webcam
  const stopWebcam = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
    setShowWebcam(false);
  };

  // Upload image to Django API
  const handleUpload = async () => {
    if (!selectedImage) {
      setError('Please select or capture an image first');
      return;
    }

    setUploading(true);
    setError(null);

    const formData = new FormData();
    formData.append('image', selectedImage);

    try {
      const response = await axios.post(
        'http://localhost:8000/api/upload/',
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      setResult(response.data);
      console.log('Upload successful:', response.data);
    } catch (err) {
      setError('Upload failed. Please try again.');
      console.error('Upload error:', err);
    } finally {
      setUploading(false);
    }
  };

  // Reset and start over
  const handleReset = () => {
    setSelectedImage(null);
    setPreviewUrl(null);
    setResult(null);
    setError(null);
    setShowWebcam(false);
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
    if (fileInputRef.current) fileInputRef.current.value = '';
    if (cameraInputRef.current) cameraInputRef.current.value = '';
  };

  return (
    <div className="capture-container">
      <div className="capture-card">
  {/* Back Button */}
  <button onClick={onBack} className="btn-back">
    ← Back to Home
  </button>
  
  <h2>📸 Upload Your Image</h2>
        <p className="instruction">
          Take a selfie or upload a clear photo of your face
        </p>

        {/* Webcam View (Desktop) */}
        {showWebcam && (
          <div className="webcam-section">
            <video
              ref={videoRef}
              autoPlay
              playsInline
              className="webcam-video"
            />
            <canvas ref={canvasRef} style={{ display: 'none' }} />
            <div className="webcam-controls">
              <button onClick={captureFromWebcam} className="btn-capture">
                📸 Capture Photo
              </button>
              <button onClick={stopWebcam} className="btn-cancel">
                ✕ Cancel
              </button>
            </div>
          </div>
        )}

        {/* Image Preview */}
        {previewUrl && !showWebcam && (
          <div className="preview-section">
            <img src={previewUrl} alt="Preview" className="preview-image" />
            <button onClick={handleReset} className="btn-reset">
              ✕ Remove
            </button>
          </div>
        )}

        {/* Upload Options */}
        {!previewUrl && !showWebcam && (
          <div className="upload-options">
            {/* Webcam Capture (Desktop) */}
            <div className="upload-option">
              <button onClick={startWebcam} className="btn-webcam">
                📹 Use Webcam
              </button>
            </div>

            {/* Camera Capture (Mobile) */}
            <div className="upload-option">
              <input
                type="file"
                accept="image/*"
                capture="user"
                ref={cameraInputRef}
                onChange={handleCameraCapture}
                style={{ display: 'none' }}
                id="camera-input"
              />
              <label htmlFor="camera-input" className="btn-camera">
                📷 Take Photo
              </label>
            </div>

            {/* File Upload */}
            <div className="upload-option">
              <input
                type="file"
                accept="image/*"
                ref={fileInputRef}
                onChange={handleFileSelect}
                style={{ display: 'none' }}
                id="file-input"
              />
              <label htmlFor="file-input" className="btn-upload">
                📁 Upload Image
              </label>
            </div>
          </div>
        )}

        {/* Upload Button */}
        {previewUrl && !result && !showWebcam && (
          <button
            onClick={handleUpload}
            disabled={uploading}
            className="btn-analyze"
          >
            {uploading ? '🔄 Uploading...' : '🔍 Analyze Image'}
          </button>
        )}

        {/* Error Message */}
        {error && (
          <div className="error-message">
            ⚠️ {error}
          </div>
        )}

        {/* Success Result */}
        {result && (
          <div className="result-section">
            <h3>✅ Upload Successful!</h3>
            <div className="result-details">
              <p><strong>Session ID:</strong> {result.session_id}</p>
              <p><strong>Created:</strong> {new Date(result.created_at).toLocaleString()}</p>
              <p><strong>Status:</strong> Image uploaded successfully</p>
            </div>
            <div className="next-steps">
              <p className="info-text">
                🎉 Your image has been uploaded! Analysis coming soon...
              </p>
              <button onClick={handleReset} className="btn-new-scan">
                📸 Start New Scan
              </button>
            </div>
          </div>
        )}

        {/* Guidelines */}
        {!previewUrl && !showWebcam && (
          <div className="guidelines">
            <h4>📋 Guidelines for Best Results:</h4>
            <ul>
              <li>✓ Good lighting (natural daylight preferred)</li>
              <li>✓ Face centered and clearly visible</li>
              <li>✓ Remove glasses if possible</li>
              <li>✓ Neutral facial expression</li>
              <li>✓ Front-facing camera (not tilted)</li>
            </ul>
          </div>
        )}
      </div>
    </div>
  );
}

export default ImageCapture;