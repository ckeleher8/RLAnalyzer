// src/services/api.js
import axios from 'axios';

// The C# .NET Gateway API
const API_BASE_URL = 'http://localhost:5000/api/replay';

export const uploadReplay = async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await axios.post(`${API_BASE_URL}/upload`, formData, {
        headers: {
            'Content-Type': 'multipart/form-data',
        },
    });
    return response.data; // { id, matchId, status, message }
};

export const getMatchStatus = async (id) => {
    const response = await axios.get(`${API_BASE_URL}/${id}/status`);
    return response.data; // { id, matchId, status, message }
};

export const getMatchById = async (id) => {
    const response = await axios.get(`${API_BASE_URL}/${id}`);
    return response.data; // Full MatchResponseDto
};

export const getRecentMatches = async (count = 20) => {
    const response = await axios.get(`${API_BASE_URL}?count=${count}`);
    return response.data; // List<MatchResponseDto>
};

export const checkHealth = async () => {
    try {
        const response = await axios.get('http://localhost:5000/api/health', { timeout: 2000 });
        return response.status === 200;
    } catch {
        return false;
    }
};