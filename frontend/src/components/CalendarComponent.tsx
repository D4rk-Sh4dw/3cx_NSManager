"use client";

import React, { useState, useEffect } from 'react';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import { getPlans, createPlan, confirmPlan } from '@/services/planService';
import { getPersons, Person } from '@/services/personService';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { motion, AnimatePresence } from "framer-motion";
import { Check, Calendar as CalendarIcon, User, X } from 'lucide-react';
import { useTheme } from "next-themes";

export default function CalendarComponent() {
    const [events, setEvents] = useState([]);
    const [persons, setPersons] = useState<Person[]>([]);
    const [modalOpen, setModalOpen] = useState(false);
    const [selectedRange, setSelectedRange] = useState<{ start: Date, end: Date } | null>(null);
    const [selectedPersonId, setSelectedPersonId] = useState<string>("");
    const { theme } = useTheme();

    useEffect(() => {
        fetchEvents();
        fetchPersons();
    }, []);

    const fetchEvents = async () => {
        try {
            const plans = await getPlans();
            const mappedEvents = plans.map(p => ({
                id: p.id.toString(),
                title: p.person ? `${p.person.first_name} ${p.person.last_name}` : 'Unknown',
                start: p.start_date,
                end: p.end_date,
                backgroundColor: p.confirmed ? (theme === 'dark' ? '#166534' : '#16a34a') : (theme === 'dark' ? '#b45309' : '#f59e0b'),
                borderColor: 'transparent',
                textColor: '#ffffff'
            }));
            setEvents(mappedEvents as any);
        } catch (e) {
            console.error("Failed to fetch plans", e);
        }
    };

    // Re-fetch events when theme changes to update keys/colors if needed, 
    // but FullCalendar handles primitive string changes usually. 
    useEffect(() => {
        fetchEvents();
    }, [theme]);

    const fetchPersons = async () => {
        const data = await getPersons();
        setPersons(data);
    };

    const handleDateSelect = (selectInfo: any) => {
        setSelectedRange({ start: selectInfo.start, end: selectInfo.end });
        setModalOpen(true);
    };

    const handleSave = async () => {
        if (selectedRange && selectedPersonId) {
            try {
                await createPlan({
                    start_date: selectedRange.start.toISOString(),
                    end_date: selectedRange.end.toISOString(),
                    person_id: parseInt(selectedPersonId)
                });
                setModalOpen(false);
                fetchEvents();
            } catch (error) {
                alert("Failed to create entry. Possible overlap.");
            }
        }
    };

    const handleEventClick = async (clickInfo: any) => {
        if (confirm(`Do you want to confirm this event? ID: ${clickInfo.event.id}`)) {
            try {
                await confirmPlan(parseInt(clickInfo.event.id));
                fetchEvents();
            } catch (e) {
                alert("Failed to confirm.");
            }
        }
    };

    return (
        <Card className="shadow-lg">
            <CardHeader>
                <CardTitle className="flex items-center gap-2"><CalendarIcon /> On-Call Schedule</CardTitle>
                <CardDescription>Manage daily and weekly emergency duties.</CardDescription>
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
                    editable={true}
                    selectable={true}
                    selectMirror={true}
                    dayMaxEvents={true}
                    events={events}
                    select={handleDateSelect}
                    eventClick={handleEventClick}
                    height="75vh"
                    eventClassNames="cursor-pointer hover:opacity-80 transition-opacity"
                />

                <AnimatePresence>
                    {modalOpen && (
                        <div className="fixed inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-50">
                            <motion.div
                                initial={{ scale: 0.9, opacity: 0 }}
                                animate={{ scale: 1, opacity: 1 }}
                                exit={{ scale: 0.9, opacity: 0 }}
                                className="bg-card text-card-foreground p-6 rounded-lg shadow-xl border w-96 max-w-[90vw]"
                            >
                                <div className="flex justify-between items-center mb-4">
                                    <h2 className="text-xl font-bold flex items-center gap-2"><User size={20} /> Assign Duty</h2>
                                    <Button variant="ghost" size="icon" onClick={() => setModalOpen(false)}><X size={16} /></Button>
                                </div>

                                <div className="space-y-4">
                                    <div className="text-sm text-muted-foreground">
                                        {selectedRange && (
                                            <p>From: {selectedRange.start.toLocaleDateString()} <br /> To: {selectedRange.end.toLocaleDateString()}</p>
                                        )}
                                    </div>

                                    <select
                                        className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
                                        value={selectedPersonId}
                                        onChange={(e) => setSelectedPersonId(e.target.value)}
                                    >
                                        <option value="">Select Person...</option>
                                        {persons.map(p => (
                                            <option key={p.id} value={p.id}>{p.first_name} {p.last_name}</option>
                                        ))}
                                    </select>
                                </div>

                                <div className="flex justify-end gap-2 mt-6">
                                    <Button variant="outline" onClick={() => setModalOpen(false)}>Cancel</Button>
                                    <Button onClick={handleSave} disabled={!selectedPersonId}><Check size={16} className="mr-2" /> Save</Button>
                                </div>
                            </motion.div>
                        </div>
                    )}
                </AnimatePresence>
            </CardContent>
        </Card>
    );
}
