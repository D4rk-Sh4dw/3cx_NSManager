import api from '@/lib/api';

export const exportPlans = async (month?: number, year?: number): Promise<void> => {
    let url = '/export/plans';
    if (month && year) {
        url += `?month=${month}&year=${year}`;
    }
    const response = await api.get(url, {
        responseType: 'blob'
    });

    const downloadUrl = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = downloadUrl;
    const dateStr = month && year ? `${year}-${month.toString().padStart(2, '0')}` : new Date().toISOString().slice(0, 10);
    link.setAttribute('download', `notfallplan_export_${dateStr}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
};

export const exportPlansPdf = async (month?: number, year?: number): Promise<void> => {
    let url = '/export/plans/pdf';
    if (month && year) {
        url += `?month=${month}&year=${year}`;
    }
    const response = await api.get(url, {
        responseType: 'blob'
    });

    const downloadUrl = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = downloadUrl;
    const dateStr = month && year ? `${year}-${month.toString().padStart(2, '0')}` : new Date().toISOString().slice(0, 10);
    link.setAttribute('download', `notfallplan_export_${dateStr}.pdf`);
    document.body.appendChild(link);
    link.click();
    link.remove();
};

export const exportAudit = async (): Promise<void> => {
    const response = await api.get('/export/audit', {
        responseType: 'blob'
    });

    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `audit_export_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    link.remove();
};
