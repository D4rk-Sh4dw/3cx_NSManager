"use client";

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import CalendarComponent from '@/components/CalendarComponent';
import Navbar from '@/components/Navbar';
import { motion } from "framer-motion";

export default function CalendarPage() {
    const router = useRouter();

    useEffect(() => {
        const token = localStorage.getItem('token');
        if (!token) {
            router.push('/login');
        }
    }, [router]);

    return (
        <main className="min-h-screen bg-background">
            <Navbar />
            <div className="container mx-auto mt-8 p-4">
                <motion.div
                    initial={{ opacity: 0, scale: 0.98 }}
                    animate={{ opacity: 1, scale: 1 }}
                    transition={{ duration: 0.4 }}
                >
                    <CalendarComponent />
                </motion.div>
            </div>
        </main>
    );
}
