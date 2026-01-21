"use client";
import { useEffect, useState } from 'react';
import Navbar from '@/components/Navbar';
import { getPersons, createPerson, deletePerson, Person } from '@/services/personService';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Trash2, Plus, UserPlus } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

import { useRouter } from 'next/navigation';

export default function AdminPage() {
    const router = useRouter();
    const [persons, setPersons] = useState<Person[]>([]);
    const [formData, setFormData] = useState({ first_name: '', last_name: '', external_number: '' });
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (!token) {
            router.push('/login');
            return;
        }
        loadPersons();
    }, []);

    const loadPersons = async () => {
        const data = await getPersons();
        setPersons(data);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        await createPerson(formData);
        setFormData({ first_name: '', last_name: '', external_number: '' });
        await loadPersons();
        setLoading(false);
    };

    const handleDelete = async (id: number) => {
        if (confirm("Delete this person?")) {
            await deletePerson(id);
            loadPersons();
        }
    };

    return (
        <main className="min-h-screen bg-background">
            <Navbar />
            <div className="container mx-auto mt-8 p-4">
                <div className="grid gap-6 md:grid-cols-3">
                    {/* Add Person Form */}
                    <motion.div
                        initial={{ opacity: 0, x: -20 }}
                        animate={{ opacity: 1, x: 0 }}
                        className="md:col-span-1"
                    >
                        <Card>
                            <CardHeader>
                                <CardTitle className="flex items-center gap-2"><UserPlus size={20} /> Add Person</CardTitle>
                                <CardDescription>Register a new emergency contact.</CardDescription>
                            </CardHeader>
                            <CardContent>
                                <form onSubmit={handleSubmit} className="space-y-4">
                                    <Input
                                        placeholder="First Name"
                                        value={formData.first_name}
                                        onChange={e => setFormData({ ...formData, first_name: e.target.value })}
                                        required
                                    />
                                    <Input
                                        placeholder="Last Name"
                                        value={formData.last_name}
                                        onChange={e => setFormData({ ...formData, last_name: e.target.value })}
                                        required
                                    />
                                    <Input
                                        placeholder="Phone (+49...)"
                                        value={formData.external_number}
                                        onChange={e => setFormData({ ...formData, external_number: e.target.value })}
                                        required
                                    />
                                    <Button type="submit" className="w-full" disabled={loading}>
                                        {loading ? "Adding..." : <><Plus size={16} className="mr-2" /> Add Person</>}
                                    </Button>
                                </form>
                            </CardContent>
                        </Card>
                    </motion.div>

                    {/* Person List */}
                    <motion.div
                        initial={{ opacity: 0, x: 20 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.2 }}
                        className="md:col-span-2"
                    >
                        <Card>
                            <CardHeader>
                                <CardTitle>Personnel List</CardTitle>
                                <CardDescription>Manage available emergency contacts.</CardDescription>
                            </CardHeader>
                            <CardContent>
                                <div className="rounded-md border">
                                    <table className="w-full text-sm text-left">
                                        <thead className="bg-muted/50 text-muted-foreground">
                                            <tr>
                                                <th className="px-4 py-3 font-medium">Name</th>
                                                <th className="px-4 py-3 font-medium">Number</th>
                                                <th className="px-4 py-3 font-medium text-right">Actions</th>
                                            </tr>
                                        </thead>
                                        <tbody className="divide-y">
                                            <AnimatePresence>
                                                {persons.map(person => (
                                                    <motion.tr
                                                        key={person.id}
                                                        initial={{ opacity: 0 }}
                                                        animate={{ opacity: 1 }}
                                                        exit={{ opacity: 0, height: 0 }}
                                                        className="hover:bg-muted/50 transition-colors"
                                                    >
                                                        <td className="px-4 py-3 font-medium">{person.first_name} {person.last_name}</td>
                                                        <td className="px-4 py-3 text-muted-foreground">{person.external_number}</td>
                                                        <td className="px-4 py-3 text-right">
                                                            <Button variant="ghost" size="icon" onClick={() => handleDelete(person.id)} className="text-destructive hover:text-destructive hover:bg-destructive/10">
                                                                <Trash2 size={16} />
                                                            </Button>
                                                        </td>
                                                    </motion.tr>
                                                ))}
                                                {persons.length === 0 && (
                                                    <tr>
                                                        <td colSpan={3} className="px-4 py-8 text-center text-muted-foreground">No persons found.</td>
                                                    </tr>
                                                )}
                                            </AnimatePresence>
                                        </tbody>
                                    </table>
                                </div>
                            </CardContent>
                        </Card>
                    </motion.div>
                </div>
            </div>
        </main>
    );
}
