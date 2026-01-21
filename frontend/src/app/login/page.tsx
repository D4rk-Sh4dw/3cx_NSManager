"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { login } from '@/services/authService';
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";
import { KeyRound, User } from 'lucide-react';

export default function LoginPage() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const router = useRouter();
    const [loading, setLoading] = useState(false);

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            const data = await login(username, password);
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('role', data.role);  // Store role for navbar
            router.push('/calendar');
        } catch (err: any) {
            console.error(err);
            if (err.response) {
                // Server responded with non-2xx code
                setError(`Server Error: ${err.response.status} - ${JSON.stringify(err.response.data)}`);
            } else if (err.request) {
                // Request made but no response (Network Error)
                setError(`Network Error: No response from server. Check console.`);
            } else {
                setError(`Client Error: ${err.message}`);
            }
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-background p-4">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
            >
                <Card className="w-full max-w-md shadow-xl border-t-4 border-t-primary">
                    <CardHeader className="text-center">
                        <CardTitle className="text-2xl font-bold">Welcome Back</CardTitle>
                        <p className="text-muted-foreground text-sm">Please sign in to continue</p>
                    </CardHeader>
                    <CardContent>
                        {error && (
                            <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: "auto" }}
                                className="bg-destructive/15 text-destructive text-sm p-3 rounded-md mb-4"
                            >
                                {error}
                            </motion.div>
                        )}
                        <form onSubmit={handleLogin} className="space-y-4">
                            <div className="space-y-2">
                                <div className="relative">
                                    <User className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                                    <Input
                                        type="text"
                                        placeholder="Username"
                                        className="pl-9"
                                        value={username}
                                        onChange={(e) => setUsername(e.target.value)}
                                        required
                                    />
                                </div>
                            </div>
                            <div className="space-y-2">
                                <div className="relative">
                                    <KeyRound className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                                    <Input
                                        type="password"
                                        placeholder="Password"
                                        className="pl-9"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        required
                                    />
                                </div>
                            </div>
                            <Button type="submit" className="w-full" disabled={loading}>
                                {loading ? "Signing In..." : "Sign In"}
                            </Button>
                        </form>
                    </CardContent>
                    <CardFooter className="justify-center text-xs text-muted-foreground">
                        Emergency Service Management System
                    </CardFooter>
                </Card>
            </motion.div>
        </div>
    );
}
