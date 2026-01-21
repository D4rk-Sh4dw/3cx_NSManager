"use client";
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { changePassword } from '@/services/authService';

export default function Navbar() {
    const router = useRouter();
    const [modalOpen, setModalOpen] = useState(false);
    const [passData, setPassData] = useState({ old: "", new: "" });

    const handleLogout = () => {
        // Ensure we are in browser
        if (typeof window !== 'undefined') {
            localStorage.removeItem('token');
            router.push('/login');
        }
    };

    const handlePasswordChange = async () => {
        try {
            await changePassword(passData.old, passData.new);
            alert("Password changed!");
            setModalOpen(false);
            setPassData({ old: "", new: "" });
        } catch (e) {
            alert("Failed to change password. Old password wrong?");
        }
    };

    return (
        <nav className="bg-gray-800 text-white p-4">
            <div className="container mx-auto flex justify-between items-center">
                <div className="font-bold text-lg">Emergency Manager</div>
                <div className="flex gap-4 items-center">
                    <Link href="/calendar" className="hover:text-gray-300">Calendar</Link>
                    <Link href="/admin" className="hover:text-gray-300">Admin</Link>
                    <Link href="/audit" className="hover:text-gray-300">Audit</Link>
                    <button onClick={() => setModalOpen(true)} className="hover:text-gray-300 ml-4">Profile</button>
                    <button onClick={handleLogout} className="bg-red-600 px-3 py-1 rounded hover:bg-red-700 ml-4 lg:ml-8">Logout</button>
                </div>
            </div>

            {modalOpen && (
                <div className="fixed inset-0 bg-gray-600 bg-opacity-50 flex items-center justify-center z-50">
                    <div className="bg-white text-black p-5 rounded-lg shadow-xl w-96">
                        <h2 className="text-xl mb-4 font-bold">Change Password</h2>
                        <input
                            type="password"
                            placeholder="Old Password"
                            className="w-full p-2 border rounded mb-2"
                            value={passData.old}
                            onChange={(e) => setPassData({ ...passData, old: e.target.value })}
                        />
                        <input
                            type="password"
                            placeholder="New Password"
                            className="w-full p-2 border rounded mb-4"
                            value={passData.new}
                            onChange={(e) => setPassData({ ...passData, new: e.target.value })}
                        />
                        <div className="flex justify-end gap-2">
                            <button onClick={() => setModalOpen(false)} className="px-4 py-2 bg-gray-300 rounded">Cancel</button>
                            <button onClick={handlePasswordChange} className="px-4 py-2 bg-blue-600 text-white rounded">Update</button>
                        </div>
                    </div>
                </div>
            )}
        </nav>
    );
}
