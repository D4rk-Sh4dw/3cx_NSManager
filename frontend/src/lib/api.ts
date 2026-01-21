import axios from 'axios';

const api = axios.create({
    baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
});

api.interceptors.request.use((config) => {
    console.log(`API REQUEST: ${config.method?.toUpperCase()} ${config.url}`, config.data);
    const token = localStorage.getItem('token');
    if (token) {
        config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
});

api.interceptors.response.use(
    (response) => {
        console.log(`API SUCCESS: ${response.status} ${response.config.url}`);
        return response;
    },
    (error) => {
        if (error.response) {
            console.error('API ERROR RESPONSE:', error.response.status, error.response.data);
        } else if (error.request) {
            console.error('API NO RESPONSE:', error.request);
        } else {
            console.error('API SETUP ERROR:', error.message);
        }
        return Promise.reject(error);
    }
);

export default api;
