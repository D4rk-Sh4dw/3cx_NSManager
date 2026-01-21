"use client";
import { useEffect, useState } from 'react';
import Navbar from '@/components/Navbar';
import { getPersons, createPerson, deletePerson, Person } from '@/services/personService';

export default function AdminPage() {
    const [persons, setPersons] = useState<Person[]>([]);
    const [formData, setFormData] = useState({ first_name: '', last_name: '', external_number: '' });

    useEffect(() => {
        loadPersons();
    }, []);

    const loadPersons = async () => {
        const data = await getPersons();
        setPersons(data);
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        await createPerson(formData);
        setFormData({ first_name: '', last_name: '', external_number: '' });
        loadPersons();
    };

    const handleDelete = async (id: number) => {
        if (confirm("Delete this person?")) {
            await deletePerson(id);
            loadPersons();
        }
    };

    return (
        <main>
            <Navbar />
            <div className="container mx-auto mt-5">
                <h1 className="text-2xl font-bold mb-4">Manage Persons</h1>

                <form onSubmit={handleSubmit} className="mb-8 p-4 border rounded bg-gray-50">
                    <div className="grid grid-cols-3 gap-4">
                        <input
                            placeholder="First Name"
                            className="p-2 border rounded"
                            value={formData.first_name}
                            onChange={e => setFormData({ ...formData, first_name: e.target.value })}
                            required
                        />
                        <input
                            placeholder="Last Name"
                            className="p-2 border rounded"
                            value={formData.last_name}
                            onChange={e => setFormData({ ...formData, last_name: e.target.value })}
                            required
                        />
                        <input
                            placeholder="Phone (+49...)"
                            className="p-2 border rounded"
                            value={formData.external_number}
                            onChange={e => setFormData({ ...formData, external_number: e.target.value })}
                            required
                        />
                    </div>
                    <button type="submit" className="mt-4 px-4 py-2 bg-green-600 text-white rounded">Add Person</button>
                </form>

                <div className="bg-white shadow overflow-hidden sm:rounded-md">
                    <ul className="divide-y divide-gray-200">
                        {persons.map(person => (
                            <li key={person.id} className="px-4 py-4 flex justify-between items-center bg-white">
                                <div>
                                    <p className="font-medium text-gray-900">{person.first_name} {person.last_name}</p>
                                    <p className="text-sm text-gray-500">{person.external_number}</p>
                                </div>
                                <button onClick={() => handleDelete(person.id)} className="text-red-600 hover:text-red-900">Delete</button>
                            </li>
                        ))}
                    </ul>
                </div>
            </div>
        </main>
    );
}
