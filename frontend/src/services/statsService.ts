import api from '@/lib/api';

export interface StatUser {
    user_id: number;
    first_name: string;
    last_name: string;
    username: string;
    total_days: number;
    total_entries: number;
}

export interface StatsResponse {
    month: {
        name: string;
        year: number;
        data: StatUser[];
    };
    year: {
        year: number;
        data: StatUser[];
    };
}

export const getStatsOverview = async (): Promise<StatsResponse> => {
    const response = await api.get('/stats/overview');
    return response.data;
};
