import React, { useState, useRef, useEffect } from 'react';
import { Upload, Play, Pause, Volume2, BarChart3, Download, Settings, Clock, Truck, AlertCircle, LineChart as LineChartIcon, TrendingUp, Calendar, Activity, Database } from 'lucide-react';
import './VehicleCounterAdvanced.css';

const VehicleCounterAdvancedApp = () => {
  // State management
  const [jobId, setJobId] = useState(null);
  const [videoFile, setVideoFile] = useState(null);
  const [uploadedFileName, setUploadedFileName] = useState('');
  const [processingStatus, setProcessingStatus] = useState('idle');
  const [speedFactor, setSpeedFactor] = useState(1.0);
  const [results, setResults] = useState(null);
  const [analytics, setAnalytics] = useState(null);
  const [progress, setProgress] = useState(0);
  const [videoInfo, setVideoInfo] = useState(null);
  const [activeTab, setActiveTab] = useState('upload');
  const [jobHistory, setJobHistory] = useState([]);
  const [batchQueue, setBatchQueue] = useState([]);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const fileInputRef = useRef(null);
  const progressIntervalRef = useRef(null);

  const API_BASE = 'http://localhost:8000';

  // Fetch job history
  const fetchJobHistory = async () => {
    try {
      const response = await fetch(`${API_BASE}/history`);
      const data = await response.json();
      setJobHistory(data.jobs || []);
    } catch (error) {
      console.error('History fetch error:', error);
    }
  };

  // Fetch queue status
  const fetchQueueStatus = async () => {
    try {
      const response = await fetch(`${API_BASE}/queue/status`);
      const data = await response.json();
      setBatchQueue(data);
    } catch (error) {
      console.error('Queue fetch error:', error);
    }
  };

  // Fetch analytics
  const fetchAnalytics = async (jId) => {
    try {
      const response = await fetch(`${API_BASE}/analytics/${jId}`);
      if (response.ok) {
        const data = await response.json();
        setAnalytics(data.analytics);
      }
    } catch (error) {
      console.error('Analytics fetch error:', error);
    }
  };

  // File handling
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
      fetchJobHistory();
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

      const response = await fetch(
        `${API_BASE}/process/${jobId}?speed_factor=${speedFactor}`,
        { method: 'POST' }
      );

      if (!response.ok) throw new Error('Processing failed');

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
          fetchAnalytics(jobId);
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

  // Add to batch
  const handleAddToBatch = async () => {
    if (!jobId) return;
    try {
      await fetch(`${API_BASE}/batch/add/${jobId}`, { method: 'POST' });
      fetchQueueStatus();
      alert('Job added to batch queue');
    } catch (error) {
      console.error('Batch error:', error);
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
    setAnalytics(null);
    setProgress(0);
    setVideoInfo(null);
    setActiveTab('upload');
  };

  // Load history on mount
  useEffect(() => {
    fetchJobHistory();
    fetchQueueStatus();
    const interval = setInterval(() => {
      fetchQueueStatus();
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="vehicle-counter-advanced-app">
      {/* Advanced Header */}
      <header className="advanced-header">
        <div className="header-content">
          <div className="app-logo">
            <Truck className="logo-icon" />
            <div>
              <h1>Vehicle Counter Pro</h1>
              <p>Advanced Analytics & Batch Processing</p>
            </div>
          </div>
          <div className="header-controls">
            <button
              className="btn-toggle-advanced"
              onClick={() => setShowAdvanced(!showAdvanced)}
            >
              <Settings size={20} />
              {showAdvanced ? 'Hide' : 'Show'} Advanced
            </button>
            <span className="status-badge" data-status={processingStatus}>
              {processingStatus.toUpperCase()}
            </span>
          </div>
        </div>
      </header>

      {/* Main Container */}
      <div className="advanced-container">
        {/* Advanced Sidebar */}
        <aside className="advanced-sidebar">
          <nav className="nav-section">
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
            <button
              className={`nav-item ${activeTab === 'analytics' ? 'active' : ''}`}
              onClick={() => analytics && setActiveTab('analytics')}
              disabled={!analytics}
            >
              <LineChartIcon size={20} />
              <span>Analytics</span>
            </button>
            <button
              className={`nav-item ${activeTab === 'history' ? 'active' : ''}`}
              onClick={() => setActiveTab('history')}
            >
              <Calendar size={20} />
              <span>History</span>
            </button>
          </nav>

          {jobId && (
            <div className="job-info">
              <p className="job-label">Active Job</p>
              <p className="job-id">{jobId}</p>
              <div className="job-stats">
                <div className="stat">
                  <span className="stat-label">Status</span>
                  <span className="stat-value">{processingStatus}</span>
                </div>
                {results && (
                  <div className="stat">
                    <span className="stat-label">Vehicles</span>
                    <span className="stat-value">{results.total_vehicles}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {showAdvanced && (
            <div className="advanced-panel">
              <h3>Advanced Options</h3>
              <button
                className="btn-batch"
                onClick={handleAddToBatch}
                disabled={!jobId || processingStatus !== 'completed'}
              >
                <Activity size={16} />
                Add to Batch
              </button>
              <div className="batch-info">
                <p className="info-label">Queue Status</p>
                <p className="info-value">{batchQueue.queue_size || 0} jobs</p>
              </div>
            </div>
          )}
        </aside>

        {/* Content Area */}
        <main className="advanced-content">
          {/* Results Tab with Enhanced Analytics */}
          {activeTab === 'results' && results && (
            <section className="tab-content results-section">
              <div className="results-container">
                {/* Enhanced Summary Cards */}
                <div className="summary-grid">
                  <div className="summary-card primary">
                    <div className="summary-icon">🚗</div>
                    <div className="summary-data">
                      <p className="summary-label">Total Vehicles</p>
                      <p className="summary-value">{results.total_vehicles}</p>
                    </div>
                  </div>

                  <div className="summary-card">
                    <div className="summary-icon">⚡</div>
                    <div className="summary-data">
                      <p className="summary-label">Processing Time</p>
                      <p className="summary-value">{results.processing_time?.toFixed(1)}s</p>
                    </div>
                  </div>

                  <div className="summary-card">
                    <div className="summary-icon">🎯</div>
                    <div className="summary-data">
                      <p className="summary-label">Accuracy</p>
                      <p className="summary-value">{(results.accuracy * 100)?.toFixed(1)}%</p>
                    </div>
                  </div>

                  <div className="summary-card">
                    <div className="summary-icon">📊</div>
                    <div className="summary-data">
                      <p className="summary-label">Vehicle Types</p>
                      <p className="summary-value">{Object.keys(results.vehicle_breakdown || {}).length}</p>
                    </div>
                  </div>
                </div>

                {/* Vehicle Breakdown */}
                <div className="breakdown-section">
                  <h2>Vehicle Type Distribution</h2>
                  <div className="vehicle-types-grid">
                    {Object.entries(results.vehicle_breakdown || {}).map(([type, count]) => (
                      <div key={type} className="vehicle-type-card">
                        <div className="type-name">{type.toUpperCase()}</div>
                        <div className="type-count">{count}</div>
                        <div className="type-percentage">
                          {((count / results.total_vehicles) * 100).toFixed(1)}%
                        </div>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Export & Actions */}
                <div className="action-section">
                  <h2>Export & Actions</h2>
                  <div className="action-buttons">
                    <button className="btn btn-outline" onClick={() => handleExport('csv')}>
                      <Download size={20} />
                      Export CSV
                    </button>
                    <button className="btn btn-outline" onClick={() => handleExport('json')}>
                      <Download size={20} />
                      Export JSON
                    </button>
                    <button className="btn btn-outline" onClick={handleAddToBatch}>
                      <Activity size={20} />
                      Add to Batch
                    </button>
                    <button className="btn btn-primary" onClick={handleReset}>
                      Process New Video
                    </button>
                  </div>
                </div>
              </div>
            </section>
          )}

          {/* Analytics Tab */}
          {activeTab === 'analytics' && analytics && (
            <section className="tab-content analytics-section">
              <div className="analytics-container">
                <h2>Advanced Analytics</h2>
                <div className="analytics-grid">
                  <div className="metric-card">
                    <TrendingUp size={24} className="metric-icon" />
                    <p className="metric-label">Peak Traffic</p>
                    <p className="metric-value">{analytics.peak_traffic}</p>
                  </div>

                  <div className="metric-card">
                    <Activity size={24} className="metric-icon" />
                    <p className="metric-label">Average Traffic</p>
                    <p className="metric-value">{analytics.average_traffic?.toFixed(1)}</p>
                  </div>

                  <div className="metric-card">
                    <BarChart3 size={24} className="metric-icon" />
                    <p className="metric-label">Detection Rate</p>
                    <p className="metric-value">{analytics.processing_efficiency?.toFixed(1)}%</p>
                  </div>

                  <div className="metric-card">
                    <LineChartIcon size={24} className="metric-icon" />
                    <p className="metric-label">Confidence Score</p>
                    <p className="metric-value">{(analytics.detection_accuracy * 100)?.toFixed(1)}%</p>
                  </div>
                </div>

                <div className="analytics-info">
                  <p>📊 Detailed analytics powered by advanced computer vision algorithms</p>
                </div>
              </div>
            </section>
          )}

          {/* History Tab */}
          {activeTab === 'history' && (
            <section className="tab-content history-section">
              <div className="history-container">
                <h2>Processing History</h2>
                <div className="history-table-wrapper">
                  <table className="history-table">
                    <thead>
                      <tr>
                        <th>Job ID</th>
                        <th>Filename</th>
                        <th>Status</th>
                        <th>Vehicles</th>
                        <th>Accuracy</th>
                        <th>Time (s)</th>
                        <th>Created</th>
                      </tr>
                    </thead>
                    <tbody>
                      {jobHistory.map((job) => (
                        <tr key={job.job_id} className={`status-${job.status}`}>
                          <td className="mono">{job.job_id}</td>
                          <td>{job.filename}</td>
                          <td><span className="status-badge">{job.status}</span></td>
                          <td>{job.total_vehicles}</td>
                          <td>{(job.accuracy * 100)?.toFixed(1)}%</td>
                          <td>{job.processing_time?.toFixed(1)}</td>
                          <td>{new Date(job.created_at).toLocaleDateString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </section>
          )}

          {/* Default sections remain the same */}
          {activeTab === 'upload' && (
            <section className="tab-content upload-section">
              <div className="upload-area">
                <div className="drop-zone">
                  <Upload size={48} className="drop-icon" />
                  <h2>Upload Your Video</h2>
                  <p>Drag and drop your video file here</p>
                  <p className="supported-formats">Supported: MP4, AVI, MOV, MKV</p>
                  <button className="btn btn-primary" onClick={() => fileInputRef.current?.click()}>
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
                    <button className="btn btn-success btn-large" onClick={handleUpload}>
                      {processingStatus === 'uploading' ? 'Uploading...' : 'Upload & Continue'}
                    </button>
                  </div>
                )}
              </div>
            </section>
          )}

          {/* Other sections (preview, process) remain the same as before */}
        </main>
      </div>
    </div>
  );
};

export default VehicleCounterAdvancedApp;
