import api from '@/lib/api';

export const login = async (username: string, password: string) => {
    const params = new URLSearchParams();
    params.append('username', username);
    params.append('password', password);

    const response = await api.post('/auth/token', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
    return response.data;
};

export interface AuthConfig {
    local_login_enabled: boolean;
    oidc_enabled: boolean;
    oidc_provider_name: string;
}

export const getAuthConfig = async (): Promise<AuthConfig> => {
    const response = await api.get('/auth/config');
    return response.data;
};

/** Full page navigation - the OIDC flow runs through browser redirects. */
export const startSsoLogin = () => {
    const base = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    window.location.href = `${base}/auth/oidc/login`;
};

/**
 * Picks up the token the SSO callback left in a short-lived httpOnly cookie.
 * withCredentials so the cookie travels when frontend and API are not same-origin.
 */
export const completeSsoLogin = async () => {
    const response = await api.post('/auth/oidc/complete', {}, { withCredentials: true });
    return response.data;
};

export const logout = () => {
    localStorage.removeItem('token');
    window.location.href = '/login';
};

export const changePassword = async (oldPassword: string, newPassword: string) => {
    const response = await api.post('/auth/change-password', {
        old_password: oldPassword,
        new_password: newPassword
    });
    return response.data;
};
