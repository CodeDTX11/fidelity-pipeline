# Frontend

React + TypeScript + Vite client for the Fidelity pipeline consumer API.

## Local development

1. Start the Spring Boot consumer so the API is available on `http://localhost:8080`.
2. Install dependencies:

```bash
npm install
```

3. Start the frontend dev server:

```bash
npm run dev
```

4. Open the Vite URL shown in the terminal.

Requests to `/api/*` are proxied to `http://localhost:8080`.
