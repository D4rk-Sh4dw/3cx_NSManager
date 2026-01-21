import api from '@/lib/api';

export interface Plan {
    id: number;
    start_date: string;
    end_date: string;
    person_id: number;
    confirmed: boolean;
    person?: {
        first_name: string;
        last_name: string;
    };
}

export interface PlanCreate {
    start_date: string;
    end_date: string;
    person_id: number;
}

export const getPlans = async (start?: string, end?: string) => {
    const response = await api.get<Plan[]>('/plans', { params: { start, end } });
    return response.data;
};

export const createPlan = async (data: PlanCreate) => {
    const response = await api.post<Plan>('/plans', data);
    return response.data;
};

export const updatePlan = async (id: number, data: Partial<PlanCreate>) => {
    const response = await api.put<Plan>(`/plans/${id}`, data);
    return response.data;
};

export const confirmPlan = async (id: number) => {
    const response = await api.post(`/plans/${id}/confirm`);
    return response.data;
};

export const deletePlan = async (id: number) => {
    const response = await api.delete(`/plans/${id}`);
    return response.data;
};

export const deletePlan = async (id: number) => {
    // Not implemented in backend yet, but UI might need it?
    // Let's implement delete in backend later.
    return;
};
