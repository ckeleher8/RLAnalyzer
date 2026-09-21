// src/components/MatchHistoryModal.jsx
import React, { useEffect, useState } from 'react';
import { getRecentMatches, getMatchById } from '../services/api';
import { History, X, Trophy, Calendar, FileText, ArrowRight, Loader2 } from 'lucide-react';

export default function MatchHistoryModal({ isOpen, onClose, onSelectMatch }) {
    const [matches, setMatches] = useState([]);
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        if (isOpen) {
            fetchHistory();
        }
    }, [isOpen]);

    const fetchHistory = async () => {
        setIsLoading(true);
        try {
            const list = await getRecentMatches(15);
            setMatches(list || []);
        } catch (error) {
            console.error('Failed to fetch match history:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleSelect = async (matchId) => {
        try {
            const fullMatch = await getMatchById(matchId);
            onSelectMatch(fullMatch);
            onClose();
        } catch (err) {
            console.error('Failed to load selected match:', err);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content glass-panel" onClick={(e) => e.stopPropagation()}>
                <div className="modal-header">
                    <div className="modal-title-wrapper">
                        <History size={20} className="text-cyan" />
                        <h3>Replay Database History</h3>
                    </div>
                    <button className="btn-close" onClick={onClose}>
                        <X size={18} />
                    </button>
                </div>

                <div className="modal-body">
                    {isLoading ? (
                        <div className="loading-state">
                            <Loader2 size={32} className="animate-spin text-cyan" />
                            <p>Loading database records...</p>
                        </div>
                    ) : matches.length === 0 ? (
                        <div className="empty-history">
                            <FileText size={40} className="text-muted" />
                            <p>No replays analyzed yet.</p>
                            <span>Upload a .replay file on the dashboard to build your match database.</span>
                        </div>
                    ) : (
                        <div className="history-list">
                            {matches.map((m) => (
                                <div 
                                    key={m.id} 
                                    className="history-item glass-panel"
                                    onClick={() => handleSelect(m.id)}
                                >
                                    <div className="history-left">
                                        <div className="history-score">
                                            <span className="text-cyan font-bold">{m.blueScore}</span>
                                            <span className="text-muted">-</span>
                                            <span className="text-orange font-bold">{m.orangeScore}</span>
                                        </div>
                                        <div>
                                            <h4 className="history-name">{m.fileName}</h4>
                                            <div className="history-meta">
                                                <Calendar size={12} />
                                                <span>{new Date(m.uploadedAt).toLocaleString()}</span>
                                                <span className="bullet">•</span>
                                                <span className={`status-tag status-${m.status.toLowerCase()}`}>
                                                    {m.status}
                                                </span>
                                            </div>
                                        </div>
                                    </div>

                                    <div className="history-action">
                                        <button className="btn btn-secondary btn-sm">
                                            <span>Inspect</span>
                                            <ArrowRight size={14} />
                                        </button>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
