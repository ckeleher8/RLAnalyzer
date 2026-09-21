// src/components/Navbar.jsx
import React from 'react';
import { Activity, History, Zap, Shield, Sparkles } from 'lucide-react';

export default function Navbar({ onOpenHistory, onNewUpload, isGatewayOnline, activeMatch }) {
    return (
        <header className="navbar-container">
            <div className="navbar-brand" onClick={onNewUpload} style={{ cursor: 'pointer' }}>
                <div className="brand-icon-wrapper">
                    <Zap size={22} className="brand-icon" />
                </div>
                <div>
                    <div className="brand-title">
                        RL<span className="brand-gradient">ANALYZER</span>
                    </div>
                    <div className="brand-subtitle">AI Telemetry & Match Impact Engine</div>
                </div>
            </div>

            <div className="navbar-actions">
                <div className="status-pill">
                    <span className={`status-dot ${isGatewayOnline ? 'dot-online' : 'dot-offline'}`} />
                    <span className="status-label">
                        {isGatewayOnline ? 'Gateway Connected' : 'Gateway Offline'}
                    </span>
                </div>

                <div className="status-pill">
                    <span className="status-dot dot-online" />
                    <span className="status-label">XGBoost v2 Ready</span>
                </div>

                <button className="btn btn-secondary" onClick={onOpenHistory}>
                    <History size={16} />
                    <span>Match History</span>
                </button>

                {activeMatch && (
                    <button className="btn btn-primary" onClick={onNewUpload}>
                        <Sparkles size={16} />
                        <span>Upload New Replay</span>
                    </button>
                )}
            </div>
        </header>
    );
}
