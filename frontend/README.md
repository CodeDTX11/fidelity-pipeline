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

## Docker Compose

The Compose setup builds the frontend into static assets and serves them with Nginx.

1. From the repo root, start the required services:

```bash
docker compose up --build frontend consumer postgres redpanda producer
```

2. Open the frontend at:

```text
http://localhost:5173
```

In Compose mode, the frontend container proxies `/api/*` requests to the `consumer` service, so the browser still talks to a single origin.
