// src/components/ReplayUpload.jsx
import React, { useState, useRef } from 'react';
import { UploadCloud, FileText, Loader2, Sparkles, CheckCircle2, AlertCircle, Play } from 'lucide-react';
import { uploadReplay, getMatchStatus, getMatchById } from '../services/api';

export default function ReplayUpload({ onAnalysisComplete }) {
    const [isDragging, setIsDragging] = useState(false);
    const [file, setFile] = useState(null);
    const [isProcessing, setIsProcessing] = useState(false);
    const [processStep, setProcessStep] = useState('');
    const [errorMessage, setErrorMessage] = useState(null);
    const fileInputRef = useRef(null);

    const handleDragOver = (e) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = () => {
        setIsDragging(false);
    };

    const handleDrop = (e) => {
        e.preventDefault();
        setIsDragging(false);
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            validateAndProcessFile(e.dataTransfer.files[0]);
        }
    };

    const handleFileInput = (e) => {
        if (e.target.files && e.target.files.length > 0) {
            validateAndProcessFile(e.target.files[0]);
        }
    };

    const validateAndProcessFile = async (selectedFile) => {
        if (!selectedFile.name.endsWith('.replay')) {
            setErrorMessage('Please upload a valid Rocket League (.replay) binary file.');
            return;
        }

        setFile(selectedFile);
        setErrorMessage(null);
        await startUploadAndPolling(selectedFile);
    };

    const startUploadAndPolling = async (replayFile) => {
        setIsProcessing(true);
        setProcessStep('Submitting replay to C# .NET Gateway...');

        try {
            // 1. Upload to Gateway
            const uploadResponse = await uploadReplay(replayFile);
            const matchId = uploadResponse.id;

            setProcessStep('Gateway queued job. Python ML engine parsing frames & heuristics...');

            // 2. Poll until completed
            let attempts = 0;
            const maxAttempts = 120; // 60s
            const pollInterval = setInterval(async () => {
                attempts++;
                try {
                    const statusRes = await getMatchStatus(matchId);
                    
                    if (statusRes.status === 'Completed') {
                        clearInterval(pollInterval);
                        setProcessStep('Analysis complete! Loading dashboard insights...');
                        const fullMatch = await getMatchById(matchId);
                        setIsProcessing(false);
                        onAnalysisComplete(fullMatch);
                    } else if (statusRes.status === 'Failed') {
                        clearInterval(pollInterval);
                        setIsProcessing(false);
                        setErrorMessage(statusRes.message || 'Replay analysis failed.');
                    } else {
                        // Dynamic progress label based on elapsed time
                        if (attempts > 3) setProcessStep('Extracting pitch state & computing 3rd-man / boost heuristics...');
                        if (attempts > 8) setProcessStep('Executing XGBoost action value evaluator across all touches...');
                        if (attempts > 14) setProcessStep('Persisting match statistics to SQL database...');
                    }
                } catch (err) {
                    console.error('Polling error:', err);
                }

                if (attempts >= maxAttempts) {
                    clearInterval(pollInterval);
                    setIsProcessing(false);
                    setErrorMessage('Processing timed out. Please verify ML engine is running.');
                }
            }, 500);

        } catch (error) {
            console.error('Upload failed:', error);
            setIsProcessing(false);
            setErrorMessage(error.response?.data?.error || error.message || 'Failed to upload replay file.');
        }
    };

    return (
        <div className="upload-container">
            <div className="upload-hero">
                <div className="badge badge-blue hero-badge">
                    <Sparkles size={14} /> AI-Powered Rocket League Telemetry
                </div>
                <h1 className="hero-title">
                    Analyze Match Impact with <span className="text-gradient-cyan">Next-Gen AI</span>
                </h1>
                <p className="hero-description">
                    Upload your Rocket League <code className="code-pill">.replay</code> file to compute frame-by-frame
                    Action Value impact ratings (ΔV), 3rd-man rotation efficiency, supersonic boost waste, and pad pathing.
                </p>
            </div>

            <div 
                className={`dropzone-card glass-panel ${isDragging ? 'dropzone-active' : ''} ${isProcessing ? 'dropzone-processing' : ''}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => !isProcessing && fileInputRef.current?.click()}
            >
                <input 
                    type="file" 
                    ref={fileInputRef} 
                    accept=".replay" 
                    onChange={handleFileInput} 
                    style={{ display: 'none' }}
                />

                {!isProcessing ? (
                    <div className="dropzone-content">
                        <div className="upload-icon-circle">
                            <UploadCloud size={40} className="upload-icon" />
                        </div>
                        <h3 className="dropzone-heading">Drop your <span className="text-cyan">.replay</span> file here</h3>
                        <p className="dropzone-sub">or click to browse local files</p>
                        
                        <div className="dropzone-specs">
                            <span className="spec-tag">Supports 1v1, 2v2, 3v3</span>
                            <span className="spec-tag">All Ranks (SSL / RLCS Optimized)</span>
                        </div>
                    </div>
                ) : (
                    <div className="dropzone-loading">
                        <div className="loading-radar-ring">
                            <Loader2 size={48} className="animate-spin text-cyan" />
                        </div>
                        <h3 className="loading-title">{processStep}</h3>
                        <div className="loading-progress-bar">
                            <div className="progress-bar-fill" />
                        </div>
                        <p className="loading-filename">
                            <FileText size={16} /> {file?.name}
                        </p>
                    </div>
                )}
            </div>

            {errorMessage && (
                <div className="error-banner">
                    <AlertCircle size={18} />
                    <span>{errorMessage}</span>
                </div>
            )}
        </div>
    );
}
