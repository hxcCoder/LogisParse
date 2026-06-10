# LogisParse Frontend

Next.js + Tailwind interface for the LogisParse API.

## Run

```bash
cd frontend
npm.cmd install
npm.cmd run dev
```

Create `.env.local` from `.env.example`:

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## API Contract

The helper in `src/lib/api.ts` maps the current FastAPI endpoints:

| Action | Endpoint |
| --- | --- |
| Login | `POST /api/v1/auth/login` |
| Upload document | `POST /api/v1/documents/upload` |
| List documents | `GET /api/v1/documents` |

The first screen is intentionally an operator console, not a marketing landing.
Replace the demo state in `src/app/page.tsx` with calls to `login`,
`uploadDocument` and `listDocuments` when wiring the live flow.
