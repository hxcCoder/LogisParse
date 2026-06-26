// src/context/AuthContext.tsx

'use client';

import React, {
    createContext,
    useEffect,
    useState,
    useCallback,
    useMemo,
} from 'react';
import { useRouter } from 'next/navigation';
import { authApi } from '@/lib/api';
import { User, LoginCredentials, RegisterPayload } from '@/types';
import toast from 'react-hot-toast';

interface AuthContextType {
    user: User | null;
    token: string | null;
    isLoading: boolean;
    login: (credentials: LoginCredentials) => Promise<void>;
    register: (payload: RegisterPayload) => Promise<void>;
    logout: () => void;
}

// ✅ EXPORTADO para que useAuth pueda importarlo
export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
    const router = useRouter();
    const [user, setUser] = useState<User | null>(null);
    const [token, setToken] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState<boolean>(true);

  // --- Hidratación desde localStorage ---
useEffect(() => {
    const storedToken = localStorage.getItem('auth_token');
    const storedUser = localStorage.getItem('auth_user');

    if (storedToken && storedUser) {
        try {
        setToken(storedToken);
        setUser(JSON.parse(storedUser));
    } catch {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('auth_user');
    }
    }
    setIsLoading(false);
}, []);

  // --- Logout (centralizado) ---
const logout = useCallback(() => {
    localStorage.removeItem('auth_token');
    localStorage.removeItem('auth_user');
    setToken(null);
    setUser(null);
    router.push('/login');
    toast.success('Sesión cerrada');
}, [router]);

  // --- Escuchar evento de 401 (desde el interceptor de Axios) ---
useEffect(() => {
    const handleUnauthorized = () => {
        toast.error('Tu sesión ha expirado. Inicia sesión nuevamente.');
        logout();
    };

    window.addEventListener('unauthorized', handleUnauthorized);
    return () => window.removeEventListener('unauthorized', handleUnauthorized);
}, [logout]);

  // --- Login ---
const login = useCallback(
async (credentials: LoginCredentials) => {
    setIsLoading(true);
    try {
        const response = await authApi.login(credentials);
        const { access_token } = response.data;

        // Mock de usuario (sin endpoint /users/me)
        const mockUser: User = {
            id: 'temp-id',
            email: credentials.email,
            full_name: credentials.email.split('@')[0],
            is_active: true,
            created_at: new Date().toISOString(),
        };

        localStorage.setItem('auth_token', access_token);
        localStorage.setItem('auth_user', JSON.stringify(mockUser));

        setToken(access_token);
        setUser(mockUser);

        toast.success('Bienvenido a LogisParse 🚀');
        router.push('/');
    } catch (error: any) {
        const message = error.response?.data?.detail || 'Error al iniciar sesión';
        toast.error(message);
        throw error;
    } finally {
        setIsLoading(false);
    }
    },
    [router]
);

  // --- Register ---
const register = useCallback(
    async (payload: RegisterPayload) => {
        setIsLoading(true);
        try {
            await authApi.register(payload);
            toast.success('Registro exitoso. Ahora inicia sesión.');
            router.push('/login');
    } catch (error: any) {
        const message = error.response?.data?.detail || 'Error al registrarse';
        toast.error(message);
        throw error;
    } finally {
        setIsLoading(false);
    }
    },
    [router]
);

const value = useMemo(
    () => ({ user, token, isLoading, login, register, logout }),
    [user, token, isLoading, login, register, logout]
);

return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

// ✅ Hook para consumir el contexto (más limpio)
export const useAuth = (): AuthContextType => {
    const context = React.useContext(AuthContext);
    if (context === undefined) {
        throw new Error('useAuth must be used within an AuthProvider');
}
return context;
};