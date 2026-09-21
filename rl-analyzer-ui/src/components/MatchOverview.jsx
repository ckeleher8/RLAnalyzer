// src/components/MatchOverview.jsx
import React from 'react';
import { Trophy, Clock, MapPin, Target, Shield, Zap, TrendingUp, Flame, Award } from 'lucide-react';

export default function MatchOverview({ matchData, onSelectTab, onSelectPlayer }) {
    if (!matchData) return null;

    const { 
        fileName, 
        mapName, 
        durationSeconds, 
        blueScore, 
        orangeScore, 
        winningTeam, 
        players = [] 
    } = matchData;

    const bluePlayers = players.filter(p => p.team?.toLowerCase() === 'blue');
    const orangePlayers = players.filter(p => p.team?.toLowerCase() === 'orange');

    // Identify match MVP based on highest total action value
    const sortedByImpact = [...players].sort((a, b) => b.total_Action_Value - a.total_Action_Value);
    const mvpPlayer = sortedByImpact[0];

    const formatDuration = (secs) => {
        if (!secs) return '5:00';
        const m = Math.floor(secs / 60);
        const s = secs % 60;
        return `${m}:${s < 10 ? '0' : ''}${s}`;
    };

    return (
        <div className="overview-container">
            {/* 1. Match Header Metadata */}
            <div className="match-meta-bar glass-panel">
                <div className="meta-item">
                    <MapPin size={16} className="text-cyan" />
                    <span className="meta-label">Map:</span>
                    <span className="meta-val">{mapName || 'DFH Stadium'}</span>
                </div>
                <div className="meta-item">
                    <Clock size={16} className="text-cyan" />
                    <span className="meta-label">Duration:</span>
                    <span className="meta-val">{formatDuration(durationSeconds)}</span>
                </div>
                <div className="meta-item">
                    <Award size={16} className="text-yellow" />
                    <span className="meta-label">Match MVP:</span>
                    <span className="meta-val highlight-mvp">{mvpPlayer?.name || 'N/A'}</span>
                </div>
            </div>

            {/* 2. Clash Scoreboard Banner */}
            <div className="scoreboard-banner glass-panel">
                <div className={`team-side team-blue ${winningTeam?.toLowerCase() === 'blue' ? 'winner-glow' : ''}`}>
                    <div className="team-header">
                        <div className="team-badge-large badge-blue">BLUE TEAM</div>
                        {winningTeam?.toLowerCase() === 'blue' && (
                            <span className="winner-tag"><Trophy size={14} /> VICTORY</span>
                        )}
                    </div>
                    <div className="score-display blue-glow-text">{blueScore ?? 0}</div>
                    <div className="team-roster">
                        {bluePlayers.map(p => (
                            <span 
                                key={p.name} 
                                className="roster-pill roster-blue"
                                onClick={() => { onSelectPlayer(p.name); onSelectTab('timeline'); }}
                            >
                                {p.name}
                            </span>
                        ))}
                    </div>
                </div>

                <div className="vs-divider">
                    <span className="vs-badge">VS</span>
                </div>

                <div className={`team-side team-orange ${winningTeam?.toLowerCase() === 'orange' ? 'winner-glow' : ''}`}>
                    <div className="team-header">
                        <div className="team-badge-large badge-orange">ORANGE TEAM</div>
                        {winningTeam?.toLowerCase() === 'orange' && (
                            <span className="winner-tag"><Trophy size={14} /> VICTORY</span>
                        )}
                    </div>
                    <div className="score-display orange-glow-text">{orangeScore ?? 0}</div>
                    <div className="team-roster">
                        {orangePlayers.map(p => (
                            <span 
                                key={p.name} 
                                className="roster-pill roster-orange"
                                onClick={() => { onSelectPlayer(p.name); onSelectTab('timeline'); }}
                            >
                                {p.name}
                            </span>
                        ))}
                    </div>
                </div>
            </div>

            {/* 3. Player Stats & ML Ratings Grid */}
            <div className="section-title-wrapper">
                <h3 className="section-heading">Player Impact & Performance Telemetry</h3>
                <span className="section-subheading">Click any card to inspect their frame-by-frame impact curve</span>
            </div>

            <div className="player-grid">
                {players.map(player => {
                    const isBlue = player.team?.toLowerCase() === 'blue';
                    const isMvp = player.name === mvpPlayer?.name;

                    return (
                        <div 
                            key={player.name}
                            className={`player-card glass-panel ${isBlue ? 'card-blue' : 'card-orange'} ${isMvp ? 'card-mvp' : ''}`}
                            onClick={() => { onSelectPlayer(player.name); onSelectTab('timeline'); }}
                        >
                            <div className="card-top">
                                <div>
                                    <div className="player-name-wrapper">
                                        <h4 className="player-card-name">{player.name}</h4>
                                        {isMvp && <span className="badge badge-warning mvp-pill"><Flame size={12} /> MVP</span>}
                                    </div>
                                    <span className={`badge ${isBlue ? 'badge-blue' : 'badge-orange'}`}>
                                        {player.team}
                                    </span>
                                </div>

                                <div className="card-impact-score">
                                    <span className="impact-label">Total Impact</span>
                                    <span className={`impact-val ${player.total_Action_Value >= 0 ? 'text-green' : 'text-rose'}`}>
                                        {player.total_Action_Value > 0 ? '+' : ''}{player.total_Action_Value.toFixed(2)}
                                    </span>
                                </div>
                            </div>

                            <div className="card-stats-row">
                                <div className="stat-box">
                                    <Target size={14} className="stat-icon text-cyan" />
                                    <span className="stat-num">{player.goals}</span>
                                    <span className="stat-lbl">Goals</span>
                                </div>
                                <div className="stat-box">
                                    <Shield size={14} className="stat-icon text-green" />
                                    <span className="stat-num">{player.saves}</span>
                                    <span className="stat-lbl">Saves</span>
                                </div>
                                <div className="stat-box">
                                    <TrendingUp size={14} className="stat-icon text-yellow" />
                                    <span className="stat-num">{player.avg_Action_Value > 0 ? '+' : ''}{player.avg_Action_Value.toFixed(3)}</span>
                                    <span className="stat-lbl">Avg / Touch</span>
                                </div>
                                <div className="stat-box">
                                    <Zap size={14} className="stat-icon text-orange" />
                                    <span className="stat-num">{player.total_Wasted_Boost}</span>
                                    <span className="stat-lbl">Wasted Boost</span>
                                </div>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
