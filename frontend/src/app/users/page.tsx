"use client";
import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import Navbar from '@/components/Navbar';
import { getUsers, createUser, updateUser, deleteUser, User, UserCreate, UserUpdate } from '@/services/userService';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Trash2, Plus, UserPlus, Edit, X, Check } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export default function UsersPage() {
    const router = useRouter();
    const [users, setUsers] = useState<User[]>([]);
    const [loading, setLoading] = useState(false);
    const [showModal, setShowModal] = useState(false);
    const [editingUser, setEditingUser] = useState<User | null>(null);
    const [formData, setFormData] = useState<UserCreate>({
        username: '',
        email: '',
        password: '',
        first_name: '',
        last_name: '',
        phone_number: '',
        role: 'planner',
        is_active: true,
        can_take_duty: true
    });

    useEffect(() => {
        const token = localStorage.getItem('token');
        const role = localStorage.getItem('role');
        if (!token) {
            router.push('/login');
            return;
        }
        if (role !== 'admin') {
            router.push('/calendar');
            return;
        }
        loadUsers();
    }, [router]);

    const loadUsers = async () => {
        try {
            const data = await getUsers();
            setUsers(data);
        } catch (error) {
            console.error('Failed to load users:', error);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            if (editingUser) {
                const updateData: UserUpdate = {
                    email: formData.email,
                    first_name: formData.first_name,
                    last_name: formData.last_name,
                    phone_number: formData.phone_number || undefined,
                    role: formData.role,
                    is_active: formData.is_active,
                    can_take_duty: formData.can_take_duty,
                };
                if (formData.password) {
                    updateData.password = formData.password;
                }
                await updateUser(editingUser.id, updateData);
            } else {
                await createUser(formData);
            }
            setShowModal(false);
            setEditingUser(null);
            resetForm();
            await loadUsers();
        } catch (error: any) {
            console.error('Failed to save user:', error);
            alert(error.response?.data?.detail || 'Failed to save user');
        } finally {
            setLoading(false);
        }
    };

    const handleEdit = (user: User) => {
        setEditingUser(user);
        setFormData({
            username: user.username,
            email: user.email,
            password: '',
            first_name: user.first_name,
            last_name: user.last_name,
            phone_number: user.phone_number || '',
            role: user.role,
            is_active: user.is_active,
            can_take_duty: user.can_take_duty
        });
        setShowModal(true);
    };

    const handleDelete = async (id: number) => {
        if (confirm("Diesen Benutzer wirklich löschen?")) {
            try {
                await deleteUser(id);
                loadUsers();
            } catch (error: any) {
                alert(error.response?.data?.detail || 'Failed to delete user');
            }
        }
    };

    const resetForm = () => {
        setFormData({
            username: '',
            email: '',
            password: '',
            first_name: '',
            last_name: '',
            phone_number: '',
            role: 'planner',
            is_active: true,
            can_take_duty: true
        });
    };

    const getRoleBadgeClass = (role: string) => {
        switch (role) {
            case 'admin': return 'bg-red-100 text-red-800 dark:bg-red-900/20 dark:text-red-400';
            case 'planner': return 'bg-blue-100 text-blue-800 dark:bg-blue-900/20 dark:text-blue-400';
            case 'buchhaltung': return 'bg-green-100 text-green-800 dark:bg-green-900/20 dark:text-green-400';
            default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900/20 dark:text-gray-400';
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
                        <CardHeader className="flex flex-row items-center justify-between">
                            <div>
                                <CardTitle className="flex items-center gap-2">
                                    <UserPlus size={20} /> Benutzerverwaltung
                                </CardTitle>
                                <CardDescription>Benutzer anlegen, bearbeiten und löschen.</CardDescription>
                            </div>
                            <Button onClick={() => { resetForm(); setEditingUser(null); setShowModal(true); }}>
                                <Plus size={16} className="mr-2" /> Neuer Benutzer
                            </Button>
                        </CardHeader>
                        <CardContent>
                            <div className="rounded-md border">
                                <table className="w-full text-sm text-left">
                                    <thead className="bg-muted/50 text-muted-foreground">
                                        <tr>
                                            <th className="px-4 py-3 font-medium">Name</th>
                                            <th className="px-4 py-3 font-medium">E-Mail</th>
                                            <th className="px-4 py-3 font-medium">Telefon</th>
                                            <th className="px-4 py-3 font-medium">Rolle</th>
                                            <th className="px-4 py-3 font-medium">Status</th>
                                            <th className="px-4 py-3 font-medium text-right">Aktionen</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y">
                                        <AnimatePresence>
                                            {users.map(user => (
                                                <motion.tr
                                                    key={user.id}
                                                    initial={{ opacity: 0 }}
                                                    animate={{ opacity: 1 }}
                                                    exit={{ opacity: 0, height: 0 }}
                                                    className="hover:bg-muted/50 transition-colors"
                                                >
                                                    <td className="px-4 py-3 font-medium">
                                                        {user.first_name} {user.last_name}
                                                        <div className="text-xs text-muted-foreground">@{user.username}</div>
                                                    </td>
                                                    <td className="px-4 py-3 text-muted-foreground">{user.email}</td>
                                                    <td className="px-4 py-3 text-muted-foreground">{user.phone_number || '-'}</td>
                                                    <td className="px-4 py-3">
                                                        <span className={`px-2 py-1 rounded-full text-xs font-medium ${getRoleBadgeClass(user.role)}`}>
                                                            {user.role}
                                                        </span>
                                                    </td>
                                                    <td className="px-4 py-3">
                                                        {user.is_active ? (
                                                            <span className="text-green-600 flex items-center gap-1"><Check size={14} /> Aktiv</span>
                                                        ) : (
                                                            <span className="text-red-600 flex items-center gap-1"><X size={14} /> Inaktiv</span>
                                                        )}
                                                    </td>
                                                    <td className="px-4 py-3 text-right space-x-2">
                                                        <Button variant="ghost" size="icon" onClick={() => handleEdit(user)}>
                                                            <Edit size={16} />
                                                        </Button>
                                                        <Button variant="ghost" size="icon" onClick={() => handleDelete(user.id)} className="text-destructive hover:text-destructive hover:bg-destructive/10">
                                                            <Trash2 size={16} />
                                                        </Button>
                                                    </td>
                                                </motion.tr>
                                            ))}
                                            {users.length === 0 && (
                                                <tr>
                                                    <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">Keine Benutzer gefunden.</td>
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

            {/* Modal */}
            <AnimatePresence>
                {showModal && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
                        onClick={() => setShowModal(false)}
                    >
                        <motion.div
                            initial={{ scale: 0.95, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.95, opacity: 0 }}
                            className="bg-background rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto"
                            onClick={e => e.stopPropagation()}
                        >
                            <div className="p-6">
                                <h2 className="text-xl font-bold mb-4">
                                    {editingUser ? 'Benutzer bearbeiten' : 'Neuer Benutzer'}
                                </h2>
                                <form onSubmit={handleSubmit} className="space-y-4">
                                    <div className="grid grid-cols-2 gap-4">
                                        <Input
                                            placeholder="Vorname"
                                            value={formData.first_name}
                                            onChange={e => setFormData({ ...formData, first_name: e.target.value })}
                                            required
                                        />
                                        <Input
                                            placeholder="Nachname"
                                            value={formData.last_name}
                                            onChange={e => setFormData({ ...formData, last_name: e.target.value })}
                                            required
                                        />
                                    </div>
                                    <Input
                                        placeholder="Benutzername"
                                        value={formData.username}
                                        onChange={e => setFormData({ ...formData, username: e.target.value })}
                                        required
                                        disabled={!!editingUser}
                                    />
                                    <Input
                                        type="email"
                                        placeholder="E-Mail"
                                        value={formData.email}
                                        onChange={e => setFormData({ ...formData, email: e.target.value })}
                                        required
                                    />
                                    <Input
                                        type="password"
                                        placeholder={editingUser ? "Neues Passwort (leer = unverändert)" : "Passwort"}
                                        value={formData.password}
                                        onChange={e => setFormData({ ...formData, password: e.target.value })}
                                        required={!editingUser}
                                    />
                                    <Input
                                        placeholder="Telefonnummer"
                                        value={formData.phone_number}
                                        onChange={e => setFormData({ ...formData, phone_number: e.target.value })}
                                    />
                                    <div>
                                        <label className="text-sm font-medium mb-2 block">Rolle</label>
                                        <select
                                            className="w-full px-3 py-2 border rounded-md bg-background"
                                            value={formData.role}
                                            onChange={e => setFormData({ ...formData, role: e.target.value })}
                                        >
                                            <option value="admin">Admin</option>
                                            <option value="planner">Planer</option>
                                            <option value="buchhaltung">Buchhaltung</option>
                                        </select>
                                    </div>
                                    <div className="flex items-center gap-4">
                                        <label className="flex items-center gap-2">
                                            <input
                                                type="checkbox"
                                                checked={formData.is_active}
                                                onChange={e => setFormData({ ...formData, is_active: e.target.checked })}
                                            />
                                            Aktiv
                                        </label>
                                        <label className="flex items-center gap-2">
                                            <input
                                                type="checkbox"
                                                checked={formData.can_take_duty}
                                                onChange={e => setFormData({ ...formData, can_take_duty: e.target.checked })}
                                            />
                                            Kann Dienst übernehmen
                                        </label>
                                    </div>
                                    <div className="flex gap-2 pt-4">
                                        <Button type="submit" className="flex-1" disabled={loading}>
                                            {loading ? "Speichern..." : "Speichern"}
                                        </Button>
                                        <Button type="button" variant="outline" onClick={() => setShowModal(false)}>
                                            Abbrechen
                                        </Button>
                                    </div>
                                </form>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </main>
    );
}
