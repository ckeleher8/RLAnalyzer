// src/components/ActionValueTimeline.jsx
import React, { useState } from 'react';
import { 
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, 
    ReferenceLine, ResponsiveContainer, Cell 
} from 'recharts';
import { 
    Filter, TrendingUp, TrendingDown, Award, 
    CheckCircle2, XCircle, Info, Zap 
} from 'lucide-react';

export default function ActionValueTimeline({ matchData, selectedPlayer, onSelectPlayer }) {
    const [filterType, setFilterType] = useState('all'); // all, positive, negative, key_events
    const [inspectedTouch, setInspectedTouch] = useState(null);

    if (!matchData || !matchData.touches || matchData.touches.length === 0) {
        return (
            <div className="empty-state glass-panel">
                <Info size={32} className="text-muted" />
                <p>No touch-level action value data found for this replay.</p>
            </div>
        );
    }

    const players = matchData.players || [];
    const activePlayerObj = players.find(p => p.name === selectedPlayer) || players[0];
    const currentPlayerName = activePlayerObj?.name || selectedPlayer;

    // Normalize touches
    const normalizedTouches = (matchData.touches || []).map(t => ({
        frame: t.frame ?? t.Frame ?? 0,
        player: t.player ?? t.Player ?? '',
        team: t.team ?? t.Team ?? '',
        action_Value: t.action_Value ?? t.Action_Value ?? 0,
        v_Before: t.v_Before ?? t.V_Before ?? 0,
        v_After: t.v_After ?? t.V_After ?? 0,
        is_Goal: t.is_Goal ?? t.Is_Goal ?? false,
        is_Save: t.is_Save ?? t.Is_Save ?? false
    }));

    // Filter touches for the selected player
    const playerTouches = normalizedTouches.filter(t => t.player === currentPlayerName);

    // Apply secondary category filter
    const filteredTouches = playerTouches.filter(touch => {
        if (filterType === 'positive') return touch.action_Value > 0;
        if (filterType === 'negative') return touch.action_Value < 0;
        if (filterType === 'key_events') return touch.is_Goal || touch.is_Save || Math.abs(touch.action_Value) >= 0.2;
        return true;
    });

    // Compute player summary stats
    const positiveTouches = playerTouches.filter(t => t.action_Value > 0);
    const negativeTouches = playerTouches.filter(t => t.action_Value < 0);
    const totalPositive = positiveTouches.reduce((acc, t) => acc + t.action_Value, 0);
    const totalNegative = negativeTouches.reduce((acc, t) => acc + t.action_Value, 0);
    const netImpact = totalPositive + totalNegative;

    const CustomTooltip = ({ active, payload }) => {
        if (active && payload && payload.length) {
            const touch = payload[0].payload;
            const isPos = touch.action_Value > 0;

            return (
                <div className="chart-tooltip glass-panel">
                    <div className="tooltip-header">
                        <span className="tooltip-frame">Frame #{touch.frame}</span>
                        <span className={`badge ${isPos ? 'badge-success' : 'badge-danger'}`}>
                            {isPos ? '+ Positive Shift' : '- Negative Shift'}
                        </span>
                    </div>
                    <div className="tooltip-body">
                        <div className="tooltip-row">
                            <span>Impact Value (ΔV):</span>
                            <strong className={isPos ? 'text-green' : 'text-rose'}>
                                {isPos ? '+' : ''}{Number(touch.action_Value).toFixed(3)}
                            </strong>
                        </div>
                        <div className="tooltip-row">
                            <span>State Before ($V_0$):</span>
                            <span>{Number(touch.v_Before).toFixed(3)}</span>
                        </div>
                        <div className="tooltip-row">
                            <span>State After ($V_1$):</span>
                            <span>{Number(touch.v_After).toFixed(3)}</span>
                        </div>
                        {touch.is_Goal && <div className="tooltip-highlight text-yellow">⚽ Goal Scored</div>}
                        {touch.is_Save && <div className="tooltip-highlight text-cyan">🛡️ Key Defensive Save</div>}
                    </div>
                </div>
            );
        }
        return null;
    };

    return (
        <div className="timeline-view-container">
            {/* 1. Control Toolbar */}
            <div className="timeline-toolbar glass-panel">
                <div className="toolbar-left">
                    <label className="toolbar-label">Player Focus:</label>
                    <select 
                        className="custom-select"
                        value={currentPlayerName}
                        onChange={(e) => {
                            onSelectPlayer(e.target.value);
                            setInspectedTouch(null);
                        }}
                    >
                        {players.map(p => (
                            <option key={p.name} value={p.name}>
                                [{p.team}] {p.name}
                            </option>
                        ))}
                    </select>
                </div>

                <div className="toolbar-filters">
                    <span className="filter-label"><Filter size={14} /> Filter:</span>
                    <button 
                        className={`filter-btn ${filterType === 'all' ? 'active' : ''}`}
                        onClick={() => setFilterType('all')}
                    >
                        All Touches ({playerTouches.length})
                    </button>
                    <button 
                        className={`filter-btn ${filterType === 'positive' ? 'active-pos' : ''}`}
                        onClick={() => setFilterType('positive')}
                    >
                        Positive (+{positiveTouches.length})
                    </button>
                    <button 
                        className={`filter-btn ${filterType === 'negative' ? 'active-neg' : ''}`}
                        onClick={() => setFilterType('negative')}
                    >
                        Negative ({negativeTouches.length})
                    </button>
                    <button 
                        className={`filter-btn ${filterType === 'key_events' ? 'active-key' : ''}`}
                        onClick={() => setFilterType('key_events')}
                    >
                        Key Highlights
                    </button>
                </div>
            </div>

            {/* 2. Impact Summary Pill Cards */}
            <div className="impact-summary-row">
                <div className="impact-pill glass-panel">
                    <TrendingUp size={20} className="text-green" />
                    <div>
                        <span className="pill-lbl">Created Value</span>
                        <span className="pill-val text-green">+{totalPositive.toFixed(2)}</span>
                    </div>
                </div>
                <div className="impact-pill glass-panel">
                    <TrendingDown size={20} className="text-rose" />
                    <div>
                        <span className="pill-lbl">Conceded Value</span>
                        <span className="pill-val text-rose">{totalNegative.toFixed(2)}</span>
                    </div>
                </div>
                <div className="impact-pill glass-panel">
                    <Award size={20} className="text-cyan" />
                    <div>
                        <span className="pill-lbl">Net Match Impact</span>
                        <span className={`pill-val ${netImpact >= 0 ? 'text-green' : 'text-rose'}`}>
                            {netImpact > 0 ? '+' : ''}{netImpact.toFixed(2)}
                        </span>
                    </div>
                </div>
            </div>

            {/* 3. Recharts Impact BarChart */}
            <div className="chart-wrapper glass-panel">
                <div className="chart-header">
                    <div>
                        <h3 className="chart-title">Action Value Impact Curve: {currentPlayerName}</h3>
                        <p className="chart-sub">
                            Evaluates probability shift (ΔV = V_after - V_before) driven by each ball touch
                        </p>
                    </div>
                    <span className="spec-tag">Frame Interval ~30Hz</span>
                </div>

                <div className="chart-canvas" style={{ width: '100%', height: 380 }}>
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart 
                            data={filteredTouches} 
                            margin={{ top: 15, right: 30, left: 10, bottom: 15 }}
                            onClick={(e) => {
                                if (e && e.activePayload && e.activePayload.length) {
                                    setInspectedTouch(e.activePayload[0].payload);
                                }
                            }}
                        >
                            <CartesianGrid strokeDasharray="3 3" stroke="#1e293b" />
                            <XAxis 
                                dataKey="frame" 
                                stroke="#64748b" 
                                tick={{ fill: '#64748b', fontSize: 11 }}
                                label={{ value: 'Replay Frame Number', position: 'insideBottom', offset: -10, fill: '#64748b', fontSize: 12 }}
                            />
                            <YAxis 
                                domain={[-0.8, 0.8]} 
                                stroke="#64748b"
                                tick={{ fill: '#64748b', fontSize: 11 }}
                                label={{ value: 'Action Value (ΔV)', angle: -90, position: 'insideLeft', fill: '#64748b', fontSize: 12 }}
                            />
                            <Tooltip content={<CustomTooltip />} />
                            <ReferenceLine y={0} stroke="#475569" strokeWidth={1.5} />
                            
                            <Bar dataKey="action_Value" radius={[3, 3, 0, 0]}>
                                {filteredTouches.map((entry, index) => (
                                    <Cell 
                                        key={`touch-cell-${index}`} 
                                        fill={entry.action_Value > 0 ? '#10b981' : '#f43f5e'}
                                        cursor="pointer"
                                    />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* 4. Touch Inspector Drawer/Card */}
            {inspectedTouch && (
                <div className="touch-inspector glass-panel">
                    <div className="inspector-header">
                        <h4>Selected Touch Telemetry (Frame #{inspectedTouch.frame})</h4>
                        <button className="btn-close" onClick={() => setInspectedTouch(null)}>✕</button>
                    </div>
                    <div className="inspector-grid">
                        <div className="inspector-item">
                            <span className="lbl">Player:</span>
                            <span className="val">{inspectedTouch.player} ({inspectedTouch.team})</span>
                        </div>
                        <div className="inspector-item">
                            <span className="lbl">Impact (ΔV):</span>
                            <span className={`val ${inspectedTouch.action_Value >= 0 ? 'text-green' : 'text-rose'}`}>
                                {inspectedTouch.action_Value > 0 ? '+' : ''}{Number(inspectedTouch.action_Value).toFixed(3)}
                            </span>
                        </div>
                        <div className="inspector-item">
                            <span className="lbl">Pitch State Before:</span>
                            <span className="val">{Number(inspectedTouch.v_Before).toFixed(3)}</span>
                        </div>
                        <div className="inspector-item">
                            <span className="lbl">Pitch State After:</span>
                            <span className="val">{Number(inspectedTouch.v_After).toFixed(3)}</span>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}