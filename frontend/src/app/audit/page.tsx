"use client";

import { useEffect, useState } from 'react';
import Navbar from '@/components/Navbar';
import { getAuditLogs, AuditLog } from '@/services/auditService';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { motion } from "framer-motion";
import { FileClock, User, Hash, Activity } from "lucide-react";

export default function AuditPage() {
    const [logs, setLogs] = useState<AuditLog[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (!token) {
            router.push('/login');
            return;
        }
        loadLogs();
    }, []);

    const loadLogs = async () => {
        try {
            const data = await getAuditLogs();
            setLogs(data);
        } catch (e) {
            console.error("Failed to load audit logs");
        } finally {
            setLoading(false);
        }
    };

    return (
        <main className="min-h-screen bg-background">
            <Navbar />
            <div className="container mx-auto mt-8 p-4">
                <motion.div
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                >
                    <Card>
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2"><FileClock /> System Audit Log</CardTitle>
                            <CardDescription>Track all changes and actions within the system.</CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="rounded-md border">
                                <table className="w-full text-sm text-left">
                                    <thead className="bg-muted/50 text-muted-foreground">
                                        <tr>
                                            <th className="px-4 py-3 font-medium">Time</th>
                                            <th className="px-4 py-3 font-medium">User</th>
                                            <th className="px-4 py-3 font-medium">Action</th>
                                            <th className="px-4 py-3 font-medium">Target</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y">
                                        {logs.map((log, index) => (
                                            <motion.tr
                                                key={log.id}
                                                initial={{ opacity: 0, x: -10 }}
                                                animate={{ opacity: 1, x: 0 }}
                                                transition={{ delay: index * 0.05 }}
                                                className="hover:bg-muted/50 transition-colors"
                                            >
                                                <td className="px-4 py-3 whitespace-nowrap text-muted-foreground">
                                                    {new Date(log.timestamp).toLocaleString()}
                                                </td>
                                                <td className="px-4 py-3 font-medium flex items-center gap-2">
                                                    <User size={14} className="text-muted-foreground" />
                                                    {log.username || 'System'}
                                                </td>
                                                <td className="px-4 py-3">
                                                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ring-1 ring-inset ${log.action === 'CREATE' ? 'bg-green-50 text-green-700 ring-green-600/20 dark:bg-green-900/10 dark:text-green-400' :
                                                        log.action === 'DELETE' ? 'bg-red-50 text-red-700 ring-red-600/20 dark:bg-red-900/10 dark:text-red-400' :
                                                            log.action === 'UPDATE' ? 'bg-blue-50 text-blue-700 ring-blue-600/20 dark:bg-blue-900/10 dark:text-blue-400' :
                                                                log.action === 'CONFIRM' ? 'bg-purple-50 text-purple-700 ring-purple-600/20 dark:bg-purple-900/10 dark:text-purple-400' :
                                                                    'bg-gray-50 text-gray-600 ring-gray-500/10 dark:bg-gray-900/10 dark:text-gray-400'
                                                        }`}>
                                                        {log.action}
                                                    </span>
                                                </td>
                                                <td className="px-4 py-3 text-muted-foreground font-mono text-xs">
                                                    {log.target_table}
                                                </td>
                                            </motion.tr>
                                        ))}
                                        {!loading && logs.length === 0 && (
                                            <tr>
                                                <td colSpan={4} className="px-4 py-8 text-center text-muted-foreground">No logs found.</td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </CardContent>
                    </Card>
                </motion.div>
            </div>
        </main>
    );
}
