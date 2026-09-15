"use client";

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { login, getAuthConfig, startSsoLogin, completeSsoLogin, type AuthConfig } from '@/services/authService';
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { motion } from "framer-motion";
import { KeyRound, User, ShieldCheck } from 'lucide-react';

const SSO_ERRORS: Record<string, string> = {
    provider_unreachable: "Der SSO-Anbieter ist nicht erreichbar. Bitte später erneut versuchen.",
    provider_rejected: "Die Anmeldung wurde vom SSO-Anbieter abgelehnt.",
    invalid_response: "Ungültige Antwort vom SSO-Anbieter.",
    state_expired: "Die Anmeldung hat zu lange gedauert. Bitte erneut versuchen.",
    state_invalid: "Die Anmeldung konnte nicht zugeordnet werden. Bitte erneut versuchen.",
    state_mismatch: "Die Anmeldung konnte nicht zugeordnet werden. Bitte erneut versuchen.",
    no_id_token: "Der SSO-Anbieter hat kein ID-Token geliefert.",
    account_disabled: "Dieses Konto ist deaktiviert. Bitte an einen Administrator wenden.",
    oidc_error: "SSO-Anmeldung fehlgeschlagen. Details stehen im Backend-Log.",
    internal_error: "Unerwarteter Fehler bei der SSO-Anmeldung.",
};

export default function LoginPage() {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const router = useRouter();
    const [loading, setLoading] = useState(false);
    const [config, setConfig] = useState<AuthConfig | null>(null);
    // Blocks the form while the token from an SSO redirect is being picked up
    const [ssoPending, setSsoPending] = useState(false);

    useEffect(() => {
        getAuthConfig()
            .then(setConfig)
            // Without the config we still show the password form rather than nothing
            .catch(() => setConfig({ local_login_enabled: true, oidc_enabled: false, oidc_provider_name: 'SSO' }));
    }, []);

    // Handle the return leg of the SSO redirect
    useEffect(() => {
        const params = new URLSearchParams(window.location.search);
        const ssoError = params.get('sso_error');
        const ssoOk = params.get('sso') === 'ok';

        if (!ssoError && !ssoOk) return;
        window.history.replaceState({}, '', '/login');

        if (ssoError) {
            setError(SSO_ERRORS[ssoError] ?? `SSO-Anmeldung fehlgeschlagen (${ssoError}).`);
            return;
        }

        setSsoPending(true);
        completeSsoLogin()
            .then((data) => {
                localStorage.setItem('token', data.access_token);
                localStorage.setItem('role', data.role);
                router.push('/calendar');
            })
            .catch((err) => {
                setError(err.response?.data?.detail ?? "Die SSO-Anmeldung konnte nicht abgeschlossen werden.");
                setSsoPending(false);
            });
    }, [router]);

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            const data = await login(username, password);
            localStorage.setItem('token', data.access_token);
            localStorage.setItem('role', data.role);  // Store role for navbar
            router.push('/calendar');
        } catch (err: any) {
            console.error(err);
            if (err.response) {
                setError(err.response.data?.detail ?? `Server Error: ${err.response.status}`);
            } else if (err.request) {
                setError(`Network Error: No response from server. Check console.`);
            } else {
                setError(`Client Error: ${err.message}`);
            }
        } finally {
            setLoading(false);
        }
    };

    const showSso = config?.oidc_enabled ?? false;
    const showLocal = config?.local_login_enabled ?? true;

    return (
        <div className="min-h-screen flex items-center justify-center bg-background p-4">
            <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.5 }}
            >
                <Card className="w-full max-w-md shadow-xl border-t-4 border-t-primary">
                    <CardHeader className="text-center">
                        <CardTitle className="text-2xl font-bold">Willkommen zurück</CardTitle>
                        <p className="text-muted-foreground text-sm">Bitte melden Sie sich an</p>
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

                        {ssoPending && (
                            <p className="text-sm text-muted-foreground text-center py-4">
                                Anmeldung wird abgeschlossen...
                            </p>
                        )}

                        {!ssoPending && showSso && (
                            <Button
                                type="button"
                                variant={showLocal ? "outline" : "default"}
                                className="w-full"
                                onClick={startSsoLogin}
                            >
                                <ShieldCheck className="mr-2 h-4 w-4" />
                                Anmelden mit {config?.oidc_provider_name}
                            </Button>
                        )}

                        {!ssoPending && showSso && showLocal && (
                            <div className="relative my-6">
                                <div className="absolute inset-0 flex items-center">
                                    <span className="w-full border-t" />
                                </div>
                                <div className="relative flex justify-center text-xs uppercase">
                                    <span className="bg-card px-2 text-muted-foreground">oder</span>
                                </div>
                            </div>
                        )}

                        {!ssoPending && showLocal && (
                            <form onSubmit={handleLogin} className="space-y-4">
                                <div className="space-y-2">
                                    <div className="relative">
                                        <User className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                                        <Input
                                            type="text"
                                            placeholder="Benutzername"
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
                                            placeholder="Passwort"
                                            className="pl-9"
                                            value={password}
                                            onChange={(e) => setPassword(e.target.value)}
                                            required
                                        />
                                    </div>
                                </div>
                                <Button type="submit" className="w-full" disabled={loading}>
                                    {loading ? "Anmelden..." : "Anmelden"}
                                </Button>
                            </form>
                        )}
                    </CardContent>
                    <CardFooter className="justify-center text-xs text-muted-foreground">
                        Bereitschaftsdienst Management System
                    </CardFooter>
                </Card>
            </motion.div>
        </div>
    );
}
