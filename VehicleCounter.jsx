import React, { useState, useRef, useEffect } from 'react';
import { Upload, Play, Pause, Volume2, BarChart3, Download, Settings, Clock, Truck, AlertCircle } from 'lucide-react';
import './VehicleCounter.css';

const VehicleCounterApp = () => {
  // State management
  const [jobId, setJobId] = useState(null);
  const [videoFile, setVideoFile] = useState(null);
  const [uploadedFileName, setUploadedFileName] = useState('');
  const [processingStatus, setProcessingStatus] = useState('idle');
  const [speedFactor, setSpeedFactor] = useState(1.0);
  const [results, setResults] = useState(null);
  const [progress, setProgress] = useState(0);
  const [videoInfo, setVideoInfo] = useState(null);
  const [activeTab, setActiveTab] = useState('upload');
  const [showChart, setShowChart] = useState(false);
  const fileInputRef = useRef(null);
  const progressIntervalRef = useRef(null);

  // API base URL
  const API_BASE = 'http://localhost:8000';

  // Handle file selection
  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      setVideoFile(file);
      setUploadedFileName(file.name);
      setActiveTab('preview');
    }
  };

  // Upload video
  const handleUpload = async () => {
    if (!videoFile) {
      alert('Please select a video file');
      return;
    }

    try {
      setProcessingStatus('uploading');
      const formData = new FormData();
      formData.append('file', videoFile);

      const response = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) throw new Error('Upload failed');

      const data = await response.json();
      setJobId(data.job_id);
      setVideoInfo(data.video_info);
      setProcessingStatus('uploaded');
      setActiveTab('process');
    } catch (error) {
      console.error('Upload error:', error);
      alert(`Upload failed: ${error.message}`);
      setProcessingStatus('idle');
    }
  };

  // Start processing
  const handleProcess = async () => {
    if (!jobId) return;

    try {
      setProcessingStatus('processing');
      setProgress(0);

      const response = await fetch(`${API_BASE}/process/${jobId}?speed_factor=${speedFactor}`, {
        method: 'POST',
      });

      if (!response.ok) throw new Error('Processing failed');

      // Poll for status
      pollProcessingStatus();
    } catch (error) {
      console.error('Processing error:', error);
      alert(`Processing failed: ${error.message}`);
      setProcessingStatus('uploaded');
    }
  };

  // Poll processing status
  const pollProcessingStatus = () => {
    progressIntervalRef.current = setInterval(async () => {
      try {
        const statusResponse = await fetch(`${API_BASE}/status/${jobId}`);
        const statusData = await statusResponse.json();

        if (statusData.status === 'completed') {
          clearInterval(progressIntervalRef.current);
          setProcessingStatus('completed');
          setProgress(100);
          fetchResults();
        } else if (statusData.status === 'failed') {
          clearInterval(progressIntervalRef.current);
          setProcessingStatus('failed');
          alert('Processing failed');
        }
      } catch (error) {
        console.error('Status check error:', error);
      }
    }, 1000);
  };

  // Fetch results
  const fetchResults = async () => {
    try {
      const response = await fetch(`${API_BASE}/results/${jobId}`);
      if (!response.ok) throw new Error('Failed to fetch results');

      const data = await response.json();
      setResults(data.result);
      setActiveTab('results');
    } catch (error) {
      console.error('Fetch results error:', error);
    }
  };

  // Export results
  const handleExport = async (format) => {
    try {
      const response = await fetch(`${API_BASE}/export/${jobId}?format=${format}`);
      if (!response.ok) throw new Error('Export failed');

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `vehicle_count_report.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Export error:', error);
      alert(`Export failed: ${error.message}`);
    }
  };

  // Reset app
  const handleReset = () => {
    setJobId(null);
    setVideoFile(null);
    setUploadedFileName('');
    setProcessingStatus('idle');
    setSpeedFactor(1.0);
    setResults(null);
    setProgress(0);
    setVideoInfo(null);
    setActiveTab('upload');
  };

  return (
    <div className="vehicle-counter-app">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <div className="app-logo">
            <Truck className="logo-icon" />
            <div>
              <h1>Vehicle Counter</h1>
              <p>Automatic Detection & Analysis</p>
            </div>
          </div>
          <div className="header-info">
            <span className="status-badge" data-status={processingStatus}>
              {processingStatus.toUpperCase()}
            </span>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <div className="app-container">
        {/* Sidebar Navigation */}
        <nav className="sidebar">
          <div className="nav-section">
            <button
              className={`nav-item ${activeTab === 'upload' ? 'active' : ''}`}
              onClick={() => setActiveTab('upload')}
            >
              <Upload size={20} />
              <span>Upload</span>
            </button>
            <button
              className={`nav-item ${activeTab === 'preview' ? 'active' : ''}`}
              onClick={() => activeTab !== 'upload' && setActiveTab('preview')}
              disabled={!videoFile}
            >
              <Play size={20} />
              <span>Preview</span>
            </button>
            <button
              className={`nav-item ${activeTab === 'process' ? 'active' : ''}`}
              onClick={() => jobId && setActiveTab('process')}
              disabled={!jobId}
            >
              <Settings size={20} />
              <span>Process</span>
            </button>
            <button
              className={`nav-item ${activeTab === 'results' ? 'active' : ''}`}
              onClick={() => results && setActiveTab('results')}
              disabled={!results}
            >
              <BarChart3 size={20} />
              <span>Results</span>
            </button>
          </div>
          {jobId && (
            <div className="job-info">
              <p className="job-label">Job ID</p>
              <p className="job-id">{jobId}</p>
            </div>
          )}
        </nav>

        {/* Content Area */}
        <main className="app-content">
          {/* Upload Tab */}
          {activeTab === 'upload' && (
            <section className="tab-content upload-section">
              <div className="upload-area">
                <div
                  className="drop-zone"
                  onDragOver={(e) => e.preventDefault()}
                  onDrop={(e) => {
                    e.preventDefault();
                    const files = e.dataTransfer.files;
                    if (files.length > 0) {
                      setVideoFile(files[0]);
                      setUploadedFileName(files[0].name);
                    }
                  }}
                >
                  <Upload size={48} className="drop-icon" />
                  <h2>Upload Your Video</h2>
                  <p>Drag and drop your video file here</p>
                  <p className="supported-formats">Supported: MP4, AVI, MOV, MKV</p>
                  <button
                    className="btn btn-primary"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    Browse Files
                  </button>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="video/*"
                    onChange={handleFileSelect}
                    style={{ display: 'none' }}
                  />
                </div>

                {videoFile && (
                  <div className="file-preview">
                    <div className="file-info">
                      <div className="file-icon">🎬</div>
                      <div className="file-details">
                        <p className="file-name">{uploadedFileName}</p>
                        <p className="file-size">{(videoFile.size / 1024 / 1024).toFixed(2)} MB</p>
                      </div>
                    </div>
                    <button
                      className="btn btn-success btn-large"
                      onClick={handleUpload}
                      disabled={processingStatus === 'uploading'}
                    >
                      {processingStatus === 'uploading' ? 'Uploading...' : 'Upload & Continue'}
                    </button>
                  </div>
                )}
              </div>
            </section>
          )}

          {/* Preview Tab */}
          {activeTab === 'preview' && videoFile && (
            <section className="tab-content preview-section">
              <div className="preview-container">
                <video
                  src={URL.createObjectURL(videoFile)}
                  controls
                  className="video-preview"
                />
                <div className="preview-info">
                  <h3>File Information</h3>
                  <div className="info-grid">
                    <div className="info-item">
                      <span className="label">Filename</span>
                      <span className="value">{uploadedFileName}</span>
                    </div>
                    <div className="info-item">
                      <span className="label">File Size</span>
                      <span className="value">{(videoFile.size / 1024 / 1024).toFixed(2)} MB</span>
                    </div>
                  </div>
                </div>
              </div>
            </section>
          )}

          {/* Process Tab */}
          {activeTab === 'process' && videoInfo && (
            <section className="tab-content process-section">
              <div className="process-container">
                <div className="video-details">
                  <h2>Video Details</h2>
                  <div className="details-grid">
                    <div className="detail-card">
                      <Clock size={24} />
                      <div>
                        <p className="detail-label">Duration</p>
                        <p className="detail-value">{videoInfo.duration.toFixed(1)}s</p>
                      </div>
                    </div>
                    <div className="detail-card">
                      <span className="icon">📊</span>
                      <div>
                        <p className="detail-label">Frames</p>
                        <p className="detail-value">{videoInfo.frames.toLocaleString()}</p>
                      </div>
                    </div>
                    <div className="detail-card">
                      <span className="icon">⚡</span>
                      <div>
                        <p className="detail-label">FPS</p>
                        <p className="detail-value">{videoInfo.fps.toFixed(1)}</p>
                      </div>
                    </div>
                    <div className="detail-card">
                      <span className="icon">📐</span>
                      <div>
                        <p className="detail-label">Resolution</p>
                        <p className="detail-value">{videoInfo.width}x{videoInfo.height}</p>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="settings-panel">
                  <h2>Processing Settings</h2>
                  <div className="setting-group">
                    <label>Playback Speed (10x = 10 times faster)</label>
                    <div className="speed-control">
                      <input
                        type="range"
                        min="1"
                        max="10"
                        value={speedFactor}
                        onChange={(e) => setSpeedFactor(parseFloat(e.target.value))}
                        className="speed-slider"
                      />
                      <span className="speed-value">{speedFactor.toFixed(1)}x</span>
                    </div>
                  </div>

                  {processingStatus === 'uploaded' && (
                    <button
                      className="btn btn-success btn-large"
                      onClick={handleProcess}
                    >
                      Start Detection
                    </button>
                  )}

                  {processingStatus === 'processing' && (
                    <div className="processing-indicator">
                      <div className="spinner"></div>
                      <p>Processing video...</p>
                      <div className="progress-bar">
                        <div
                          className="progress-fill"
                          style={{ width: `${progress}%` }}
                        ></div>
                      </div>
                      <p className="progress-text">{progress}%</p>
                    </div>
                  )}

                  {processingStatus === 'completed' && (
                    <div className="success-indicator">
                      <span className="check-icon">✓</span>
                      <p>Processing completed!</p>
                    </div>
                  )}
                </div>
              </div>
            </section>
          )}

          {/* Results Tab */}
          {activeTab === 'results' && results && (
            <section className="tab-content results-section">
              <div className="results-container">
                <div className="summary-cards">
                  <div className="summary-card primary">
                    <div className="summary-icon">🚗</div>
                    <div className="summary-data">
                      <p className="summary-label">Total Vehicles</p>
                      <p className="summary-value">{results.total_vehicles_detected.toLocaleString()}</p>
                    </div>
                  </div>

                  <div className="summary-card">
                    <div className="summary-icon">📹</div>
                    <div className="summary-data">
                      <p className="summary-label">Frames Processed</p>
                      <p className="summary-value">{results.processed_frames.toLocaleString()}</p>
                    </div>
                  </div>

                  <div className="summary-card">
                    <div className="summary-icon">📈</div>
                    <div className="summary-data">
                      <p className="summary-label">Detection Rate</p>
                      <p className="summary-value">
                        {((results.processed_frames / results.total_frames) * 100).toFixed(1)}%
                      </p>
                    </div>
                  </div>
                </div>

                <div className="breakdown-section">
                  <h2>Vehicle Breakdown</h2>
                  <div className="vehicle-types">
                    {Object.entries(results.vehicle_breakdown).map(([type, count]) => (
                      <div key={type} className="vehicle-type-card">
                        <div className="type-name">{type.toUpperCase()}</div>
                        <div className="type-count">{count}</div>
                      </div>
                    ))}
                  </div>
                </div>

                <div className="export-section">
                  <h2>Export Results</h2>
                  <div className="export-buttons">
                    <button
                      className="btn btn-outline"
                      onClick={() => handleExport('csv')}
                    >
                      <Download size={20} />
                      Export as CSV
                    </button>
                    <button
                      className="btn btn-outline"
                      onClick={() => handleExport('json')}
                    >
                      <Download size={20} />
                      Export as JSON
                    </button>
                  </div>
                </div>

                <button
                  className="btn btn-primary"
                  onClick={handleReset}
                >
                  Process New Video
                </button>
              </div>
            </section>
          )}

          {/* Error State */}
          {processingStatus === 'failed' && (
            <section className="tab-content error-section">
              <div className="error-container">
                <AlertCircle size={48} />
                <h2>Processing Failed</h2>
                <p>An error occurred during video processing.</p>
                <button className="btn btn-primary" onClick={handleReset}>
                  Try Again
                </button>
              </div>
            </section>
          )}
        </main>
      </div>
    </div>
  );
};

export default VehicleCounterApp;
