import api from '@/lib/api';

export interface User {
    id: number;
    username: string;
    email: string;
    first_name: string;
    last_name: string;
    phone_number: string | null;
    role: string;
    is_active: boolean;
    can_take_duty: boolean;
    created_at: string;
    last_login: string | null;
}

export interface UserCreate {
    username: string;
    email: string;
    password: string;
    first_name: string;
    last_name: string;
    phone_number?: string;
    role: string;
    is_active?: boolean;
    can_take_duty?: boolean;
}

export interface UserUpdate {
    email?: string;
    first_name?: string;
    last_name?: string;
    phone_number?: string;
    role?: string;
    is_active?: boolean;
    can_take_duty?: boolean;
    password?: string;
}

export const getUsers = async (): Promise<User[]> => {
    const response = await api.get('/users');
    return response.data;
};

export const getDutyEligibleUsers = async (): Promise<User[]> => {
    const response = await api.get('/users/duty-eligible');
    return response.data;
};

export const getUser = async (id: number): Promise<User> => {
    const response = await api.get(`/users/${id}`);
    return response.data;
};

export const createUser = async (data: UserCreate): Promise<User> => {
    const response = await api.post('/users', data);
    return response.data;
};

export const updateUser = async (id: number, data: UserUpdate): Promise<User> => {
    const response = await api.put(`/users/${id}`, data);
    return response.data;
};

export const deleteUser = async (id: number): Promise<void> => {
    await api.delete(`/users/${id}`);
};
