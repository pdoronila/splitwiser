// API configuration with automatic token refresh
import { refreshAccessToken } from './AuthContext';

const API_BASE_URL = 'http://localhost:8000';

// Create a fetch wrapper with automatic token refresh
export const fetchWithAuth = async (url: string, options: RequestInit = {}): Promise<Response> => {
    let token = localStorage.getItem('token');

    // Add authorization header if token exists
    const headers = {
        ...options.headers,
        ...(token && { 'Authorization': `Bearer ${token}` })
    };

    // Make the request
    let response = await fetch(url, {
        ...options,
        headers
    });

    // If 401, try to refresh and retry once
    if (response.status === 401) {
        const newToken = await refreshAccessToken();

        if (newToken) {
            // Retry with new token
            response = await fetch(url, {
                ...options,
                headers: {
                    ...options.headers,
                    'Authorization': `Bearer ${newToken}`
                }
            });
        } else {
            // Refresh failed, redirect to login
            window.location.href = '/login';
        }
    }

    return response;
};

export { API_BASE_URL };
