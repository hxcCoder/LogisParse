  "use client"; // Muy importante en Next.js para poder usar estados y eventos

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function LoginPage() {
    const router = useRouter();
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [error, setError] = useState("");

const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
    setError("");
  
    try {
        // 1. Llamamos a tu Backend FastAPI (el código que me mostraste)
    const res = await fetch("http://localhost:8000/api/v1/auth/login", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
        },
        body: JSON.stringify({ email, password }),
        });

        if (!res.ok) {
            throw new Error("Credenciales inválidas");
        }

        // 2. Extraemos el TokenResponse
        const data = await res.json();
        
        // 3. Guardamos el token para usarlo después (ej: al subir PDFs)
        localStorage.setItem("token", data.access_token);

        // 4. Redirigimos al usuario al dashboard
        router.push("/dashboard");
        
    } catch (err: any) {
        setError(err.message);
    }
    };

    return (
        <div className="flex h-screen items-center justify-center bg-gray-100">
        <div className="w-full max-w-md rounded-lg bg-white p-8 shadow-md">
            <h2 className="mb-6 text-center text-2xl font-bold">Iniciar Sesión</h2>
        
        {error && <p className="mb-4 text-sm text-red-500">{error}</p>}
        
        <form onSubmit={handleLogin}>
            <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700">Email</label>
            <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1 w-full rounded border border-gray-300 p-2"
                required
            />
            </div>
            
            <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700">Contraseña</label>
                <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-1 w-full rounded border border-gray-300 p-2"
                required
            />
            </div>
            
            <button
                type="submit"
                className="w-full rounded bg-blue-600 py-2 text-white hover:bg-blue-700"
            >
            Entrar
            </button>
        </form>
        </div>
    </div>
    );
}