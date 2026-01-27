"use client";

import React, { useState, useEffect } from 'react';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import { getPlans, createPlan, confirmPlan, deletePlan } from '@/services/planService';
import { getDutyEligibleUsers, User } from '@/services/userService';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { motion, AnimatePresence } from "framer-motion";
import { Check, Calendar as CalendarIcon, User as UserIcon, X, Trash2 } from 'lucide-react';
import { useTheme } from "next-themes";
import { jwtDecode } from "jwt-decode";
import { stringToColor } from "@/lib/utils";

export default function CalendarComponent() {
    const [events, setEvents] = useState([]);
    const [users, setUsers] = useState<User[]>([]);
    const [modalOpen, setModalOpen] = useState(false);
    const [detailModalOpen, setDetailModalOpen] = useState(false);
    const [selectedRange, setSelectedRange] = useState<{ start: Date, end: Date } | null>(null);
    const [selectedUserId, setSelectedUserId] = useState<string>("");
    const [selectedEvent, setSelectedEvent] = useState<any>(null);
    const { theme } = useTheme();
    const [currentUserRole, setCurrentUserRole] = useState<string | null>(null);
    const [currentUsername, setCurrentUsername] = useState<string | null>(null);

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (token) {
            try {
                const decoded: any = jwtDecode(token);
                setCurrentUserRole(decoded.role);
                setCurrentUsername(decoded.sub);
            } catch (e) {
                console.error("Invalid token");
            }
        }
        fetchEvents();
        fetchUsers();
    }, [theme]);

    const fetchEvents = async () => {
        try {
            const plans = await getPlans();
            const mappedEvents = plans.map(p => {
                const userColor = p.user?.username ? stringToColor(p.user.username) : '#808080';

                return {
                    id: p.id.toString(),
                    title: p.user ? `${p.user.first_name} ${p.user.last_name}` : 'Unknown',
                    start: p.start_date,
                    end: p.end_date,
                    backgroundColor: userColor,
                    borderColor: 'transparent',
                    textColor: '#ffffff',
                    allDay: true, // Force "full day" block appearance
                    classNames: p.confirmed ? [] : ['opacity-60', 'border-2', 'border-dashed'], // Visual cue for unconfirmed
                    extendedProps: {
                        user_id: p.user_id,
                        username: p.user?.username,
                        confirmed: p.confirmed,
                        created_by: p.created_by
                    }
                };
            });
            setEvents(mappedEvents as any);
        } catch (e) {
            console.error("Failed to fetch plans", e);
        }
    };

    const fetchUsers = async () => {
        try {
            const data = await getDutyEligibleUsers();
            setUsers(data);
        } catch (e) { console.error("Failed to fetch users", e); }
    };

    const handleDateSelect = (selectInfo: any) => {
        // Buchhaltung cannot create plans
        if (currentUserRole === 'buchhaltung') return;

        let start = selectInfo.start;
        let end = selectInfo.end;

        // "Planner" role restriction: Always full weeks (Mon - Sun)
        if (currentUserRole === 'planner') {
            const day = start.getDay(); // 0 (Sun) to 6 (Sat)
            // Calculate Monday of the selected week
            // If Sunday (0), subtract 6 days. Else subtract day - 1.
            const diff = start.getDate() - (day === 0 ? 6 : day - 1);

            const monday = new Date(start);
            monday.setDate(diff);
            monday.setHours(0, 0, 0, 0);

            const nextMonday = new Date(monday);
            nextMonday.setDate(monday.getDate() + 7);

            start = monday;
            end = nextMonday;
        }

        setSelectedRange({ start: start, end: end });

        // If planner, auto-select self if available in list (though backend enforces it anyway)
        if (currentUserRole === 'planner' && currentUsername) {
            const me = users.find(u => u.username === currentUsername);
            if (me) setSelectedUserId(me.id.toString());
        } else {
            setSelectedUserId("");
        }
        setModalOpen(true);
    };

    const handleSave = async () => {
        if (selectedRange && selectedUserId) {
            try {
                // Helper to preserve local time value when converting to ISO (basically converting 00:00 Local -> 00:00 UTC)
                const toLocalISOString = (date: Date) => {
                    const tzOffset = date.getTimezoneOffset() * 60000;
                    return new Date(date.getTime() - tzOffset).toISOString();
                };

                await createPlan({
                    start_date: toLocalISOString(selectedRange.start),
                    end_date: toLocalISOString(selectedRange.end),
                    user_id: parseInt(selectedUserId)
                });
                setModalOpen(false);
                fetchEvents();
            } catch (error: any) {
                alert(error.response?.data?.detail || "Eintrag konnte nicht erstellt werden.");
            }
        }
    };

    const handleEventClick = (clickInfo: any) => {
        // Buchhaltung read-only
        if (currentUserRole === 'buchhaltung') return;

        setSelectedEvent({
            id: clickInfo.event.id,
            title: clickInfo.event.title,
            start: clickInfo.event.start,
            end: clickInfo.event.end,
            ...clickInfo.event.extendedProps
        });
        setDetailModalOpen(true);
    };

    const handleConfirm = async () => {
        if (!selectedEvent) return;
        try {
            await confirmPlan(parseInt(selectedEvent.id));
            setDetailModalOpen(false);
            fetchEvents();
        } catch (error: any) {
            alert(error.response?.data?.detail || "Bestätigung fehlgeschlagen.");
        }
    };

    const handleDelete = async () => {
        if (!selectedEvent) return;
        if (!confirm("Wirklich löschen?")) return;
        try {
            await deletePlan(parseInt(selectedEvent.id));
            setDetailModalOpen(false);
            fetchEvents();
        } catch (error: any) {
            alert(error.response?.data?.detail || "Löschen fehlgeschlagen.");
        }
    };

    return (
        <Card className="shadow-lg">
            <CardHeader>
                <CardTitle className="flex items-center gap-2"><CalendarIcon /> Dienstplan</CardTitle>
                <CardDescription>Planung der Notfalldienste (Tag/Woche).</CardDescription>
            </CardHeader>
            <CardContent className="p-0 sm:p-6 text-sm">
                <FullCalendar
                    plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
                    headerToolbar={{
                        left: 'prev,next today',
                        center: 'title',
                        right: 'dayGridMonth,timeGridWeek'
                    }}
                    initialView='dayGridMonth'
                    editable={currentUserRole === 'admin'} // Drag & Drop only for admin for now
                    selectable={currentUserRole !== 'buchhaltung'}
                    selectMirror={true}
                    dayMaxEvents={true}
                    events={events}
                    select={handleDateSelect}
                    eventClick={handleEventClick}
                    height="75vh"
                    eventClassNames="cursor-pointer hover:opacity-80 transition-opacity"
                    locale="de"
                    firstDay={1}
                />

                {/* Create Modal */}
                <AnimatePresence>
                    {modalOpen && (
                        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                            <motion.div
                                initial={{ scale: 0.9, opacity: 0 }}
                                animate={{ scale: 1, opacity: 1 }}
                                exit={{ scale: 0.9, opacity: 0 }}
                                className="bg-card text-card-foreground p-6 rounded-lg shadow-xl border w-full max-w-md"
                            >
                                <div className="flex justify-between items-center mb-4">
                                    <h2 className="text-xl font-bold flex items-center gap-2"><UserIcon size={20} /> Dienst eintragen</h2>
                                    <Button variant="ghost" size="icon" onClick={() => setModalOpen(false)}><X size={16} /></Button>
                                </div>

                                <div className="space-y-4">
                                    <div className="text-sm text-muted-foreground bg-muted p-2 rounded">
                                        {selectedRange && (
                                            <>
                                                Von: {selectedRange.start.toLocaleString()} <br />
                                                Bis: {selectedRange.end.toLocaleString()}
                                            </>
                                        )}
                                    </div>

                                    {currentUserRole === 'admin' ? (
                                        <div>
                                            <label className="text-sm font-medium mb-1 block">Benutzer auswählen</label>
                                            <select
                                                className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm"
                                                value={selectedUserId}
                                                onChange={(e) => setSelectedUserId(e.target.value)}
                                            >
                                                <option value="">Bitte wählen...</option>
                                                {users.map(u => (
                                                    <option key={u.id} value={u.id}>{u.first_name} {u.last_name}{u.role ? ` (${u.role})` : ''}</option>
                                                ))}
                                            </select>
                                        </div>
                                    ) : (
                                        <div className="p-3 border rounded bg-muted/50">
                                            <span className="text-sm font-medium">Als Diensthabender eintragen:</span>
                                            {selectedUserId ? (
                                                <div className="text-lg font-bold mt-1">
                                                    {users.find(u => u.id.toString() === selectedUserId)?.first_name} {users.find(u => u.id.toString() === selectedUserId)?.last_name}
                                                </div>
                                            ) : (
                                                <div className="text-red-500 font-bold mt-1">
                                                    Nicht berechtigt (User '{currentUsername}' nicht in 'Eligible Users' gefunden).
                                                </div>
                                            )}
                                        </div>
                                    )}
                                </div>

                                <div className="flex justify-end gap-2 mt-6">
                                    <Button variant="outline" onClick={() => setModalOpen(false)}>Abbrechen</Button>
                                    <Button onClick={handleSave} disabled={!selectedUserId}><Check size={16} className="mr-2" /> Speichern</Button>
                                </div>
                            </motion.div>
                        </div>
                    )}
                </AnimatePresence>

                {/* Detail/Action Modal */}
                <AnimatePresence>
                    {detailModalOpen && selectedEvent && (
                        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                            <motion.div
                                initial={{ scale: 0.9, opacity: 0 }}
                                animate={{ scale: 1, opacity: 1 }}
                                exit={{ scale: 0.9, opacity: 0 }}
                                className="bg-card text-card-foreground p-6 rounded-lg shadow-xl border w-full max-w-md"
                            >
                                <div className="flex justify-between items-center mb-4">
                                    <h2 className="text-xl font-bold">Dienst Details</h2>
                                    <Button variant="ghost" size="icon" onClick={() => setDetailModalOpen(false)}><X size={16} /></Button>
                                </div>

                                <div className="space-y-4 mb-6">
                                    <div className="flex justify-between border-b pb-2">
                                        <span className="text-muted-foreground">Person:</span>
                                        <span className="font-medium">{selectedEvent.title}</span>
                                    </div>
                                    <div className="flex justify-between border-b pb-2">
                                        <span className="text-muted-foreground">Start:</span>
                                        <span>{selectedEvent.start?.toLocaleString()}</span>
                                    </div>
                                    <div className="flex justify-between border-b pb-2">
                                        <span className="text-muted-foreground">Ende:</span>
                                        <span>{selectedEvent.end?.toLocaleString()}</span>
                                    </div>
                                    <div className="flex justify-between border-b pb-2">
                                        <span className="text-muted-foreground">Status:</span>
                                        <span className={selectedEvent.confirmed ? "text-green-500 font-bold" : "text-yellow-500 font-bold"}>
                                            {selectedEvent.confirmed ? "Bestätigt" : "Entwurf"}
                                        </span>
                                    </div>
                                </div>

                                <div className="flex justify-between gap-2">
                                    {/* Delete Button: Show if Admin OR (Planner AND NOT Confirmed) */}
                                    {(currentUserRole === 'admin' || (currentUserRole === 'planner' && !selectedEvent.confirmed)) && (
                                        <Button variant="destructive" onClick={handleDelete}>
                                            <Trash2 size={16} className="mr-2" /> Löschen
                                        </Button>
                                    )}

                                    {/* Only Admin can confirm */}
                                    {!selectedEvent.confirmed && currentUserRole === 'admin' && (
                                        <Button onClick={handleConfirm} className="bg-green-600 hover:bg-green-700 text-white">
                                            <Check size={16} className="mr-2" /> Bestätigen
                                        </Button>
                                    )}
                                </div>
                            </motion.div>
                        </div>
                    )}
                </AnimatePresence>

            </CardContent>
        </Card>
    );
}
