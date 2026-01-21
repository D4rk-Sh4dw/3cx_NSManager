"use client";
import { useEffect, useState } from 'react';
import Navbar from '@/components/Navbar';
import { getAuditLogs, AuditLog } from '@/services/auditService';

export default function AuditPage() {
    const [logs, setLogs] = useState<AuditLog[]>([]);

    useEffect(() => {
        loadLogs();
    }, []);

    const loadLogs = async () => {
        try {
            const data = await getAuditLogs();
            setLogs(data);
        } catch (e) {
            console.error("Failed to load audit logs");
        }
    };

    return (
        <main>
            <Navbar />
            <div className="container mx-auto mt-5">
                <h1 className="text-2xl font-bold mb-4">System Audit Log</h1>
                <div className="bg-white shadow overflow-hidden sm:rounded-lg">
                    <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Time</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Action</th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Target</th>
                            </tr>
                        </thead>
                        <tbody className="bg-white divide-y divide-gray-200">
                            {logs.map((log) => (
                                <tr key={log.id}>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{new Date(log.timestamp).toLocaleString()}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">{log.username || 'System'}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{log.action}</td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{log.target_table}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </main>
    );
}
