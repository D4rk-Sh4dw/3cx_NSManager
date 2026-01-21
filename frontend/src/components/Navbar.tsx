"use client";
import Link from 'next/link';
import { useRouter, usePathname } from 'next/navigation';
import { useState, useEffect } from 'react';
import { changePassword } from '@/services/authService';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useTheme } from "next-themes";
import { Calendar, Users, FileText, LogOut, User, Moon, Sun, Menu, X } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

export default function Navbar() {
    const router = useRouter();
    const pathname = usePathname();
    const [modalOpen, setModalOpen] = useState(false);
    const [passData, setPassData] = useState({ old: "", new: "" });
    const { setTheme, theme } = useTheme();
    const [mounted, setMounted] = useState(false);
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

    // Prevent hydration mismatch
    useEffect(() => {
        setMounted(true);
    }, []);

    const handleLogout = () => {
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
            alert("Failed to change password.");
        }
    };

    const navLinks = [
        { href: "/calendar", label: "Calendar", icon: Calendar },
        { href: "/admin", label: "Admin", icon: Users },
        { href: "/audit", label: "Audit", icon: FileText },
    ];

    if (!mounted) return <nav className="bg-background border-b p-4"><div className="h-8"></div></nav>;

    return (
        <nav className="bg-background border-b">
            <div className="container mx-auto px-4 py-3 flex justify-between items-center">
                <div className="flex items-center gap-2 font-bold text-xl text-primary">
                    <div className="bg-primary text-primary-foreground p-1 rounded">
                        <Users size={20} />
                    </div>
                    Emergency Manager
                </div>

                {/* Desktop Menu */}
                <div className="hidden md:flex items-center gap-6">
                    {navLinks.map(link => {
                        const Icon = link.icon;
                        const isActive = pathname === link.href;
                        return (
                            <Link key={link.href} href={link.href} className={`flex items-center gap-2 text-sm font-medium transition-colors hover:text-primary ${isActive ? "text-primary" : "text-muted-foreground"}`}>
                                <Icon size={16} />
                                {link.label}
                            </Link>
                        )
                    })}
                </div>

                <div className="hidden md:flex items-center gap-4">
                    <Button variant="ghost" size="icon" onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
                        <Sun className="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
                        <Moon className="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
                        <span className="sr-only">Toggle theme</span>
                    </Button>

                    <Button variant="outline" size="sm" onClick={() => setModalOpen(true)}>
                        <User size={16} className="mr-2" /> Profile
                    </Button>
                    <Button variant="destructive" size="sm" onClick={handleLogout}>
                        <LogOut size={16} className="mr-2" /> Logout
                    </Button>
                </div>

                {/* Mobile Toggle */}
                <div className="md:hidden flex items-center gap-4">
                    <Button variant="ghost" size="icon" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
                        {mobileMenuOpen ? <X /> : <Menu />}
                    </Button>
                </div>
            </div>

            {/* Mobile Menu */}
            <AnimatePresence>
                {mobileMenuOpen && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="md:hidden border-t bg-background overflow-hidden"
                    >
                        <div className="p-4 flex flex-col gap-4">
                            {navLinks.map(link => (
                                <Link key={link.href} href={link.href} onClick={() => setMobileMenuOpen(false)} className="flex items-center gap-2 text-sm font-medium py-2">
                                    <link.icon size={16} /> {link.label}
                                </Link>
                            ))}
                            <div className="flex flex-col gap-2 mt-2 pt-2 border-t">
                                <Button variant="outline" size="sm" onClick={() => { setTheme(theme === "dark" ? "light" : "dark"); }}>
                                    Toggle Theme
                                </Button>
                                <Button variant="outline" size="sm" onClick={() => setModalOpen(true)}>
                                    Profile
                                </Button>
                                <Button variant="destructive" size="sm" onClick={handleLogout}>
                                    Logout
                                </Button>
                            </div>
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {modalOpen && (
                <div className="fixed inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-50">
                    <motion.div
                        initial={{ scale: 0.9, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        className="bg-card text-card-foreground p-6 rounded-lg shadow-lg border w-96"
                    >
                        <h2 className="text-xl mb-4 font-bold flex items-center gap-2"><User /> Change Password</h2>
                        <div className="space-y-4">
                            <Input
                                type="password"
                                placeholder="Old Password"
                                value={passData.old}
                                onChange={(e) => setPassData({ ...passData, old: e.target.value })}
                            />
                            <Input
                                type="password"
                                placeholder="New Password"
                                value={passData.new}
                                onChange={(e) => setPassData({ ...passData, new: e.target.value })}
                            />
                        </div>
                        <div className="flex justify-end gap-2 mt-6">
                            <Button variant="secondary" onClick={() => setModalOpen(false)}>Cancel</Button>
                            <Button onClick={handlePasswordChange}>Update</Button>
                        </div>
                    </motion.div>
                </div>
            )}
        </nav>
    );
}
