// src/hooks/useAuth.ts

'use client';

import { useContext } from 'react';
import { AuthContext } from '@/context/AuthContext'; // Nota: exportaremos AuthContext también desde el archivo.

// Para mantener la consistencia, en el archivo AuthContext.tsx añade:
// export const AuthContext = createContext<AuthContextType | undefined>(undefined);
// (Actualmente está como const AuthContext = ...)
// Así que en este archivo haremos: