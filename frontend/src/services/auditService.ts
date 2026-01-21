import api from '@/lib/api';

export interface AuditLog {
    id: number;
    username: string;
    action: string;
    target_table: string;
    timestamp: string;
}

export const getAuditLogs = async () => {
    const response = await api.get<AuditLog[]>('/audit');
    return response.data;
};
