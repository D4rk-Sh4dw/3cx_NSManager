"use client";

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useEffect, useState } from 'react';
import { Calendar, Users, FileText, Download, UserCog, Menu, BarChart } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

interface SidebarProps {
    className?: string;
}

export function AppSidebar({ className }: SidebarProps) {
    const pathname = usePathname();
    const [userRole, setUserRole] = useState<string | null>(null);
    const [mounted, setMounted] = useState(false);

    useEffect(() => {
        setMounted(true);
        if (typeof window !== 'undefined') {
            setUserRole(localStorage.getItem('role'));
        }
    }, []);

    // Base links for all authenticated users
    const navLinks = [
        { href: "/calendar", label: "Kalender", icon: Calendar, roles: ["admin", "planner", "buchhaltung"] },
        { href: "/audit", label: "Audit-Log", icon: FileText, roles: ["admin", "planner", "buchhaltung"] },
        { href: "/users", label: "Benutzerverwaltung", icon: UserCog, roles: ["admin"] },
        { href: "/export", label: "Daten-Export", icon: Download, roles: ["admin", "buchhaltung"] },
        { href: "/stats", label: "Statistik", icon: BarChart, roles: ["admin", "buchhaltung"] },
    ];

    const filteredLinks = navLinks.filter(link =>
        !userRole || link.roles.includes(userRole)
    );

    if (!mounted) return null;

    return (
        <div className={cn("pb-12 min-h-screen w-64 border-r bg-card hidden md:block", className)}>
            <div className="space-y-4 py-4">
                <div className="px-3 py-2">
                    <div className="flex items-center gap-2 mb-6 px-4">
                        <div className="bg-primary text-primary-foreground p-1 rounded">
                            <Users size={20} />
                        </div>
                        <h2 className="text-lg font-bold tracking-tight">{process.env.NEXT_PUBLIC_SIDEBAR_TITLE || "Management"}</h2>
                    </div>
                    <div className="space-y-1">
                        {filteredLinks.map((link) => {
                            const Icon = link.icon;
                            const isActive = pathname === link.href;
                            return (
                                <Link
                                    key={link.href}
                                    href={link.href}
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
                </div>
                {/* Optional: Add a section for help or bottom links */}
            </div>

        </div>
    );
}
