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
