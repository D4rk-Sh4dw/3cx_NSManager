"use client";

import React, { useState, useEffect } from 'react';
import FullCalendar from '@fullcalendar/react';
import dayGridPlugin from '@fullcalendar/daygrid';
import timeGridPlugin from '@fullcalendar/timegrid';
import interactionPlugin from '@fullcalendar/interaction';
import { getPlans, createPlan, confirmPlan } from '@/services/planService';
import { getPersons, Person } from '@/services/personService';

export default function CalendarComponent() {
    const [events, setEvents] = useState([]);
    const [persons, setPersons] = useState<Person[]>([]);
    const [modalOpen, setModalOpen] = useState(false);
    const [selectedRange, setSelectedRange] = useState<{ start: Date, end: Date } | null>(null);
    const [selectedPersonId, setSelectedPersonId] = useState<string>("");

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
                backgroundColor: p.confirmed ? 'green' : 'orange',
            }));
            setEvents(mappedEvents as any);
        } catch (e) {
            console.error("Failed to fetch plans", e);
        }
    };

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
        <div className='p-4'>
            <FullCalendar
                plugins={[dayGridPlugin, timeGridPlugin, interactionPlugin]}
                headerToolbar={{
                    left: 'prev,next today',
                    center: 'title',
                    right: 'dayGridMonth,timeGridWeek,timeGridDay'
                }}
                initialView='dayGridMonth'
                editable={true}
                selectable={true}
                selectMirror={true}
                dayMaxEvents={true}
                events={events}
                select={handleDateSelect}
                eventClick={handleEventClick}
                height="80vh"
            />

            {modalOpen && (
                <div className="fixed inset-0 bg-gray-600 bg-opacity-50 overflow-y-auto h-full w-full flex items-center justify-center z-50">
                    <div className="bg-white p-5 rounded-lg shadow-xl w-96">
                        <h2 className="text-xl mb-4">Assign Person</h2>
                        <select
                            className="w-full p-2 border rounded mb-4"
                            value={selectedPersonId}
                            onChange={(e) => setSelectedPersonId(e.target.value)}
                        >
                            <option value="">Select Person...</option>
                            {persons.map(p => (
                                <option key={p.id} value={p.id}>{p.first_name} {p.last_name}</option>
                            ))}
                        </select>
                        <div className="flex justify-end gap-2">
                            <button onClick={() => setModalOpen(false)} className="px-4 py-2 bg-gray-300 rounded">Cancel</button>
                            <button onClick={handleSave} className="px-4 py-2 bg-blue-500 text-white rounded">Save</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
