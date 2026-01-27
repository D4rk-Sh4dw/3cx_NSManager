"use client";
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { exportPlans, exportAudit, exportPlansPdf } from '@/services/exportService';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Download, FileSpreadsheet, FileClock } from 'lucide-react';
import { motion } from 'framer-motion';

export default function ExportPage() {
    const router = useRouter();
    const [selectedMonth, setSelectedMonth] = useState(new Date().getMonth() + 1);
    const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
    const [loadingPlans, setLoadingPlans] = useState(false);
    const [loadingAudit, setLoadingAudit] = useState(false);

    useEffect(() => {
        const token = localStorage.getItem('token');
        const role = localStorage.getItem('role');
        if (!token) {
            router.push('/login');
            return;
        }
        if (role !== 'admin' && role !== 'buchhaltung') {
            router.push('/calendar');
            return;
        }
    }, [router]);

    const handleExportPlans = async () => {
        setLoadingPlans(true);
        try {
            await exportPlans(selectedMonth === 0 ? undefined : selectedMonth, selectedYear);
        } catch (error) {
            console.error('Export failed:', error);
            alert('Export fehlgeschlagen');
        } finally {
            setLoadingPlans(false);
        }
    };

    const handleExportPlansPdf = async () => {
        setLoadingPlans(true);
        try {
            await exportPlansPdf(selectedMonth === 0 ? undefined : selectedMonth, selectedYear);
        } catch (error) {
            console.error('Export failed:', error);
            alert('Export fehlgeschlagen');
        } finally {
            setLoadingPlans(false);
        }
    };

    const handleExportAudit = async () => {
        setLoadingAudit(true);
        try {
            await exportAudit();
        } catch (error) {
            console.error('Export failed:', error);
            alert('Export fehlgeschlagen');
        } finally {
            setLoadingAudit(false);
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
        >
            <Card>
                <CardHeader>
                    <CardTitle className="flex items-center gap-2">
                        <Download size={20} /> Daten-Export
                    </CardTitle>
                    <CardDescription>
                        Exportieren Sie Notfallpläne und Audit-Logs als CSV-Datei für die Buchhaltung.
                    </CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="grid gap-4 md:grid-cols-2">
                        <Card className="border-2 border-dashed hover:border-primary transition-colors">
                            <CardContent className="pt-6 text-center">
                                <FileSpreadsheet className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                                <h3 className="font-semibold mb-2">Notfallpläne</h3>
                                <p className="text-sm text-muted-foreground mb-4">
                                    Alle Dienstpläne mit Benutzerinformationen, Zeiten und Status.
                                </p>

                                <div className="grid grid-cols-2 gap-2 mb-4">
                                    <select
                                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                                        value={selectedMonth}
                                        onChange={(e) => setSelectedMonth(Number(e.target.value))}
                                    >
                                        <option value={0}>Alle Monate</option>
                                        {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                                            <option key={m} value={m}>{new Date(0, m - 1).toLocaleString('de-DE', { month: 'long' })}</option>
                                        ))}
                                    </select>
                                    <select
                                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                                        value={selectedYear}
                                        onChange={(e) => setSelectedYear(Number(e.target.value))}
                                    >
                                        {Array.from({ length: 5 }, (_, i) => new Date().getFullYear() - 2 + i).map((y) => (
                                            <option key={y} value={y}>{y}</option>
                                        ))}
                                    </select>
                                </div>

                                <Button onClick={handleExportPlans} disabled={loadingPlans} className="w-full mb-2">
                                    {loadingPlans ? 'Exportiere CSV...' : 'Als CSV herunterladen'}
                                </Button>
                                <Button onClick={handleExportPlansPdf} disabled={loadingPlans} variant="outline" className="w-full">
                                    {loadingPlans ? 'Exportiere PDF...' : 'Als PDF herunterladen'}
                                </Button>
                            </CardContent>
                        </Card>

                        <Card className="border-2 border-dashed hover:border-primary transition-colors">
                            <CardContent className="pt-6 text-center">
                                <FileClock className="mx-auto h-12 w-12 text-muted-foreground mb-4" />
                                <h3 className="font-semibold mb-2">Audit-Log</h3>
                                <p className="text-sm text-muted-foreground mb-4">
                                    Alle Systemaktivitäten mit Zeitstempel, Benutzer und Aktion.
                                </p>
                                <div className="h-[52px] mb-4"></div> {/* Spacer to align buttons */}
                                <Button onClick={handleExportAudit} disabled={loadingAudit} className="w-full">
                                    {loadingAudit ? 'Exportiere...' : 'Als CSV herunterladen'}
                                </Button>
                            </CardContent>
                        </Card>
                    </div>
                </CardContent>
            </Card>
        </motion.div>
    );
}
