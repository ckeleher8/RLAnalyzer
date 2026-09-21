// src/App.jsx
import React, { useState, useEffect } from 'react';
import Navbar from './components/Navbar';
import ReplayUpload from './components/ReplayUpload';
import MatchOverview from './components/MatchOverview';
import ActionValueTimeline from './components/ActionValueTimeline';
import HeuristicsCenter from './components/HeuristicsCenter';
import MatchHistoryModal from './components/MatchHistoryModal';
import { checkHealth } from './services/api';
import { LayoutDashboard, Activity, ShieldAlert } from 'lucide-react';
import './App.css';

export default function App() {
    const [matchData, setMatchData] = useState(null);
    const [selectedPlayer, setSelectedPlayer] = useState('');
    const [activeTab, setActiveTab] = useState('overview'); // overview, timeline, heuristics
    const [isHistoryOpen, setIsHistoryOpen] = useState(false);
    const [isGatewayOnline, setIsGatewayOnline] = useState(false);

    useEffect(() => {
        const verifyHealth = async () => {
            const healthy = await checkHealth();
            setIsGatewayOnline(healthy);
        };
        verifyHealth();
        const interval = setInterval(verifyHealth, 8000);
        return () => clearInterval(interval);
    }, []);

    const handleAnalysisComplete = (data) => {
        setMatchData(data);
        if (data.players && data.players.length > 0) {
            setSelectedPlayer(data.players[0].name);
        }
        setActiveTab('overview');
    };

    const handleNewUpload = () => {
        setMatchData(null);
        setActiveTab('overview');
    };

    return (
        <div className="app-wrapper">
            <Navbar 
                onOpenHistory={() => setIsHistoryOpen(true)}
                onNewUpload={handleNewUpload}
                isGatewayOnline={isGatewayOnline}
                activeMatch={matchData}
            />

            <main className="main-content">
                {!matchData ? (
                    <ReplayUpload onAnalysisComplete={handleAnalysisComplete} />
                ) : (
                    <div className="dashboard-content">
                        {/* Tab Switcher */}
                        <div className="dashboard-nav-tabs">
                            <button 
                                className={`dash-tab-btn ${activeTab === 'overview' ? 'dash-tab-active' : ''}`}
                                onClick={() => setActiveTab('overview')}
                            >
                                <LayoutDashboard size={18} /> Match Overview
                            </button>
                            <button 
                                className={`dash-tab-btn ${activeTab === 'timeline' ? 'dash-tab-active' : ''}`}
                                onClick={() => setActiveTab('timeline')}
                            >
                                <Activity size={18} /> ML Impact Timeline
                            </button>
                            <button 
                                className={`dash-tab-btn ${activeTab === 'heuristics' ? 'dash-tab-active' : ''}`}
                                onClick={() => setActiveTab('heuristics')}
                            >
                                <ShieldAlert size={18} /> Heuristics Center
                            </button>
                        </div>

                        {/* Active Tab View */}
                        {activeTab === 'overview' && (
                            <MatchOverview 
                                matchData={matchData} 
                                onSelectTab={setActiveTab}
                                onSelectPlayer={setSelectedPlayer}
                            />
                        )}

                        {activeTab === 'timeline' && (
                            <ActionValueTimeline 
                                matchData={matchData} 
                                selectedPlayer={selectedPlayer}
                                onSelectPlayer={setSelectedPlayer}
                            />
                        )}

                        {activeTab === 'heuristics' && (
                            <HeuristicsCenter 
                                matchData={matchData} 
                                selectedPlayer={selectedPlayer}
                                onSelectPlayer={setSelectedPlayer}
                            />
                        )}
                    </div>
                )}
            </main>

            <MatchHistoryModal 
                isOpen={isHistoryOpen}
                onClose={() => setIsHistoryOpen(false)}
                onSelectMatch={handleAnalysisComplete}
            />
        </div>
    );
}