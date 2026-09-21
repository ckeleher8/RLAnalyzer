// src/components/HeuristicsCenter.jsx
import React, { useState } from 'react';
import { 
    ShieldAlert, Zap, Compass, AlertTriangle, 
    CheckCircle2, Flame, HelpCircle, Navigation, 
    Info, Target, ArrowRight, Gauge, Layers
} from 'lucide-react';

export default function HeuristicsCenter({ matchData, selectedPlayer, onSelectPlayer }) {
    const [subTab, setSubTab] = useState('rotation'); // rotation, boost_waste, pad_pathing

    if (!matchData) return null;

    const players = matchData.players || [];
    const activePlayerObj = players.find(p => p.name === selectedPlayer) || players[0];
    const currentPlayer = activePlayerObj?.name || selectedPlayer;
    const heuristics = matchData.heuristics || {};

    // Determine team size and game mode (2v2 vs 3v3 vs 1v1)
    const bluePlayers = players.filter(p => p.team?.toLowerCase() === 'blue');
    const orangePlayers = players.filter(p => p.team?.toLowerCase() === 'orange');
    const teamSize = Math.max(bluePlayers.length, orangePlayers.length) || 2;
    const is2v2 = teamSize === 2;
    const is3v3 = teamSize >= 3;

    const roleTitle = is2v2 ? "2nd Man (Last Man)" : is3v3 ? "3rd Man (Last Defender)" : "Solo Defender";
    const roleShort = is2v2 ? "2nd-Man" : is3v3 ? "3rd-Man" : "Last Man";
    const gameModeLabel = is2v2 ? "2v2 Doubles" : is3v3 ? "3v3 Standard" : "1v1 Duel";
    const optimalPresenceRange = is2v2 ? "40% – 60%" : is3v3 ? "28% – 38%" : "100%";

    // 1. Rotation Data (from Last Man / Third Man heuristic)
    const blueThirdMan = heuristics['Blue_Third_Man'] || heuristics['Blue_Last_Man'] || [];
    const orangeThirdMan = heuristics['Orange_Third_Man'] || heuristics['Orange_Last_Man'] || [];
    const allThirdMan = [...blueThirdMan, ...orangeThirdMan];

    const blueLastMeta = heuristics['Blue_Last_Man_Meta'] || {};
    const orangeLastMeta = heuristics['Orange_Last_Man_Meta'] || {};
    const playerLastMeta = blueLastMeta?.player_summaries?.[currentPlayer] || 
                           orangeLastMeta?.player_summaries?.[currentPlayer] || null;

    const rawCreepCount = allThirdMan.filter(r => (r.Third_Man_Name === currentPlayer || r.Last_Man_Name === currentPlayer) && r.Flag_Creeping).length;
    const rawSagCount = allThirdMan.filter(r => (r.Third_Man_Name === currentPlayer || r.Last_Man_Name === currentPlayer) && r.Flag_Sagging).length;
    const rawTotalLastManFrames = allThirdMan.filter(r => r.Third_Man_Name === currentPlayer || r.Last_Man_Name === currentPlayer).length;

    const creepingFrames = playerLastMeta?.creeping_frames ?? (rawCreepCount * 10);
    const creepingSeconds = playerLastMeta?.creeping_seconds ?? (creepingFrames / 30.0).toFixed(1);
    const saggingFrames = playerLastMeta?.sagging_frames ?? (rawSagCount * 10);
    const saggingSeconds = playerLastMeta?.sagging_seconds ?? (saggingFrames / 30.0).toFixed(1);

    const totalMatchFrames = matchData.durationSeconds ? (matchData.durationSeconds * 30) : 9000;
    const totalLastManFrames = playerLastMeta?.total_last_man_frames ?? (rawTotalLastManFrames * 10);
    const presencePct = playerLastMeta?.presence_pct ?? Math.min(100, Math.round((totalLastManFrames / totalMatchFrames) * 100));

    // Dynamic Benchmarks for Creeping and Sagging
    const getCreepStatus = (frames) => {
        if (frames <= 30) return { label: "Optimal (< 1.0s)", color: "text-green", border: "border-green", badgeClass: "badge-green", state: "optimal" };
        if (frames <= 90) return { label: "Acceptable (1.0s – 3.0s)", color: "text-yellow", border: "border-amber", badgeClass: "badge-yellow", state: "acceptable" };
        return { label: "Critical Overcommit (> 3.0s)", color: "text-rose", border: "border-rose", badgeClass: "badge-rose", state: "danger" };
    };

    const getSagStatus = (frames) => {
        if (frames <= 60) return { label: "Optimal (< 2.0s)", color: "text-green", border: "border-green", badgeClass: "badge-green", state: "optimal" };
        if (frames <= 150) return { label: "Acceptable (2.0s – 5.0s)", color: "text-cyan", border: "border-cyan", badgeClass: "badge-cyan", state: "acceptable" };
        return { label: "Too Passive (> 5.0s)", color: "text-rose", border: "border-rose", badgeClass: "badge-rose", state: "danger" };
    };

    const creepStatus = getCreepStatus(creepingFrames);
    const sagStatus = getSagStatus(saggingFrames);

    // 2. Supersonic Waste data
    const wasteList = heuristics[`${currentPlayer}_Supersonic_Waste`] || [];
    const wasteEcon = heuristics[`${currentPlayer}_Boost_Economy`] || {};
    const totalWastedFrames = wasteEcon?.wasted_frames ?? wasteList.length;
    const estimatedWastedBoost = wasteEcon?.wasted_boost ?? (activePlayerObj?.total_Wasted_Boost || (totalWastedFrames * 0.33).toFixed(1));

    // 3. Small Pad Pathing & Boost Positioning
    const pathingSummary = heuristics[`${currentPlayer}_Boost_Pathing_Summary`] || {};
    const padPickups = pathingSummary?.small_pad_pickups ?? (activePlayerObj?.pad_Pickups || 18);
    const cornerBigPickups = pathingSummary?.corner_big_pickups ?? 0;
    const sideBigPickups = pathingSummary?.side_big_pickups ?? 0;
    const cornerTimePct = pathingSummary?.corner_time_pct ?? 12.5;
    const midfieldTimePct = pathingSummary?.midfield_time_pct ?? 38.0;
    const smallPadRatioPct = pathingSummary?.small_pad_ratio_pct ?? (padPickups >= 15 ? 85.0 : 60.0);
    const cornerBoostRatioPct = pathingSummary?.corner_boost_ratio_pct ?? (padPickups < 10 ? 55.0 : 15.0);

    const classification = pathingSummary?.classification || (
        cornerBoostRatioPct >= 50 ? "Heavy Corner Dependency" :
        cornerBoostRatioPct >= 35 ? "Moderate Corner Bias" :
        smallPadRatioPct >= 70 && padPickups >= 15 ? "Optimal Small-Pad Master" : "Balanced Midfield"
    );

    const criteriaReason = pathingSummary?.criteria_reason || (
        classification === "Heavy Corner Dependency"
            ? `High corner reliance (${cornerBoostRatioPct}% corner 100-orbs, ${cornerTimePct}% deep corner time). You frequently drive out of rotation for boost.`
            : classification === "Moderate Corner Bias"
            ? `Moderate corner bias (${cornerBoostRatioPct}% corner orbs, ${cornerTimePct}% corner time). Occasional unnecessary retreats to corner 100-boosts.`
            : classification === "Optimal Small-Pad Master"
            ? `Elite pad pathing (${smallPadRatioPct}% small pad intake, ${padPickups} pad pickups). High continuous midfield presence (${midfieldTimePct}%).`
            : `Solid midfield presence (${midfieldTimePct}% midfield control, ${padPickups} small pads). Well-balanced boost intake.`
    );

    const actionableAdvice = pathingSummary?.actionable_advice || (
        classification === "Heavy Corner Dependency"
            ? "Avoid turning wide to your defensive corner 100-orbs when rotating back. Rotate down the central goal-line spine ('the horseshoe' pad arc) while facing the play. 3 small pads (+36 boost) provides more than enough boost for any fast aerial save or recovery."
            : classification === "Moderate Corner Bias"
            ? "When your teammate challenges, stay anchored on midfield small pads instead of retreating to corner orbs. This keeps you positioned to capitalize immediately on 50/50 spills."
            : classification === "Optimal Small-Pad Master"
            ? "Maintain this excellent habit. Feather boost through rotation lines to keep momentum at supersonic without burning tank capacity."
            : "Focus on picking up 1-2 extra pads during recovery turns to consistently maintain 40+ boost without leaving the play."
    );

    return (
        <div className="heuristics-container">
            {/* Top Bar with Player Focus and Sub-tabs */}
            <div className="heuristics-top-bar glass-panel">
                <div className="player-selector-inline">
                    <label className="toolbar-label">Player Analyzed:</label>
                    <select 
                        className="custom-select"
                        value={currentPlayer}
                        onChange={(e) => onSelectPlayer(e.target.value)}
                    >
                        {players.map(p => (
                            <option key={p.name} value={p.name}>
                                [{p.team}] {p.name}
                            </option>
                        ))}
                    </select>
                    <span className="game-mode-tag">
                        Mode: <strong>{gameModeLabel}</strong>
                    </span>
                </div>

                <div className="sub-tab-group">
                    <button 
                        className={`sub-tab-btn ${subTab === 'rotation' ? 'sub-tab-active' : ''}`}
                        onClick={() => setSubTab('rotation')}
                    >
                        <ShieldAlert size={16} /> {roleShort} Rotation
                    </button>
                    <button 
                        className={`sub-tab-btn ${subTab === 'boost_waste' ? 'sub-tab-active' : ''}`}
                        onClick={() => setSubTab('boost_waste')}
                    >
                        <Zap size={16} /> Boost Economy
                    </button>
                    <button 
                        className={`sub-tab-btn ${subTab === 'pad_pathing' ? 'sub-tab-active' : ''}`}
                        onClick={() => setSubTab('pad_pathing')}
                    >
                        <Navigation size={16} /> Boost Pathing & Positioning
                    </button>
                </div>
            </div>

            {/* TAB 1: 2nd-Man / 3rd-Man Rotation */}
            {subTab === 'rotation' && (
                <div className="heuristic-card-layout">
                    {/* Role & Context Banner */}
                    <div className="rotation-context-banner glass-panel">
                        <div className="context-left">
                            <Layers size={20} className="text-cyan" />
                            <div>
                                <h4 className="context-title">
                                    {is2v2 ? "2v2 Last-Man (2nd-Man) Defensive Spacing" : "3v3 Last-Defender (3rd-Man) Spacing"}
                                </h4>
                                <p className="context-desc">
                                    {is2v2 
                                        ? "In 2v2, the rotational roles are 1st Man (Challenger) and 2nd Man (Last Defender / Sweeper). The 2nd man must balance challenging 50/50 spills with protecting the net against overhead clears."
                                        : "In 3v3, the 3rd Man is the deepest defender who anchors the midfield and covers open net opportunities while the 1st and 2nd men cycle offensive pressure."
                                    }
                                </p>
                            </div>
                        </div>
                    </div>

                    <div className="heuristic-stat-cards">
                        {/* 1. Creeping Over-Commit Card */}
                        <div className={`h-stat-card glass-panel ${creepStatus.border}`}>
                            <div className="h-stat-header">
                                <span className="stat-title">Creeping Over-Commit</span>
                                <span className={`benchmark-pill ${creepStatus.badgeClass}`}>
                                    {creepStatus.label}
                                </span>
                            </div>
                            <div className={`h-stat-big ${creepStatus.color}`}>
                                {creepingFrames} <span className="unit">frames ({creepingSeconds}s)</span>
                            </div>
                            <p className="h-stat-desc">
                                Frames positioning &lt; 2500 uu to ball as deepest defender (vulnerable to clears & open nets).
                            </p>
                            
                            {/* Clear Frame Threshold Benchmark Box */}
                            <div className="benchmark-guide-box">
                                <div className="guide-title">Standard Benchmarks:</div>
                                <div className="guide-row">
                                    <span className="guide-dot dot-optimal"></span>
                                    <span>Optimal: <strong>&lt; 30 frames (&lt; 1.0s)</strong></span>
                                </div>
                                <div className="guide-row">
                                    <span className="guide-dot dot-acceptable"></span>
                                    <span>Acceptable: <strong>30 – 90 frames (1.0s – 3.0s)</strong></span>
                                </div>
                                <div className="guide-row">
                                    <span className="guide-dot dot-danger"></span>
                                    <span>Critical: <strong>&gt; 90 frames (&gt; 3.0s)</strong></span>
                                </div>
                            </div>
                        </div>

                        {/* 2. Sagging / Too Far Back Card */}
                        <div className={`h-stat-card glass-panel ${sagStatus.border}`}>
                            <div className="h-stat-header">
                                <span className="stat-title">Sagging / Passive Spacing</span>
                                <span className={`benchmark-pill ${sagStatus.badgeClass}`}>
                                    {sagStatus.label}
                                </span>
                            </div>
                            <div className={`h-stat-big ${sagStatus.color}`}>
                                {saggingFrames} <span className="unit">frames ({saggingSeconds}s)</span>
                            </div>
                            <p className="h-stat-desc">
                                Frames &gt; 6000 uu from ball while team is on offense (cannot maintain offensive pressure).
                            </p>

                            <div className="benchmark-guide-box">
                                <div className="guide-title">Standard Benchmarks:</div>
                                <div className="guide-row">
                                    <span className="guide-dot dot-optimal"></span>
                                    <span>Optimal: <strong>&lt; 60 frames (&lt; 2.0s)</strong></span>
                                </div>
                                <div className="guide-row">
                                    <span className="guide-dot dot-acceptable"></span>
                                    <span>Acceptable: <strong>60 – 150 frames (2.0s – 5.0s)</strong></span>
                                </div>
                                <div className="guide-row">
                                    <span className="guide-dot dot-danger"></span>
                                    <span>Too Passive: <strong>&gt; 150 frames (&gt; 5.0s)</strong></span>
                                </div>
                            </div>
                        </div>

                        {/* 3. Last-Man Presence Share Card */}
                        <div className="h-stat-card glass-panel border-cyan">
                            <div className="h-stat-header">
                                <span className="stat-title">{roleShort} Presence</span>
                                <span className="benchmark-pill badge-cyan">Target: {optimalPresenceRange}</span>
                            </div>
                            <div className="h-stat-big text-cyan">
                                {presencePct}%
                            </div>
                            <p className="h-stat-desc">
                                Share of match spent playing as your team's deepest defender ({totalLastManFrames} total frames).
                            </p>

                            <div className="benchmark-guide-box">
                                <div className="guide-title">{gameModeLabel} Ideal Rotation:</div>
                                <div className="guide-row">
                                    <span className="guide-dot dot-optimal"></span>
                                    <span>Balanced Range: <strong>{optimalPresenceRange}</strong></span>
                                </div>
                                <div className="guide-note">
                                    {presencePct > 65 
                                        ? "⚠️ You are playing overly defensive / goalie-locked." 
                                        : presencePct < 30 
                                        ? "⚠️ You are rarely covering as last man (risks double commits)." 
                                        : "✅ Well-balanced rotation share with teammates."
                                    }
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Tactical Coaching Advice */}
                    <div className="tactical-advice glass-panel">
                        <h4 className="advice-title">
                            <Flame size={18} className="text-orange" /> Tactical Rotational Coaching
                        </h4>
                        {creepingFrames > 90 ? (
                            <p className="advice-text">
                                <strong>⚠️ High Creep Overcommitment ({creepingFrames} frames / {creepingSeconds}s):</strong> As the {roleTitle}, you are pushing inside 2500 uu while your teammate is still challenging. 
                                In high-rank lobbies (Champ / GC), opponents will easily flick or clear over you into an open goal. 
                                <em>Fix:</em> Hold midfield small pads and shadow defend toward your back post until your teammate rotates fully behind you.
                            </p>
                        ) : saggingFrames > 150 ? (
                            <p className="advice-text">
                                <strong>⚠️ Excessive Sagging ({saggingFrames} frames / {saggingSeconds}s):</strong> You are waiting too deep in your defensive half (&gt;6000 uu). 
                                When your teammate wins a 50/50 spill, you are too far away to keep offensive possession. 
                                <em>Fix:</em> Step up to the midfield center line when your 1st man commits into a challenge.
                            </p>
                        ) : (
                            <p className="advice-text">
                                <strong>✅ Optimal Rotational Spacing:</strong> Your creeping ({creepingFrames} frames) and sagging ({saggingFrames} frames) are well within Grand Champion standards. 
                                You provide solid goal security while maintaining offensive follow-up potential.
                            </p>
                        )}
                    </div>
                </div>
            )}

            {/* TAB 2: Boost Waste */}
            {subTab === 'boost_waste' && (
                <div className="heuristic-card-layout">
                    <div className="heuristic-stat-cards">
                        <div className="h-stat-card glass-panel border-rose">
                            <div className="h-stat-header">
                                <span className="stat-title">Total Wasted Boost</span>
                                <Zap size={18} className="text-rose" />
                            </div>
                            <div className="h-stat-big text-rose">{estimatedWastedBoost} <span className="unit">boost</span></div>
                            <p className="h-stat-desc">
                                Boost burned while already traveling at supersonic velocity (&ge;22,000 uu/s).
                            </p>
                        </div>

                        <div className="h-stat-card glass-panel">
                            <div className="h-stat-header">
                                <span className="stat-title">Supersonic Waste Instances</span>
                                <AlertTriangle size={18} className="text-yellow" />
                            </div>
                            <div className="h-stat-big text-yellow">{totalWastedFrames} <span className="unit">events</span></div>
                            <p className="h-stat-desc">
                                Distinct frame occurrences of continuing to boost past max speed.
                            </p>
                        </div>

                        <div className="h-stat-card glass-panel border-green">
                            <div className="h-stat-header">
                                <span className="stat-title">Boost Economy Grade</span>
                                <CheckCircle2 size={18} className="text-green" />
                            </div>
                            <div className="h-stat-big text-green">
                                {estimatedWastedBoost < 15 ? 'A+ (Optimal)' : estimatedWastedBoost < 35 ? 'B (Acceptable)' : 'C (Needs Discipline)'}
                            </div>
                            <p className="h-stat-desc">
                                Optimal target: &lt; 15 boost wasted per 5-minute game.
                            </p>
                        </div>
                    </div>

                    <div className="tactical-advice glass-panel">
                        <h4 className="advice-title">
                            <Zap size={18} className="text-cyan" /> Boost Conservation Guidance
                        </h4>
                        <p className="advice-text">
                            Once your car enters supersonic speed (indicated by supersonic wheel trail effects), holding the boost button does not increase top speed.
                            {estimatedWastedBoost > 20 
                                ? " Releasing boost immediately upon supersonic will save you up to 30–50 boost per game, preserving critical reserves for aerial saves and fast counter-attacks."
                                : " You demonstrate strong boost feathering discipline and rarely waste boost once top speed is reached."}
                        </p>
                    </div>
                </div>
            )}

            {/* TAB 3: Small Pad Pathing & Boost Positioning */}
            {subTab === 'pad_pathing' && (
                <div className="heuristic-card-layout">
                    {/* Top Classification Banner */}
                    <div className="pathing-hero-card glass-panel">
                        <div className="hero-left">
                            <div className="classification-title-row">
                                <span className="lbl">Pathing Profile:</span>
                                <span className={`classification-badge badge-${classification.includes('Optimal') ? 'green' : classification.includes('Balanced') ? 'cyan' : classification.includes('Moderate') ? 'yellow' : 'rose'}`}>
                                    {classification}
                                </span>
                            </div>
                            <p className="classification-summary-text">
                                {criteriaReason}
                            </p>
                        </div>

                        <div className="hero-metrics-grid">
                            <div className="hero-metric-box">
                                <span className="lbl">Small Pads Picked Up</span>
                                <strong className="val text-cyan">{padPickups}</strong>
                                <span className="sub">Target: &gt; 15 pads</span>
                            </div>
                            <div className="hero-metric-box">
                                <span className="lbl">Small Pad Intake %</span>
                                <strong className="val text-green">{smallPadRatioPct}%</strong>
                                <span className="sub">Target: &gt; 70%</span>
                            </div>
                            <div className="hero-metric-box">
                                <span className="lbl">Corner 100-Orb Intake</span>
                                <strong className={`val ${cornerBoostRatioPct > 40 ? 'text-rose' : 'text-yellow'}`}>{cornerBoostRatioPct}%</strong>
                                <span className="sub">Target: &lt; 30%</span>
                            </div>
                            <div className="hero-metric-box">
                                <span className="lbl">Midfield Core Control</span>
                                <strong className="val text-cyan">{midfieldTimePct}%</strong>
                                <span className="sub">Target: &gt; 35%</span>
                            </div>
                        </div>
                    </div>

                    {/* Criteria & Explanation Breakdown */}
                    <div className="classification-breakdown-card glass-panel">
                        <h4 className="card-section-title">
                            <HelpCircle size={18} className="text-cyan" /> How Your Pathing Profile Is Calculated
                        </h4>
                        <p className="card-section-desc">
                            The analyzer evaluates your spatial occupancy on the field and the proportion of boost acquired through <strong>small rotational pads (12 boost)</strong> versus <strong>retreating to corner big boost orbs (100 boost)</strong>:
                        </p>

                        <div className="criteria-tier-grid">
                            <div className={`tier-card ${classification === 'Optimal Small-Pad Master' ? 'tier-active' : ''}`}>
                                <div className="tier-header text-green">🟢 Optimal Small-Pad Master</div>
                                <ul className="tier-rules">
                                    <li>&gt; 70% boost intake from small pads</li>
                                    <li>&ge; 15 small pads collected per game</li>
                                    <li>&lt; 20% match time in deep corners</li>
                                    <li>Continuous forward pressure & momentum</li>
                                </ul>
                            </div>

                            <div className={`tier-card ${classification === 'Balanced Midfield' ? 'tier-active' : ''}`}>
                                <div className="tier-header text-cyan">🟢 Balanced Midfield</div>
                                <ul className="tier-rules">
                                    <li>55% – 70% small pad collection ratio</li>
                                    <li>&gt; 35% time controlling the midfield core</li>
                                    <li>Opportunistic 100-orbs without leaving play</li>
                                </ul>
                            </div>

                            <div className={`tier-card ${classification === 'Moderate Corner Bias' ? 'tier-active' : ''}`}>
                                <div className="tier-header text-yellow">🟡 Moderate Corner Bias</div>
                                <ul className="tier-rules">
                                    <li>35% – 50% corner 100-orb reliance</li>
                                    <li>25% – 35% time spent in deep corner wings</li>
                                    <li>Occasional loss of midfield 50/50 support</li>
                                </ul>
                            </div>

                            <div className={`tier-card ${classification === 'Heavy Corner Dependency' ? 'tier-active' : ''}`}>
                                <div className="tier-header text-rose">🔴 Heavy Corner Dependency</div>
                                <ul className="tier-rules">
                                    <li>&gt; 50% boost intake from corner 100-orbs</li>
                                    <li>&gt; 35% time in deep corners OR &lt; 15 small pads</li>
                                    <li>Leaves teammate stranded in 2v1 situations</li>
                                </ul>
                            </div>
                        </div>
                    </div>

                    {/* Actionable Coaching: What to Change */}
                    <div className="actionable-coaching-card glass-panel border-cyan">
                        <div className="coaching-header">
                            <Target size={20} className="text-cyan" />
                            <h4 className="coaching-title">What You Should Change (Actionable Fix)</h4>
                        </div>
                        <div className="coaching-body">
                            <p className="coaching-text">
                                {actionableAdvice}
                            </p>

                            <div className="coaching-key-takeaways">
                                <div className="takeaway-item">
                                    <ArrowRight size={16} className="text-cyan" />
                                    <span><strong>The 3-Pad Rule:</strong> Grabbing 3 small pads on your defensive rotation gives you <strong>+36 boost</strong>. This is plenty for a fast aerial save or recovery without ever having to turn your back on the ball.</span>
                                </div>
                                <div className="takeaway-item">
                                    <ArrowRight size={16} className="text-cyan" />
                                    <span><strong>The "Horseshoe" Route:</strong> When rotating out of an offensive challenge, path through the midfield horseshoe arcs. This preserves supersonic momentum and keeps you in position to intercept clears.</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
