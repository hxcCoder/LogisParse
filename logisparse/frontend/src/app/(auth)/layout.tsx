// src/app/(auth)/layout.tsx

export default function AuthLayout({
    children,
}: {
    children: React.ReactNode;
}) {
return (
    <div className="min-h-screen flex items-center justify-center bg-[#0F172A] p-4">
        <div className="w-full max-w-md">
        {children}
        </div>
    </div>
);
}