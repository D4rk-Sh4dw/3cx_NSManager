"use client";
import React, { useEffect, useState } from 'react';
import { getStatsOverview, StatsResponse } from '@/services/statsService';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { BarChart, Calendar, Trophy } from "lucide-react";

export default function StatsPage() {
    const [stats, setStats] = useState<StatsResponse | null>(null);

    useEffect(() => {
        getStatsOverview().then(setStats).catch(console.error);
    }, []);

    if (!stats) return <div className="p-8">Lade Statistik...</div>;

    const renderTable = (data: any[]) => (
        <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
                <thead className="bg-muted text-muted-foreground uppercase font-medium">
                    <tr>
                        <th className="px-4 py-3 rounded-tl-lg">Mitarbeiter</th>
                        <th className="px-4 py-3 text-right">Tage</th>
                        <th className="px-4 py-3 text-right rounded-tr-lg">Dienste</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-border">
                    {data.sort((a, b) => b.total_days - a.total_days).map((u) => (
                        <tr key={u.user_id} className="hover:bg-muted/50 transition-colors">
                            <td className="px-4 py-3 font-medium">{u.first_name} {u.last_name}</td>
                            <td className="px-4 py-3 text-right font-bold">{u.total_days}</td>
                            <td className="px-4 py-3 text-right">{u.total_entries}</td>
                        </tr>
                    ))}
                    {data.length === 0 && (
                        <tr>
                            <td colSpan={3} className="px-4 py-8 text-center text-muted-foreground">Keine Daten vorhanden.</td>
                        </tr>
                    )}
                </tbody>
            </table>
        </div>
    );

    return (
        <div className="space-y-6">
            <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
                <BarChart className="w-8 h-8" /> Statistik
            </h1>

            <div className="grid gap-6 md:grid-cols-2">
                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Calendar className="w-5 h-5 text-primary" />
                            Aktueller Monat ({stats.month.name} {stats.month.year})
                        </CardTitle>
                        <CardDescription>Übersicht der geleisteten Dienste im aktuellen Monat.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        {renderTable(stats.month.data)}
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Trophy className="w-5 h-5 text-yellow-500" />
                            Jahresübersicht ({stats.year.year})
                        </CardTitle>
                        <CardDescription>Gesamtstatistik für das laufende Jahr.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        {renderTable(stats.year.data)}
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
