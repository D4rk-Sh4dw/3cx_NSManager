"use client";

import { useState, useEffect } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import Link from 'next/link';
import { changePassword } from '@/services/authService';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useTheme } from "next-themes";
import { LogOut, User, Moon, Sun, Lock, Menu, X, Calendar, FileText, Download, UserCog, Users } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { cn } from "@/lib/utils";

export function AppHeader() {
    const router = useRouter();
    const pathname = usePathname();
    const { setTheme, theme } = useTheme();
    const [modalOpen, setModalOpen] = useState(false);
    const [passData, setPassData] = useState({ old: "", new: "" });
    const [userMenuOpen, setUserMenuOpen] = useState(false);
    const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
    const [userRole, setUserRole] = useState<string | null>(null);

    useEffect(() => {
        if (typeof window !== 'undefined') {
            setUserRole(localStorage.getItem('role'));
        }
    }, []);

    const handleLogout = () => {
        if (typeof window !== 'undefined') {
            localStorage.removeItem('token');
            localStorage.removeItem('role');
            router.push('/login');
        }
    };

    const handlePasswordChange = async () => {
        try {
            await changePassword(passData.old, passData.new);
            alert("Passwort geändert!");
            setModalOpen(false);
            setPassData({ old: "", new: "" });
        } catch (e) {
            alert("Passwortänderung fehlgeschlagen.");
        }
    };

    // Mobile Nav Links (duplicate of Sidebar for mobile)
    const navLinks = [
        { href: "/calendar", label: "Kalender", icon: Calendar, roles: ["admin", "planner", "buchhaltung"] },
        { href: "/audit", label: "Audit-Log", icon: FileText, roles: ["admin", "planner", "buchhaltung"] },
        { href: "/users", label: "Benutzerverwaltung", icon: UserCog, roles: ["admin"] },
        { href: "/export", label: "Daten-Export", icon: Download, roles: ["admin", "buchhaltung"] },
    ];
    const filteredLinks = navLinks.filter(link => !userRole || link.roles.includes(userRole));

    return (
        <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b bg-background px-6 shadow-sm">
            <div className="flex-1 flex items-center gap-4">
                <Button variant="ghost" size="icon" className="md:hidden" onClick={() => setMobileMenuOpen(!mobileMenuOpen)}>
                    <Menu />
                </Button>
                <h1 className="text-lg font-semibold text-foreground hidden md:block">3CX Call Routing Manager</h1>
                <h1 className="text-lg font-semibold text-foreground md:hidden">Manager</h1>
            </div>

            <div className="flex items-center gap-2 relative">
                <Button variant="ghost" size="icon" onClick={() => setTheme(theme === "dark" ? "light" : "dark")}>
                    <Sun className="h-[1.2rem] w-[1.2rem] rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
                    <Moon className="absolute h-[1.2rem] w-[1.2rem] rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
                    <span className="sr-only">Toggle theme</span>
                </Button>

                <div className="relative">
                    <Button
                        variant="outline"
                        size="icon"
                        className="rounded-full"
                        onClick={() => setUserMenuOpen(!userMenuOpen)}
                    >
                        <User className="h-5 w-5" />
                    </Button>

                    <AnimatePresence>
                        {userMenuOpen && (
                            <motion.div
                                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                                animate={{ opacity: 1, y: 0, scale: 1 }}
                                exit={{ opacity: 0, y: 10, scale: 0.95 }}
                                className="absolute right-0 mt-2 w-48 bg-popover rounded-md shadow-lg border border-border py-1 z-50 text-popover-foreground"
                            >
                                <div className="px-2 py-1.5 text-sm font-semibold border-b">Mein Account</div>
                                <button
                                    onClick={() => { setModalOpen(true); setUserMenuOpen(false); }}
                                    className="w-full text-left px-2 py-1.5 text-sm hover:bg-accent hover:text-accent-foreground flex items-center gap-2"
                                >
                                    <Lock className="w-4 h-4" /> Passwort ändern
                                </button>
                                <button
                                    onClick={handleLogout}
                                    className="w-full text-left px-2 py-1.5 text-sm hover:bg-destructive/10 text-destructive hover:text-destructive flex items-center gap-2"
                                >
                                    <LogOut className="w-4 h-4" /> Logout
                                </button>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </div>

            {/* Mobile Menu Overlay */}
            <AnimatePresence>
                {mobileMenuOpen && (
                    <motion.div
                        initial={{ opacity: 0, x: -300 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: -300 }}
                        transition={{ type: "spring", bounce: 0, duration: 0.3 }}
                        className="fixed inset-y-0 left-0 w-64 bg-background border-r shadow-2xl z-50 p-4 md:hidden"
                    >
                        <div className="flex items-center justify-between mb-8">
                            <div className="flex items-center gap-2 font-bold text-xl text-primary">
                                <div className="bg-primary text-primary-foreground p-1 rounded">
                                    <Users size={20} />
                                </div>
                                Manager
                            </div>
                            <Button variant="ghost" size="icon" onClick={() => setMobileMenuOpen(false)}>
                                <X />
                            </Button>
                        </div>
                        <div className="space-y-1">
                            {filteredLinks.map((link) => {
                                const Icon = link.icon;
                                const isActive = pathname === link.href;
                                return (
                                    <Link
                                        key={link.href}
                                        href={link.href}
                                        onClick={() => setMobileMenuOpen(false)}
                                        className={cn(
                                            "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-all hover:text-primary",
                                            isActive ? "bg-secondary text-primary" : "text-muted-foreground"
                                        )}
                                    >
                                        <Icon className="h-4 w-4" />
                                        {link.label}
                                    </Link>
                                )
                            })}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>

            {modalOpen && (
                <div className="fixed inset-0 bg-background/80 backdrop-blur-sm flex items-center justify-center z-50">
                    <motion.div
                        initial={{ scale: 0.9, opacity: 0 }}
                        animate={{ scale: 1, opacity: 1 }}
                        className="bg-card text-card-foreground p-6 rounded-lg shadow-lg border w-96 relative"
                    >
                        <h2 className="text-xl mb-4 font-bold flex items-center gap-2"><Lock /> Passwort ändern</h2>
                        <div className="space-y-4">
                            <Input
                                type="password"
                                placeholder="Altes Passwort"
                                value={passData.old}
                                onChange={(e) => setPassData({ ...passData, old: e.target.value })}
                            />
                            <Input
                                type="password"
                                placeholder="Neues Passwort"
                                value={passData.new}
                                onChange={(e) => setPassData({ ...passData, new: e.target.value })}
                            />
                        </div>
                        <div className="flex justify-end gap-2 mt-6">
                            <Button variant="secondary" onClick={() => setModalOpen(false)}>Abbrechen</Button>
                            <Button onClick={handlePasswordChange}>Aktualisieren</Button>
                        </div>
                    </motion.div>
                </div>
            )}
        </header>
    );
}
